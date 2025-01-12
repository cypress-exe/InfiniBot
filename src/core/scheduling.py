from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
import datetime
import logging
import time

from config.global_settings import get_configs
from features.birthdays import fifteen_minutely_action
from features.leveling import midnight_action_leveling


async def run_every_minute() -> None:
    """
    |coro|

    Run midnight code. This function is intended to be run every minute.

    :return: None
    :rtype: None
    """
    logging.debug("Running run_every_minute")
    try:
        # Get the current time
        current_time_utc = datetime.datetime.now(datetime.timezone.utc)
        
        utc_offset = get_configs()["server_utc_offset"]
        current_time_local = current_time_utc + datetime.timedelta(hours=utc_offset)
        
        # Check if the time is 00:01
        if current_time_local.hour == 00 and current_time_local.minute == 5:
            
            # Run midnight code
            from core.bot import bot
            await midnight_action_leveling(bot)

        if current_time_local.minute in [0, 15, 30, 45]:
            from core.bot import bot
            await fifteen_minutely_action(bot)
    
    except Exception as e:
        logging.error(f"Error running run_every_minute: {e}", exc_info=True)

    finally:
        finish_time_utc = datetime.datetime.now(datetime.timezone.utc)
        if finish_time_utc - current_time_utc > datetime.timedelta(seconds=10):
            logging.warning(f"Scheduler took too long to run: {finish_time_utc - current_time_utc}")

# Create a scheduler instance
scheduler = AsyncIOScheduler()

# Suppress logs from APScheduler
logging.getLogger('apscheduler').setLevel(logging.WARNING)

def start_scheduler() -> None:
    """
    Starts the scheduler. Scheduler will run the `run_every_minute` function every 60 seconds.

    :return: None
    :rtype: None
    """
    global scheduler

    # Stop the scheduler if it's already running
    if scheduler.running:
        scheduler.shutdown()

    # Calculate the next run time as the next full minute
    next_run_time = datetime.datetime.now() + datetime.timedelta(seconds=(60 - time.time() % 60))

    # Add a job to run the function every 60 seconds
    scheduler.add_job(
        run_every_minute,
        trigger=IntervalTrigger(minutes=1),
        next_run_time=next_run_time,
        misfire_grace_time=get_configs()["scheduler"]["misfire_grace_time_seconds"]  # Allow a grace period for missed runs
    )

    # Start the scheduler
    scheduler.start()

    logging.info("Scheduler started.")

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