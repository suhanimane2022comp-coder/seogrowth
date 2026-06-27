from datetime import datetime
from sqlalchemy.orm import Session
from db.models import AgentProgress


def update_agent_progress(
    db: Session,
    user_id: int,
    agent_name: str,
    status: str = "completed",
    increment_tasks: int = 1,
    progress_pct: float = 100,
):
    """Create or update an AgentProgress row for a given user + agent."""
    row = (
        db.query(AgentProgress)
        .filter(AgentProgress.user_id == user_id, AgentProgress.agent_name == agent_name)
        .first()
    )
    if not row:
        row = AgentProgress(
            user_id=user_id,
            agent_name=agent_name,
            status=status,
            completed_tasks=increment_tasks,
            progress_pct=progress_pct,
            last_execution=datetime.utcnow(),
        )
        db.add(row)
    else:
        row.status = status
        row.completed_tasks = (row.completed_tasks or 0) + increment_tasks
        row.progress_pct = progress_pct
        row.last_execution = datetime.utcnow()
    db.commit()
    return row


AGENT_NAMES = [
    "Business & Audience Agent",
    "Competitor Agent",
    "SEO Agent",
    "Content & Website Prompt Agent",
    "Social Media Strategy Agent",
]


def ensure_default_rows(db: Session, user_id: int):
    for name in AGENT_NAMES:
        exists = (
            db.query(AgentProgress)
            .filter(AgentProgress.user_id == user_id, AgentProgress.agent_name == name)
            .first()
        )
        if not exists:
            db.add(AgentProgress(user_id=user_id, agent_name=name, status="idle", completed_tasks=0, progress_pct=0))
    db.commit()
