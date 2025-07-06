from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from cachetools import TTLCache
import asyncio
import datetime
import logging
import psutil
import time
import zoneinfo

from config.global_settings import get_configs
from config.server import Server
from features.birthdays import check_and_run_birthday_actions
from features.leveling import daily_leveling_maintenance
from features.moderation import daily_moderation_maintenance
from core.db_manager import daily_database_maintenance
from core.log_manager import setup_logging




# Cache configuration for 10000 guilds
tz_cache = TTLCache(maxsize=10000, ttl=3600)  # 1-hour cache, handles 10k guilds
MONITORING_INTERVAL = 25  # Guilds processed between monitoring checks

INTERVAL_MINUTES = 15  # Define the interval (keep as first assignment)
INTERVAL_SECONDS = INTERVAL_MINUTES * 60

async def run_scheduled_tasks() -> None:
    """
    |coro|
    Optimized scheduler for thousands of guilds with resource monitoring.
    """
    start_time = datetime.datetime.now(datetime.timezone.utc)
    logging.debug("Starting scheduled tasks run")
    
    current_time_utc = datetime.datetime.now(datetime.timezone.utc)
    if current_time_utc.minute % INTERVAL_MINUTES != 0:
        logging.error("Scheduler interval misalignment detected!")

    log_on_correct_behavior = (current_time_utc.minute // INTERVAL_MINUTES) % 7 == 0
    if (not log_on_correct_behavior):
        logging.info("Logging skipped due to intended behavior.")

    try:
        # Start new log if it is a new day
        if current_time_utc.hour == 0 and current_time_utc.minute == 0:
            logging.warning("New day, generating new log file")
            setup_logging()

        from core.bot import bot
        guilds = list(bot.guilds)
        total_guilds = len(guilds)
        processed = 0
        successes = 0
        errors = 0
        max_cpu = 75  # More conservative threshold for large scale
        throttle_count = 0

        for i, guild in enumerate(guilds):
            try:
                # Throttling check
                if i % MONITORING_INTERVAL == 0:
                    cpu = psutil.cpu_percent()
                    
                    if cpu > max_cpu:
                        throttle_count += 1
                        delay = min(2.0, 0.5 * (cpu / max_cpu))  # Dynamic backoff
                        logging.warning(f"CPU {cpu}% > {max_cpu}%, throttling for {delay}s")
                        await asyncio.sleep(delay)
                        continue

                # Timezone caching
                try:
                    tz = tz_cache.get(guild.id)
                    if not tz:
                        server = Server(guild.id)
                        tz = zoneinfo.ZoneInfo(server.infinibot_settings_profile.timezone or "America/Phoenix") # Using MST as default because most of the world is asleep at 3:00 MST, so it works out well to just use that as the default
                        tz_cache[guild.id] = tz
                except Exception as e:
                    logging.error(f"Timezone lookup failed for {guild.id}: {e}")
                    continue

                # Time calculation
                current_time_local = current_time_utc.astimezone(tz)

                # Birthday checks
                await check_and_run_birthday_actions(bot, guild)
                
                # Daily maintenance
                if current_time_local.hour == 3: # 3am local time is a good time to run daily maintenance since it's a low traffic hour
                    await daily_leveling_maintenance(bot, guild)
                    await daily_moderation_maintenance(bot, guild)
                
                successes += 1
                processed += 1

            except Exception as e:
                errors += 1
                logging.error(f"Guild {guild.id} processing failed: {e}", exc_info=True)

            # Progress monitoring
            if log_on_correct_behavior and processed % 100 == 0 and processed > 0:
                elapsed = (datetime.datetime.now(datetime.timezone.utc) - start_time).total_seconds()
                rate = processed / elapsed if elapsed > 0 else 0
                logging.info(
                    f"Progress: {processed}/{total_guilds} "
                    f"({(processed/total_guilds)*100:.1f}%) | "
                    f"Rate: {rate:.1f} guilds/sec | "
                    f"CPU: {psutil.cpu_percent()}% | "
                    f"Mem: {psutil.virtual_memory().percent}%"
                )

        if (current_time_utc.hour == 9 and current_time_utc.minute == 0): # 9am utc time = LOW TRAFFIC HOUR GLOBALLY
            await daily_database_maintenance(bot)

        # Final monitoring report
        if log_on_correct_behavior:
            duration = datetime.datetime.now(datetime.timezone.utc) - start_time
            logging.info(
                f"Completed processing {total_guilds} guilds\n"
                f"Successes: {successes} | Errors: {errors} | Throttle events: {throttle_count}\n"
                f"Cache stats: Size {len(tz_cache)}/{tz_cache.maxsize} | "
                f"System load: CPU {psutil.cpu_percent()}% | Mem {psutil.virtual_memory().percent}%\n"
                f"Total duration: {duration} | Avg rate: {total_guilds/duration.total_seconds():.1f} guilds/sec"
            )

            logging.info("------------------------------------------------------------------------------------")

    except Exception as e:
        logging.error(f"Fatal scheduler error: {e}", exc_info=True)

    finally:
        if (datetime.datetime.now(datetime.timezone.utc) - start_time) > datetime.timedelta(minutes=5):
            logging.warning("Scheduler run exceeded 5 minutes warning threshold")

# Create a scheduler instance
scheduler = AsyncIOScheduler()

# Suppress logs from APScheduler
logging.getLogger('apscheduler').setLevel(logging.WARNING)

def start_scheduler() -> None:
    """
    Starts the scheduler. Scheduler will run the job function every 5 minutes,
    aligned to the nearest 5-minute interval (00:00, 00:05, 00:10, etc.).
    """
    global scheduler

    # Stop the scheduler if it's already running
    if scheduler.running:
        scheduler.shutdown()

    # Calculate next run time aligned to the nearest 5-minute interval
    now = time.time()
    seconds_since_last = now % INTERVAL_SECONDS
    seconds_to_next = INTERVAL_SECONDS - seconds_since_last
    next_run_time = datetime.datetime.fromtimestamp(now + seconds_to_next, tz=datetime.timezone.utc)

    # Add the job with aligned start time
    scheduler.add_job(
        run_scheduled_tasks,  # Make sure this matches your actual job function
        trigger=IntervalTrigger(minutes=INTERVAL_MINUTES),
        next_run_time=next_run_time,
        misfire_grace_time=get_configs()["scheduler.misfire-grace-time-seconds"]
    )

    # Configure scheduler to use UTC and start
    scheduler.configure(timezone="UTC")  # Critical for alignment
    scheduler.start()

    logging.info(f"Scheduler started. Next run at {next_run_time} UTC")

def stop_scheduler() -> None:
    """
    Stops the scheduler.

    If the scheduler is not running, this function does nothing.

    :return: None
    :rtype: None
    """
    global scheduler
    if scheduler.running:
        scheduler.shutdown(wait=True)  # Wait for running jobs to finish
    logging.info("Scheduler stopped.")

def get_scheduler() -> AsyncIOScheduler:
    """
    Get the scheduler instance.

    :return: The scheduler instance
    :rtype: apscheduler.schedulers.asyncio.AsyncIOScheduler
    """
    global scheduler
    return scheduler