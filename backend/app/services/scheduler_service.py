"""
Scheduled Scan Scheduler Service
Lightweight asyncio background loop that checks for due schedules every 60s
and triggers scans via the existing OrchestratorService pipeline.
"""
import asyncio
import logging
import uuid
from datetime import datetime, timedelta

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.models import ScheduledScan, Scan, ScanStatus
from app.services.orchestrator import OrchestratorService, get_orchestrator

logger = logging.getLogger(__name__)

_scheduler_task = None


def compute_next_run(
    frequency: str,
    hour: int = 0,
    minute: int = 0,
    day_of_week: int = 0,
    day_of_month: int = 1,
    from_time: datetime = None,
) -> datetime:
    """Compute the next run time based on frequency and time parameters."""
    now = from_time or datetime.utcnow()

    if frequency == "hourly":
        # Next full hour + minute offset
        candidate = now.replace(minute=minute % 60, second=0, microsecond=0)
        if candidate <= now:
            candidate += timedelta(hours=1)
        return candidate

    if frequency == "daily":
        candidate = now.replace(hour=hour % 24, minute=minute % 60, second=0, microsecond=0)
        if candidate <= now:
            candidate += timedelta(days=1)
        return candidate

    if frequency == "weekly":
        # day_of_week: 0=Mon..6=Sun
        current_dow = now.weekday()
        days_ahead = (day_of_week % 7) - current_dow
        if days_ahead < 0:
            days_ahead += 7
        candidate = now + timedelta(days=days_ahead)
        candidate = candidate.replace(hour=hour % 24, minute=minute % 60, second=0, microsecond=0)
        if candidate <= now:
            candidate += timedelta(weeks=1)
        return candidate

    if frequency == "monthly":
        dom = max(1, min(day_of_month or 1, 28))
        candidate = now.replace(day=dom, hour=hour % 24, minute=minute % 60, second=0, microsecond=0)
        if candidate <= now:
            month = now.month + 1
            year = now.year
            if month > 12:
                month = 1
                year += 1
            candidate = candidate.replace(year=year, month=month)
        return candidate

    # custom / fallback: 1 hour from now
    return now + timedelta(hours=1)


async def _trigger_scheduled_scan(schedule: ScheduledScan, db: Session) -> None:
    """Trigger a single scheduled scan using OrchestratorService."""
    scan_id = str(uuid.uuid4())
    logger.info(
        "Scheduler triggering scan: schedule=%s target=%s scan_id=%s",
        schedule.schedule_id, schedule.target_url, scan_id,
    )

    try:
        # Create the Scan record
        scan = Scan(
            scan_id=scan_id,
            target_url=schedule.target_url,
            scan_type=schedule.scan_type or "full",
            status=ScanStatus.PENDING,
            progress_percentage=0,
            current_phase="initializing",
            created_at=datetime.utcnow(),
            total_findings=0,
            critical_count=0,
            high_count=0,
            medium_count=0,
            low_count=0,
            info_count=0,
        )
        db.add(scan)
        db.commit()
        db.refresh(scan)

        # Launch via orchestrator
        orchestrator = get_orchestrator()
        result = await orchestrator.start_scan(
            scan_id=scan_id,
            target_url=schedule.target_url,
            scan_type=schedule.scan_type or "full",
            user_id="scheduler",
            policy=schedule.scan_config or {},
        )

        if result.get("success"):
            scan.status = ScanStatus.RUNNING
            scan.current_phase = "phase_1_initialization"
            scan.started_at = datetime.utcnow()
        else:
            scan.status = ScanStatus.FAILED
            scan.error_message = result.get("message", "Scheduler trigger failed")
            scan.completed_at = datetime.utcnow()

        db.commit()

        # Update schedule tracking
        schedule.last_run_at = datetime.utcnow()
        schedule.last_scan_id = scan_id
        schedule.total_runs = (schedule.total_runs or 0) + 1
        schedule.next_run_at = compute_next_run(
            frequency=schedule.frequency,
            hour=schedule.hour or 0,
            minute=schedule.minute or 0,
            day_of_week=schedule.day_of_week or 0,
            day_of_month=schedule.day_of_month or 1,
        )
        db.commit()
        logger.info("Scheduled scan triggered: %s, next_run=%s", scan_id, schedule.next_run_at)

    except Exception as e:
        logger.error("Failed to trigger scheduled scan %s: %s", schedule.schedule_id, e)
        db.rollback()


async def _scheduler_loop() -> None:
    """Main scheduler loop - checks every 60 seconds for due schedules."""
    logger.info("Scan scheduler started")
    while True:
        try:
            db = SessionLocal()
            try:
                now = datetime.utcnow()
                due = (
                    db.query(ScheduledScan)
                    .filter(
                        ScheduledScan.is_active == True,
                        ScheduledScan.next_run_at <= now,
                    )
                    .all()
                )
                for schedule in due:
                    await _trigger_scheduled_scan(schedule, db)
            finally:
                db.close()
        except Exception as e:
            logger.error("Scheduler loop error: %s", e)

        await asyncio.sleep(60)


def start_scheduler() -> None:
    """Start the background scheduler task. Call from FastAPI startup event."""
    global _scheduler_task
    if _scheduler_task is None or _scheduler_task.done():
        _scheduler_task = asyncio.create_task(_scheduler_loop())
        logger.info("Background scan scheduler task created")


def stop_scheduler() -> None:
    """Stop the background scheduler task."""
    global _scheduler_task
    if _scheduler_task and not _scheduler_task.done():
        _scheduler_task.cancel()
        logger.info("Background scan scheduler task cancelled")
