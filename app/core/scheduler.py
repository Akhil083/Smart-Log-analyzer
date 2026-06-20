from __future__ import annotations

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.core.config import get_settings
from app.db.session import AsyncSessionFactory
from app.services.alert_service import AlertService
from app.services.cleanup_service import CleanupService

settings = get_settings()

scheduler = AsyncIOScheduler()


async def run_alert_check():
    """Periodic alert checking task"""

    try:
        async with AsyncSessionFactory() as session:
            alert_service = AlertService(session)

            await alert_service.check_error_threshold(threshold=50)

            await alert_service.check_anomaly_alerts(interval="minute")

    except Exception as exc:
        print(f"Alert check failed: {exc}")


async def run_cleanup():
    """Periodic cleanup task"""

    try:
        async with AsyncSessionFactory() as session:
            cleanup_service = CleanupService(session)

            await cleanup_service.delete_old_log(
                retention_days=settings.log_retention_days
            )

    except Exception as exc:
        print(f"Cleanup job failed: {exc}")


def start_schedular():
    """Start scheduler background jobs"""

    scheduler.add_job(
        run_alert_check,
        "interval",
        minutes=2,
        id="alert-check-job",
        replace_existing=True,
        max_instances=1,
    )

    scheduler.add_job(
        run_cleanup,
        "cron",
        hour=0,
        minute=0,
        id="cleanup-job",
        replace_existing=True,
        max_instances=1,
    )

    scheduler.start()
