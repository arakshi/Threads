from apscheduler.schedulers.blocking import BlockingScheduler

from app.core.config import get_settings
from app.scheduler.jobs import scheduled_collect


def run_scheduler() -> None:
    settings = get_settings()
    scheduler = BlockingScheduler()
    scheduler.add_job(scheduled_collect, 'interval', minutes=settings.scheduler_interval_minutes, id='collect_job', replace_existing=True)
    scheduler.start()
