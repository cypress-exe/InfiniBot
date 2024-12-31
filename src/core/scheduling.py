from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
import datetime
import logging
import time

from config.global_settings import get_configs
from features.leveling import midnight_action_leveling


async def run_every_minute():
    # Get the current time
    current_time_utc = datetime.datetime.now(datetime.timezone.utc)
    
    utc_offset = get_configs()["server_utc_offset"]
    current_time_local = current_time_utc + datetime.timedelta(hours=utc_offset)
    
    # Check if the time is 00:01
    if current_time_local.hour == 00 and current_time_local.minute == 1:
        # Run midnight code
        from core.bot import bot
        await midnight_action_leveling(bot)

# Create a scheduler instance
scheduler = AsyncIOScheduler()

# Suppress logs from APScheduler but keep INFO level for the rest of the program
logging.getLogger('apscheduler').setLevel(logging.WARNING)

def start_scheduler():
    global scheduler

    # Calculate the next run time as the next full minute
    next_run_time = datetime.datetime.now() + datetime.timedelta(seconds=(60 - time.time() % 60))

    # Add a job to run the function every 60 seconds
    scheduler.add_job(
        run_every_minute,
        trigger=IntervalTrigger(minutes=1),
        next_run_time=next_run_time,
    )

    # Start the scheduler
    scheduler.start()

def get_scheduler():
    global scheduler
    return scheduler