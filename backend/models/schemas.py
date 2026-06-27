from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime


# Auth
class UserRegister(BaseModel):
    email: EmailStr
    name: str
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    email: str
    name: str
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# Project
class ProjectCreate(BaseModel):
    business_name: str
    business_description: str
    products_services: str
    target_audience: str
    target_location: str
    website_url: Optional[str] = None
    competitor_urls: Optional[List[str]] = []


class ProjectResponse(BaseModel):
    id: int
    business_name: str
    business_description: str
    target_location: str
    website_url: Optional[str]
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


# SEO Analysis
class SEOIssue(BaseModel):
    page_url: str
    issue_type: str
    severity: str  # critical, warning, info
    description: str


class PageData(BaseModel):
    url: str
    title: Optional[str]
    meta_description: Optional[str]
    h1: Optional[str]
    h2_tags: List[str] = []
    h3_tags: List[str] = []
    images_count: int = 0
    missing_alt_count: int = 0
    internal_links_count: int = 0
    external_links_count: int = 0
    canonical: Optional[str]
    word_count: int = 0
    issues: List[str] = []


class KeywordData(BaseModel):
    primary: List[str] = []
    secondary: List[str] = []
    long_tail: List[str] = []
    transactional: List[str] = []
    informational: List[str] = []
    local: List[str] = []


class ContentGap(BaseModel):
    missing_pages: List[str] = []
    missing_topics: List[str] = []
    missing_faqs: List[str] = []
    missing_services: List[str] = []
    missing_landing_pages: List[str] = []


class SEOScore(BaseModel):
    technical_score: float = 0
    content_score: float = 0
    keyword_score: float = 0
    metadata_score: float = 0
    overall_score: float = 0


class GeneratedFAQ(BaseModel):
    question: str
    answer: str


class GeneratedMeta(BaseModel):
    page: str
    title: str
    description: str


class GeneratedBlog(BaseModel):
    title: str
    outline: str
    target_keyword: str


class AnalysisRequest(BaseModel):
    project_id: int


class ReportResponse(BaseModel):
    id: int
    project_id: int
    overall_score: float
    report_data: Dict[str, Any]
    created_at: datetime

    class Config:
        from_attributes = True


# ============== Profile (Feature 1) ==============

class ProfileCreate(BaseModel):
    business_name: str
    industry: str
    business_type: str
    website_url: Optional[str] = None
    business_description: str
    products_services: str
    target_location: str
    languages: Optional[List[str]] = []
    keywords: Optional[List[str]] = []
    social_media_links: Optional[Dict[str, str]] = {}
    brand_tone: str


class ProfileResponse(ProfileCreate):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AudiencePersonaResponse(BaseModel):
    id: int
    age_group: Optional[str]
    gender_distribution: Optional[Dict[str, Any]] = {}
    interests: Optional[List[str]] = []
    occupation: Optional[List[str]] = []
    pain_points: Optional[List[str]] = []
    buying_behavior: Optional[str]
    preferred_platforms: Optional[List[str]] = []
    content_preferences: Optional[List[str]] = []

    class Config:
        from_attributes = True


class CompetitorResponse(BaseModel):
    id: int
    name: str
    website_url: Optional[str]
    category: Optional[str]
    domain_authority: Optional[str]
    relevance_reason: Optional[str]

    class Config:
        from_attributes = True


# ============== Analysis (Feature 2) ==============

class AnalyzeRequest(BaseModel):
    website_url: str


# ============== Prompt Agent (Feature 4) ==============

class PromptAgentResponse(BaseModel):
    id: int
    website_prompt: Dict[str, Any]
    seasonal_content: Dict[str, Any]
    created_at: datetime

    class Config:
        from_attributes = True


# ============== Social Media (Feature 5) ==============

class SocialCalendarRequest(BaseModel):
    platforms: List[str]
    month: Optional[str] = None  # "YYYY-MM"; defaults to current month


class PostStatusUpdate(BaseModel):
    status: str  # Pending, Posted, Missed
    actual_posted_date: Optional[str] = None
    engagement_score: Optional[float] = None


# ============== Agent Progress ==============

class AgentProgressResponse(BaseModel):
    agent_name: str
    status: str
    completed_tasks: int
    progress_pct: float
    last_execution: datetime

    class Config:
        from_attributes = True


# ============== Notifications ==============

class NotificationResponse(BaseModel):
    id: int
    type: str
    message: str
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True
