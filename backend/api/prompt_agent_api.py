from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from db.database import get_db
from db.models import User, Profile, Competitor, Project, Report, PromptAgentOutput, Notification
from models.schemas import PromptAgentResponse
from api.deps import get_current_user
from agents.prompt_agent import generate_website_prompt, generate_seasonal_content
from services.agent_progress import update_agent_progress

router = APIRouter(prefix="/prompt-agent", tags=["prompt-agent"])


@router.post("/generate", response_model=PromptAgentResponse)
def generate(
    project_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    profile = db.query(Profile).filter(Profile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=400, detail="Please complete your business profile first.")

    competitors = db.query(Competitor).filter(Competitor.profile_id == profile.id).all()

    report_data = {}
    keywords = {}
    if project_id:
        project = db.query(Project).filter(Project.id == project_id, Project.user_id == current_user.id).first()
        if project:
            report = db.query(Report).filter(Report.project_id == project_id).order_by(Report.created_at.desc()).first()
            if report:
                report_data = report.report_data or {}
            from db.models import Keyword
            kw_rows = db.query(Keyword).filter(Keyword.project_id == project_id).all()
            for kw in kw_rows:
                keywords.setdefault(kw.keyword_type, []).append(kw.keyword)
    else:
        # use latest project for this user if none specified
        project = db.query(Project).filter(Project.user_id == current_user.id).order_by(Project.created_at.desc()).first()
        if project:
            project_id = project.id
            report = db.query(Report).filter(Report.project_id == project_id).order_by(Report.created_at.desc()).first()
            if report:
                report_data = report.report_data or {}
            from db.models import Keyword
            kw_rows = db.query(Keyword).filter(Keyword.project_id == project_id).all()
            for kw in kw_rows:
                keywords.setdefault(kw.keyword_type, []).append(kw.keyword)

    profile_dict = {
        "business_name": profile.business_name,
        "industry": profile.industry,
        "brand_tone": profile.brand_tone,
        "business_description": profile.business_description,
        "products_services": profile.products_services,
    }
    competitors_list = [{"name": c.name} for c in competitors]

    website_prompt = generate_website_prompt(profile_dict, report_data, keywords, competitors_list)
    seasonal_content = generate_seasonal_content(profile_dict)

    output = PromptAgentOutput(
        user_id=current_user.id,
        project_id=project_id,
        website_prompt=website_prompt,
        seasonal_content=seasonal_content,
    )
    db.add(output)

    update_agent_progress(db, current_user.id, "Content & Website Prompt Agent", increment_tasks=1)
    db.add(Notification(
        user_id=current_user.id,
        type="prompt_generated",
        message="New website prompt and seasonal content generated.",
    ))
    db.commit()
    db.refresh(output)
    return output


@router.get("/latest", response_model=PromptAgentResponse)
def get_latest(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    output = (
        db.query(PromptAgentOutput)
        .filter(PromptAgentOutput.user_id == current_user.id)
        .order_by(PromptAgentOutput.created_at.desc())
        .first()
    )
    if not output:
        raise HTTPException(status_code=404, detail="No prompt agent output yet. Generate one first.")
    return output
