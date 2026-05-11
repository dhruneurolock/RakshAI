"""
Reports API Endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import FileResponse, RedirectResponse
from sqlalchemy.orm import Session
from typing import List
from pathlib import Path
from urllib.request import urlopen

from app.core.database import get_db
from app.core.config import settings
from app.models.models import Report
from app.models.schemas import ReportResponse

router = APIRouter()


@router.get("/", response_model=List[ReportResponse])
async def list_reports(
    scan_id: int = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List all generated reports"""
    query = db.query(Report)
    
    if scan_id:
        query = query.filter(Report.scan_id == scan_id)
    
    reports = query.order_by(Report.generated_at.desc()).offset(skip).limit(limit).all()
    return reports


@router.get("/{report_id}", response_model=ReportResponse)
async def get_report(report_id: str, db: Session = Depends(get_db)):
    """Get report metadata"""
    report = db.query(Report).filter(Report.report_id == report_id).first()
    
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    return report


@router.get("/{report_id}/download")
async def download_report(report_id: str, db: Session = Depends(get_db)):
    """Download report file"""
    report = db.query(Report).filter(Report.report_id == report_id).first()

    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    normalized_type = (report.report_type or "").lower()
    if normalized_type == "excel":
        normalized_type = "xlsx"
    elif normalized_type == "word":
        normalized_type = "docx"

    media_type_map = {
        "pdf": "application/pdf",
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "json": "application/json",
        "xml": "application/xml",
    }
    media_type = media_type_map.get(normalized_type, "application/octet-stream")
    download_filename = f"{report.report_id}.{normalized_type or 'bin'}"

    # Return inline content (JSON/XML fallback reports)
    if report.content:
        return Response(
            content=report.content,
            media_type=media_type,
            headers={
                "Content-Disposition": f"attachment; filename={download_filename}"
            }
        )

    if report.file_path:
        if report.file_path.startswith("http://") or report.file_path.startswith("https://"):
            try:
                with urlopen(report.file_path, timeout=30) as remote_file:
                    binary_content = remote_file.read()
                return Response(
                    content=binary_content,
                    media_type=media_type,
                    headers={
                        "Content-Disposition": f"attachment; filename={download_filename}"
                    },
                )
            except Exception:
                return RedirectResponse(url=report.file_path, status_code=307)

        file_path = Path(report.file_path)
        if file_path.exists() and file_path.is_file():
            return FileResponse(
                path=str(file_path),
                media_type=media_type,
                filename=download_filename,
            )

    raise HTTPException(status_code=404, detail="Report file not found")


@router.delete("/{report_id}")
async def delete_report(report_id: str, db: Session = Depends(get_db)):
    """Delete a report"""
    report = db.query(Report).filter(Report.report_id == report_id).first()
    
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    # Delete file if exists
    if report.file_path:
        file_path = Path(report.file_path)
        if file_path.exists():
            file_path.unlink()
    
    db.delete(report)
    db.commit()
    
    return {"message": "Report deleted", "report_id": report_id}
