from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from db.database import get_db
from db.models import User, Profile, AudiencePersona, Competitor, Notification
from models.schemas import ProfileCreate, ProfileResponse, AudiencePersonaResponse, CompetitorResponse
from api.deps import get_current_user
from agents.audience_agent import generate_audience_persona
from agents.competitor_agent import find_competitors
from services.agent_progress import update_agent_progress, ensure_default_rows

router = APIRouter(prefix="/profile", tags=["profile"])


@router.get("/", response_model=ProfileResponse)
def get_profile(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    profile = db.query(Profile).filter(Profile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile


@router.post("/", response_model=ProfileResponse)
def create_or_update_profile(
    data: ProfileCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ensure_default_rows(db, current_user.id)

    profile = db.query(Profile).filter(Profile.user_id == current_user.id).first()
    payload = data.model_dump()

    if profile:
        for k, v in payload.items():
            setattr(profile, k, v)
    else:
        profile = Profile(user_id=current_user.id, **payload)
        db.add(profile)

    db.commit()
    db.refresh(profile)

    # ---- Auto-generate audience persona ----
    persona_data = generate_audience_persona(payload)
    persona = db.query(AudiencePersona).filter(AudiencePersona.profile_id == profile.id).first()
    if persona:
        for k, v in persona_data.items():
            setattr(persona, k, v)
    else:
        persona = AudiencePersona(profile_id=profile.id, **persona_data)
        db.add(persona)
    db.commit()

    # ---- Auto-generate competitors ----
    db.query(Competitor).filter(Competitor.profile_id == profile.id).delete()
    competitors_data = find_competitors(payload)
    for c in competitors_data:
        db.add(Competitor(
            profile_id=profile.id,
            name=c.get("name", "Unknown"),
            website_url=c.get("website_url"),
            category=c.get("category"),
            domain_authority=c.get("domain_authority"),
            relevance_reason=c.get("relevance_reason"),
        ))
    db.commit()

    update_agent_progress(db, current_user.id, "Business & Audience Agent", increment_tasks=1)
    update_agent_progress(db, current_user.id, "Competitor Agent", increment_tasks=len(competitors_data))

    db.add(Notification(
        user_id=current_user.id,
        type="profile_updated",
        message=f"Profile saved. Audience persona and {len(competitors_data)} competitors generated.",
    ))
    db.commit()

    db.refresh(profile)
    return profile


@router.get("/audience", response_model=AudiencePersonaResponse)
def get_audience(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    profile = db.query(Profile).filter(Profile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    persona = db.query(AudiencePersona).filter(AudiencePersona.profile_id == profile.id).first()
    if not persona:
        raise HTTPException(status_code=404, detail="Audience persona not found")
    return persona


@router.get("/competitors", response_model=list[CompetitorResponse])
def get_competitors(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    profile = db.query(Profile).filter(Profile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return db.query(Competitor).filter(Competitor.profile_id == profile.id).all()


@router.post("/regenerate-competitors", response_model=list[CompetitorResponse])
def regenerate_competitors(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    profile = db.query(Profile).filter(Profile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    db.query(Competitor).filter(Competitor.profile_id == profile.id).delete()
    payload = ProfileResponse.model_validate(profile).model_dump()
    competitors_data = find_competitors(payload)
    for c in competitors_data:
        db.add(Competitor(
            profile_id=profile.id,
            name=c.get("name", "Unknown"),
            website_url=c.get("website_url"),
            category=c.get("category"),
            domain_authority=c.get("domain_authority"),
            relevance_reason=c.get("relevance_reason"),
        ))
    update_agent_progress(db, current_user.id, "Competitor Agent", increment_tasks=len(competitors_data))
    db.commit()
    return db.query(Competitor).filter(Competitor.profile_id == profile.id).all()
