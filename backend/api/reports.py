from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from db.database import get_db
from db.models import Report, Project
from api.deps import get_current_user
from db.models import User
from services.pdf_service import generate_pdf_report
import json
import io

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/{project_id}")
def get_report(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == current_user.id
    ).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    report = db.query(Report).filter(
        Report.project_id == project_id
    ).order_by(Report.created_at.desc()).first()

    if not report:
        raise HTTPException(status_code=404, detail="Report not found. Analysis may still be running.")

    return {
        "id": report.id,
        "project_id": report.project_id,
        "overall_score": report.overall_score,
        "report_data": report.report_data,
        "created_at": report.created_at,
    }


@router.get("/{project_id}/pdf")
def download_pdf_report(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == current_user.id
    ).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    report = db.query(Report).filter(
        Report.project_id == project_id
    ).order_by(Report.created_at.desc()).first()

    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    pdf_bytes = generate_pdf_report(report.report_data)

    filename = f"seo-report-{project.business_name.replace(' ', '-').lower()}.pdf"
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/{project_id}/json")
def download_json_report(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == current_user.id
    ).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    report = db.query(Report).filter(
        Report.project_id == project_id
    ).order_by(Report.created_at.desc()).first()

    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    json_str = json.dumps(report.report_data, indent=2, default=str)
    filename = f"seo-report-{project.business_name.replace(' ', '-').lower()}.json"
    return StreamingResponse(
        io.StringIO(json_str),
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
