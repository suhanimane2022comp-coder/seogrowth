from datetime import date
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from db.database import get_db
from db.models import User, Profile, AudiencePersona, SocialMediaCalendar, SocialMediaPost, Notification
from models.schemas import SocialCalendarRequest, PostStatusUpdate
from api.deps import get_current_user
from agents.social_strategy_agent import (
    determine_platform_priority, generate_content_calendar,
    generate_prime_times, generate_engagement_suggestions,
)
from services.agent_progress import update_agent_progress

router = APIRouter(prefix="/social", tags=["social"])


def _profile_dict(profile: Profile) -> dict:
    return {
        "business_name": profile.business_name,
        "industry": profile.industry,
        "business_type": profile.business_type,
        "target_location": profile.target_location,
        "brand_tone": profile.brand_tone,
    }


def _audience_dict(persona: AudiencePersona) -> dict:
    if not persona:
        return {}
    return {
        "age_group": persona.age_group,
        "interests": persona.interests or [],
        "content_preferences": persona.content_preferences or [],
    }


@router.post("/generate-calendar")
def generate_calendar(
    data: SocialCalendarRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    profile = db.query(Profile).filter(Profile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=400, detail="Please complete your business profile first.")
    persona = db.query(AudiencePersona).filter(AudiencePersona.profile_id == profile.id).first()

    month = data.month or date.today().strftime("%Y-%m")
    profile_dict = _profile_dict(profile)
    audience_dict = _audience_dict(persona)

    priority = determine_platform_priority(profile_dict, audience_dict, data.platforms)
    calendar_data = generate_content_calendar(profile_dict, audience_dict, data.platforms, month)
    prime_times = generate_prime_times(profile_dict, audience_dict, data.platforms)
    engagement = generate_engagement_suggestions(profile_dict, audience_dict)

    calendar = SocialMediaCalendar(
        user_id=current_user.id,
        month=month,
        platforms=data.platforms,
        platform_priority=priority,
        prime_times=prime_times,
        engagement_suggestions=engagement,
    )
    db.add(calendar)
    db.commit()
    db.refresh(calendar)

    for p in calendar_data["posts"]:
        db.add(SocialMediaPost(
            calendar_id=calendar.id,
            date=p["date"],
            platform=p["platform"],
            post_type=p["post_type"],
            caption=p["caption"],
            hashtags=p["hashtags"],
            cta=p["cta"],
            status="Pending",
        ))
    db.commit()

    update_agent_progress(db, current_user.id, "Social Media Strategy Agent", increment_tasks=len(calendar_data["posts"]))
    db.add(Notification(
        user_id=current_user.id,
        type="calendar_generated",
        message=f"New social media calendar generated for {month} ({len(calendar_data['posts'])} posts).",
    ))
    db.commit()

    return get_calendar_detail(calendar.id, db, current_user)


@router.get("/calendars")
def list_calendars(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    calendars = (
        db.query(SocialMediaCalendar)
        .filter(SocialMediaCalendar.user_id == current_user.id)
        .order_by(SocialMediaCalendar.created_at.desc())
        .all()
    )
    return [{"id": c.id, "month": c.month, "platforms": c.platforms, "created_at": c.created_at} for c in calendars]


@router.get("/calendars/{calendar_id}")
def get_calendar_detail(calendar_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    calendar = db.query(SocialMediaCalendar).filter(
        SocialMediaCalendar.id == calendar_id, SocialMediaCalendar.user_id == current_user.id
    ).first()
    if not calendar:
        raise HTTPException(status_code=404, detail="Calendar not found")

    posts = db.query(SocialMediaPost).filter(SocialMediaPost.calendar_id == calendar.id).order_by(SocialMediaPost.date).all()
    total = len(posts)
    posted = len([p for p in posts if p.status == "Posted"])
    completion_pct = round((posted / total) * 100, 1) if total else 0

    return {
        "id": calendar.id,
        "month": calendar.month,
        "platforms": calendar.platforms,
        "platform_priority": calendar.platform_priority,
        "prime_times": calendar.prime_times,
        "engagement_suggestions": calendar.engagement_suggestions,
        "completion_pct": completion_pct,
        "posts": [
            {
                "id": p.id, "date": p.date, "platform": p.platform, "post_type": p.post_type,
                "caption": p.caption, "hashtags": p.hashtags, "cta": p.cta,
                "status": p.status, "actual_posted_date": p.actual_posted_date,
                "engagement_score": p.engagement_score,
            }
            for p in posts
        ],
    }


@router.patch("/posts/{post_id}")
def update_post_status(
    post_id: int,
    data: PostStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    post = (
        db.query(SocialMediaPost)
        .join(SocialMediaCalendar)
        .filter(SocialMediaPost.id == post_id, SocialMediaCalendar.user_id == current_user.id)
        .first()
    )
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    post.status = data.status
    if data.actual_posted_date is not None:
        post.actual_posted_date = data.actual_posted_date
    if data.engagement_score is not None:
        post.engagement_score = data.engagement_score

    if data.status == "Missed":
        db.add(Notification(user_id=current_user.id, type="missed_post", message=f"Missed scheduled post on {post.date} ({post.platform})."))

    db.commit()
    return {"message": "Post updated"}
