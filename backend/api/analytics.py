from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from db.database import get_db
from db.models import (
    User, Project, Report, Audit, Keyword, Profile, AudiencePersona,
    Competitor, SocialMediaCalendar, SocialMediaPost, AgentProgress, PromptAgentOutput,
)
from api.deps import get_current_user
from services.agent_progress import ensure_default_rows

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/seo")
def seo_analytics(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    projects = db.query(Project).filter(Project.user_id == current_user.id).order_by(Project.created_at).all()
    trend = []
    for p in projects:
        report = db.query(Report).filter(Report.project_id == p.id).order_by(Report.created_at).first()
        audit = db.query(Audit).filter(Audit.project_id == p.id).order_by(Audit.created_at).first()
        if report:
            scores = (audit.seo_scores if audit else {}) or {}
            trend.append({
                "label": p.created_at.strftime("%b %d"),
                "seo_score": report.overall_score or 0,
                "technical_score": scores.get("technical_score", 0),
                "content_score": scores.get("content_score", 0),
                "keyword_score": scores.get("keyword_score", 0),
            })
    return {"trend": trend}


@router.get("/competitors")
def competitor_analytics(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    profile = db.query(Profile).filter(Profile.user_id == current_user.id).first()
    if not profile:
        return {"competitors": []}
    competitors = db.query(Competitor).filter(Competitor.profile_id == profile.id).all()
    da_map = {"high": 90, "medium": 60, "low": 30}

    def score_of(c):
        if c.domain_authority and c.domain_authority.replace(".", "").isdigit():
            return float(c.domain_authority)
        return da_map.get((c.domain_authority or "").lower(), 50)

    return {
        "competitors": [
            {"name": c.name, "domain_authority_score": score_of(c), "category": c.category}
            for c in competitors
        ]
    }


@router.get("/audience")
def audience_analytics(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    profile = db.query(Profile).filter(Profile.user_id == current_user.id).first()
    if not profile:
        return {"gender": [], "age_group": None}
    persona = db.query(AudiencePersona).filter(AudiencePersona.profile_id == profile.id).first()
    if not persona:
        return {"gender": [], "age_group": None}
    gender_dist = persona.gender_distribution or {}
    return {
        "gender": [{"name": k.capitalize(), "value": v} for k, v in gender_dist.items()],
        "age_group": persona.age_group,
        "interests": persona.interests or [],
    }


@router.get("/social")
def social_analytics(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    calendars = db.query(SocialMediaCalendar).filter(SocialMediaCalendar.user_id == current_user.id).all()
    calendar_ids = [c.id for c in calendars]
    posts = db.query(SocialMediaPost).filter(SocialMediaPost.calendar_id.in_(calendar_ids)).all() if calendar_ids else []

    by_month = {}
    platform_dist = {}
    for p in posts:
        cal = next((c for c in calendars if c.id == p.calendar_id), None)
        month = cal.month if cal else "unknown"
        by_month.setdefault(month, {"month": month, "published": 0, "engagement": 0.0})
        if p.status == "Posted":
            by_month[month]["published"] += 1
            by_month[month]["engagement"] += p.engagement_score or 0
        platform_dist[p.platform] = platform_dist.get(p.platform, 0) + 1

    return {
        "posts_published": list(by_month.values()),
        "platform_distribution": [{"name": k, "value": v} for k, v in platform_dist.items()],
        "total_posts": len(posts),
        "total_posted": len([p for p in posts if p.status == "Posted"]),
    }


@router.get("/agents")
def agent_analytics(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    ensure_default_rows(db, current_user.id)
    rows = db.query(AgentProgress).filter(AgentProgress.user_id == current_user.id).all()
    return [
        {
            "agent_name": r.agent_name,
            "status": r.status,
            "completed_tasks": r.completed_tasks,
            "progress_pct": r.progress_pct,
            "last_execution": r.last_execution,
        }
        for r in rows
    ]
