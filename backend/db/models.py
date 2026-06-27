from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey, Boolean, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from db.database import Base


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    projects = relationship("Project", back_populates="owner")


class Project(Base):
    __tablename__ = "projects"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    business_name = Column(String, nullable=False)
    business_description = Column(Text)
    products_services = Column(Text)
    target_audience = Column(Text)
    target_location = Column(String)
    website_url = Column(String)
    competitor_urls = Column(JSON, default=[])
    status = Column(String, default="pending")  # pending, running, completed, failed
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    owner = relationship("User", back_populates="projects")
    audits = relationship("Audit", back_populates="project")
    reports = relationship("Report", back_populates="project")
    keywords = relationship("Keyword", back_populates="project")
    generated_contents = relationship("GeneratedContent", back_populates="project")


class Audit(Base):
    __tablename__ = "audits"
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    business_analysis = Column(JSON)
    seo_issues = Column(JSON)
    content_gaps = Column(JSON)
    seo_scores = Column(JSON)
    pages_crawled = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    project = relationship("Project", back_populates="audits")
    pages = relationship("Page", back_populates="audit")


class Page(Base):
    __tablename__ = "pages"
    id = Column(Integer, primary_key=True, index=True)
    audit_id = Column(Integer, ForeignKey("audits.id"), nullable=False)
    url = Column(String, nullable=False)
    title = Column(String)
    meta_description = Column(Text)
    h1 = Column(String)
    h2_tags = Column(JSON, default=[])
    h3_tags = Column(JSON, default=[])
    images_count = Column(Integer, default=0)
    missing_alt_count = Column(Integer, default=0)
    internal_links_count = Column(Integer, default=0)
    external_links_count = Column(Integer, default=0)
    canonical = Column(String)
    word_count = Column(Integer, default=0)
    issues = Column(JSON, default=[])
    audit = relationship("Audit", back_populates="pages")


class Keyword(Base):
    __tablename__ = "keywords"
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    keyword = Column(String, nullable=False)
    keyword_type = Column(String)  # primary, secondary, long_tail, transactional, informational, local
    created_at = Column(DateTime, default=datetime.utcnow)
    project = relationship("Project", back_populates="keywords")


class GeneratedContent(Base):
    __tablename__ = "generated_contents"
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    content_type = Column(String)  # meta_title, meta_desc, faq, blog_idea, service_page, cta
    title = Column(String)
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    project = relationship("Project", back_populates="generated_contents")


class Report(Base):
    __tablename__ = "reports"
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    report_data = Column(JSON)
    overall_score = Column(Float, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    project = relationship("Project", back_populates="reports")


# ============== Profile / Audience / Competitor (Feature 1) ==============

class Profile(Base):
    __tablename__ = "profiles"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)

    business_name = Column(String, nullable=False)
    industry = Column(String)
    business_type = Column(String)
    website_url = Column(String)
    business_description = Column(Text)
    products_services = Column(Text)
    target_location = Column(String)
    languages = Column(JSON, default=[])
    keywords = Column(JSON, default=[])
    social_media_links = Column(JSON, default={})
    brand_tone = Column(String)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", backref="profile", uselist=False)
    audience_persona = relationship("AudiencePersona", back_populates="profile", uselist=False)
    competitors = relationship("Competitor", back_populates="profile")


class AudiencePersona(Base):
    __tablename__ = "audience_personas"
    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("profiles.id"), unique=True, nullable=False)

    age_group = Column(String)
    gender_distribution = Column(JSON, default={})
    interests = Column(JSON, default=[])
    occupation = Column(JSON, default=[])
    pain_points = Column(JSON, default=[])
    buying_behavior = Column(Text)
    preferred_platforms = Column(JSON, default=[])
    content_preferences = Column(JSON, default=[])

    created_at = Column(DateTime, default=datetime.utcnow)
    profile = relationship("Profile", back_populates="audience_persona")


class Competitor(Base):
    __tablename__ = "competitors"
    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("profiles.id"), nullable=False)

    name = Column(String, nullable=False)
    website_url = Column(String)
    category = Column(String)
    domain_authority = Column(String)
    relevance_reason = Column(Text)

    created_at = Column(DateTime, default=datetime.utcnow)
    profile = relationship("Profile", back_populates="competitors")


# ============== Agent Progress ==============

class AgentProgress(Base):
    __tablename__ = "agent_progress"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    agent_name = Column(String, nullable=False)
    status = Column(String, default="idle")
    completed_tasks = Column(Integer, default=0)
    progress_pct = Column(Float, default=0)
    last_execution = Column(DateTime, default=datetime.utcnow)


# ============== Prompt Agent (Feature 4) ==============

class PromptAgentOutput(Base):
    __tablename__ = "prompt_agent_outputs"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)

    website_prompt = Column(JSON)
    seasonal_content = Column(JSON)

    created_at = Column(DateTime, default=datetime.utcnow)


# ============== Social Media Strategy Agent (Feature 5) ==============

class SocialMediaCalendar(Base):
    __tablename__ = "social_media_calendars"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    month = Column(String)
    platforms = Column(JSON, default=[])
    platform_priority = Column(JSON, default=[])
    prime_times = Column(JSON, default=[])
    engagement_suggestions = Column(JSON, default=[])

    created_at = Column(DateTime, default=datetime.utcnow)
    posts = relationship("SocialMediaPost", back_populates="calendar")


class SocialMediaPost(Base):
    __tablename__ = "social_media_posts"
    id = Column(Integer, primary_key=True, index=True)
    calendar_id = Column(Integer, ForeignKey("social_media_calendars.id"), nullable=False)

    date = Column(String)
    platform = Column(String)
    post_type = Column(String)
    caption = Column(Text)
    hashtags = Column(JSON, default=[])
    cta = Column(String)

    status = Column(String, default="Pending")
    actual_posted_date = Column(String, nullable=True)
    engagement_score = Column(Float, default=0)

    calendar = relationship("SocialMediaCalendar", back_populates="posts")


# ============== Notifications ==============

class Notification(Base):
    __tablename__ = "notifications"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    type = Column(String)
    message = Column(Text)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
