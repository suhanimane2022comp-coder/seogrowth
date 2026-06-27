from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
from db.database import get_db
from db.models import User, Project, Audit, Page, Keyword, GeneratedContent, Report, Profile, Notification
from models.schemas import ProjectCreate, ProjectResponse, AnalyzeRequest
from api.deps import get_current_user
from services.workflow import run_seo_analysis
from services.agent_progress import update_agent_progress
import json

router = APIRouter(prefix="/projects", tags=["projects"])


def run_analysis_task(project_id: int, db_url: str, user_id: int = None):
    """Background task to run SEO analysis."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from db.models import Project, Audit, Page, Keyword, GeneratedContent, Report, Notification
    from services.agent_progress import update_agent_progress

    engine = create_engine(db_url, connect_args={"check_same_thread": False})
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    try:
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return

        project.status = "running"
        db.commit()

        result = run_seo_analysis(
            business_name=project.business_name,
            business_description=project.business_description,
            products_services=project.products_services,
            target_audience=project.target_audience,
            target_location=project.target_location,
            website_url=project.website_url,
            competitor_urls=project.competitor_urls or [],
        )

        # Save audit
        audit = Audit(
            project_id=project_id,
            business_analysis=result.get("business_analysis"),
            seo_issues=result.get("seo_issues"),
            content_gaps=result.get("content_gaps"),
            seo_scores=result.get("seo_scores"),
            pages_crawled=result.get("pages_crawled", 0),
        )
        db.add(audit)
        db.flush()

        # Save pages
        for p in result.get("crawled_pages", []):
            page = Page(
                audit_id=audit.id,
                url=p["url"],
                title=p.get("title"),
                meta_description=p.get("meta_description"),
                h1=p.get("h1"),
                h2_tags=p.get("h2_tags", []),
                h3_tags=p.get("h3_tags", []),
                images_count=p.get("images_count", 0),
                missing_alt_count=p.get("missing_alt_count", 0),
                internal_links_count=p.get("internal_links_count", 0),
                external_links_count=p.get("external_links_count", 0),
                canonical=p.get("canonical"),
                word_count=p.get("word_count", 0),
                issues=p.get("issues", []),
            )
            db.add(page)

        # Save keywords
        for kw_type, kw_list in result.get("keywords", {}).items():
            for kw in kw_list:
                keyword = Keyword(project_id=project_id, keyword=kw, keyword_type=kw_type)
                db.add(keyword)

        # Save generated content
        content = result.get("generated_content", {})
        for meta in content.get("metadata", []):
            gc = GeneratedContent(
                project_id=project_id,
                content_type="metadata",
                title=meta.get("page"),
                content=json.dumps(meta),
            )
            db.add(gc)
        for faq in content.get("faqs", []):
            gc = GeneratedContent(
                project_id=project_id,
                content_type="faq",
                title=faq.get("question"),
                content=faq.get("answer"),
            )
            db.add(gc)
        for blog in content.get("blog_ideas", []):
            gc = GeneratedContent(
                project_id=project_id,
                content_type="blog_idea",
                title=blog.get("title"),
                content=blog.get("outline"),
            )
            db.add(gc)

        # Save report
        report = Report(
            project_id=project_id,
            report_data=result.get("report"),
            overall_score=result.get("seo_scores", {}).get("overall_score", 0),
        )
        db.add(report)

        project.status = "completed"
        db.commit()

        if user_id:
            update_agent_progress(db, user_id, "SEO Agent", status="completed", increment_tasks=1, progress_pct=100)
            db.add(Notification(
                user_id=user_id,
                type="new_report",
                message=f"New SEO report available for {project.business_name}.",
            ))
            db.commit()

    except Exception as e:
        project = db.query(Project).filter(Project.id == project_id).first()
        if project:
            project.status = "failed"
            db.commit()
        if user_id:
            update_agent_progress(db, user_id, "SEO Agent", status="failed", increment_tasks=0, progress_pct=0)
        print(f"Analysis failed for project {project_id}: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


@router.post("/", response_model=ProjectResponse)
def create_project(
    data: AnalyzeRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    profile = db.query(Profile).filter(Profile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=400, detail="Please complete your business profile before running an analysis.")

    if not data.website_url or not data.website_url.strip():
        raise HTTPException(status_code=422, detail="Website URL is required")

    persona = profile.audience_persona
    if persona and persona.interests:
        audience_text = f"{persona.age_group or ''} {profile.industry or ''} audience interested in {', '.join(persona.interests[:4])}".strip()
    else:
        audience_text = profile.industry or "General audience"

    project = Project(
        user_id=current_user.id,
        business_name=profile.business_name,
        business_description=profile.business_description,
        products_services=profile.products_services,
        target_audience=audience_text,
        target_location=profile.target_location,
        website_url=data.website_url,
        competitor_urls=[c.website_url for c in profile.competitors if c.website_url] if profile.competitors else [],
        status="pending",
    )
    db.add(project)
    db.commit()
    db.refresh(project)

    update_agent_progress(db, current_user.id, "SEO Agent", status="running", increment_tasks=0, progress_pct=10)

    from core.config import settings
    background_tasks.add_task(run_analysis_task, project.id, settings.DATABASE_URL, current_user.id)

    return project


@router.get("/", response_model=List[ProjectResponse])
def get_projects(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return db.query(Project).filter(Project.user_id == current_user.id).order_by(Project.created_at.desc()).all()


@router.get("/{project_id}")
def get_project(
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

    report = db.query(Report).filter(Report.project_id == project_id).order_by(Report.created_at.desc()).first()
    audit = db.query(Audit).filter(Audit.project_id == project_id).order_by(Audit.created_at.desc()).first()

    return {
        "id": project.id,
        "business_name": project.business_name,
        "business_description": project.business_description,
        "products_services": project.products_services,
        "target_audience": project.target_audience,
        "target_location": project.target_location,
        "website_url": project.website_url,
        "competitor_urls": project.competitor_urls,
        "status": project.status,
        "created_at": project.created_at,
        "report": report.report_data if report else None,
        "overall_score": report.overall_score if report else None,
        "pages_crawled": audit.pages_crawled if audit else 0,
        "seo_issues": audit.seo_issues if audit else [],
        "seo_scores": audit.seo_scores if audit else {},
    }


@router.delete("/{project_id}")
def delete_project(
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

    db.delete(project)
    db.commit()
    return {"message": "Project deleted"}
