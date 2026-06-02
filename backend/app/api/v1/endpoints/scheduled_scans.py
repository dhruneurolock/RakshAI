"""
Scheduled Scans API Endpoints
CRUD operations for recurring scan schedules.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import uuid
from datetime import datetime

from app.core.database import get_db
from app.models.models import ScheduledScan
from app.models.schemas import ScheduledScanCreate, ScheduledScanUpdate, ScheduledScanResponse
from app.services.scheduler_service import compute_next_run, _trigger_scheduled_scan

router = APIRouter()


@router.post("/", response_model=ScheduledScanResponse, status_code=status.HTTP_201_CREATED)
async def create_scheduled_scan(data: ScheduledScanCreate, db: Session = Depends(get_db)):
    """Create a new scheduled scan."""
    if data.frequency not in ("hourly", "daily", "weekly", "monthly", "custom"):
        raise HTTPException(status_code=400, detail="Invalid frequency")

    next_run = compute_next_run(
        frequency=data.frequency,
        hour=data.hour or 0,
        minute=data.minute or 0,
        day_of_week=data.day_of_week or 0,
        day_of_month=data.day_of_month or 1,
    )

    schedule = ScheduledScan(
        schedule_id=str(uuid.uuid4()),
        name=data.name,
        target_url=data.target_url,
        scan_type=data.scan_type or "full",
        frequency=data.frequency,
        cron_expression=data.cron_expression,
        hour=data.hour,
        minute=data.minute,
        day_of_week=data.day_of_week,
        day_of_month=data.day_of_month,
        is_active=True,
        scan_config=data.scan_config,
        next_run_at=next_run,
        total_runs=0,
        created_by="local-user",
    )
    db.add(schedule)
    db.commit()
    db.refresh(schedule)
    return schedule


@router.get("/", response_model=List[ScheduledScanResponse])
async def list_scheduled_scans(db: Session = Depends(get_db)):
    """List all scheduled scans."""
    return db.query(ScheduledScan).order_by(ScheduledScan.created_at.desc()).all()


@router.get("/{schedule_id}", response_model=ScheduledScanResponse)
async def get_scheduled_scan(schedule_id: str, db: Session = Depends(get_db)):
    """Get a single scheduled scan."""
    schedule = db.query(ScheduledScan).filter(ScheduledScan.schedule_id == schedule_id).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    return schedule


@router.patch("/{schedule_id}", response_model=ScheduledScanResponse)
async def update_scheduled_scan(schedule_id: str, data: ScheduledScanUpdate, db: Session = Depends(get_db)):
    """Update a scheduled scan."""
    schedule = db.query(ScheduledScan).filter(ScheduledScan.schedule_id == schedule_id).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")

    update_data = data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(schedule, field, value)

    # Recompute next_run if schedule config changed
    freq_fields = {"frequency", "hour", "minute", "day_of_week", "day_of_month"}
    if freq_fields & set(update_data.keys()):
        schedule.next_run_at = compute_next_run(
            frequency=schedule.frequency,
            hour=schedule.hour or 0,
            minute=schedule.minute or 0,
            day_of_week=schedule.day_of_week or 0,
            day_of_month=schedule.day_of_month or 1,
        )

    db.commit()
    db.refresh(schedule)
    return schedule


@router.delete("/{schedule_id}")
async def delete_scheduled_scan(schedule_id: str, db: Session = Depends(get_db)):
    """Delete a scheduled scan."""
    schedule = db.query(ScheduledScan).filter(ScheduledScan.schedule_id == schedule_id).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    db.delete(schedule)
    db.commit()
    return {"message": "Schedule deleted", "schedule_id": schedule_id}


@router.post("/{schedule_id}/toggle", response_model=ScheduledScanResponse)
async def toggle_scheduled_scan(schedule_id: str, db: Session = Depends(get_db)):
    """Toggle a scheduled scan active/inactive."""
    schedule = db.query(ScheduledScan).filter(ScheduledScan.schedule_id == schedule_id).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")

    schedule.is_active = not schedule.is_active
    if schedule.is_active:
        schedule.next_run_at = compute_next_run(
            frequency=schedule.frequency,
            hour=schedule.hour or 0,
            minute=schedule.minute or 0,
            day_of_week=schedule.day_of_week or 0,
            day_of_month=schedule.day_of_month or 1,
        )
    db.commit()
    db.refresh(schedule)
    return schedule


@router.post("/{schedule_id}/trigger", response_model=ScheduledScanResponse)
async def trigger_scheduled_scan(schedule_id: str, db: Session = Depends(get_db)):
    """Manually trigger a scheduled scan immediately."""
    schedule = db.query(ScheduledScan).filter(ScheduledScan.schedule_id == schedule_id).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")

    await _trigger_scheduled_scan(schedule, db)
    db.refresh(schedule)
    return schedule
