"""
Multi-tenant data model for Product Marketing AI SaaS.

Tenant boundary: Workspace
Every resource (Product, Campaign, SocialAccount, etc.) is scoped
to a Workspace and never crosses tenant boundaries.
"""
from sqlalchemy import (
    Column, String, Boolean, DateTime, Text,
    ForeignKey, Integer, Float, UniqueConstraint, Index,
)
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime, timezone
from database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.now(timezone.utc)


# ─── Identity ─────────────────────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=_uuid)
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=_now)
    updated_at = Column(DateTime(timezone=True), default=_now, onupdate=_now)

    memberships = relationship("WorkspaceMember", back_populates="user")


class Workspace(Base):
    """Tenant unit. A user can belong to many workspaces."""
    __tablename__ = "workspaces"

    id = Column(String, primary_key=True, default=_uuid)
    name = Column(String, nullable=False)
    slug = Column(String, unique=True, nullable=False, index=True)
    owner_id = Column(String, ForeignKey("users.id"), nullable=False)
    plan = Column(String, default="free")          # free | starter | pro | enterprise
    created_at = Column(DateTime(timezone=True), default=_now)

    members = relationship("WorkspaceMember", back_populates="workspace")
    products = relationship("Product", back_populates="workspace")
    social_accounts = relationship("SocialAccount", back_populates="workspace")
    ai_usage = relationship("AIUsage", back_populates="workspace")


class WorkspaceMember(Base):
    __tablename__ = "workspace_members"
    __table_args__ = (UniqueConstraint("workspace_id", "user_id"),)

    id = Column(String, primary_key=True, default=_uuid)
    workspace_id = Column(String, ForeignKey("workspaces.id"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    role = Column(String, default="member")        # owner | admin | member

    workspace = relationship("Workspace", back_populates="members")
    user = relationship("User", back_populates="memberships")


# ─── Product & Crawling ───────────────────────────────────────────────────────

class Product(Base):
    __tablename__ = "products"

    id = Column(String, primary_key=True, default=_uuid)
    workspace_id = Column(String, ForeignKey("workspaces.id"), nullable=False, index=True)
    name = Column(String, nullable=False)
    base_url = Column(String, nullable=False)
    category = Column(String, nullable=True)
    status = Column(String, default="active")      # active | archived
    created_at = Column(DateTime(timezone=True), default=_now)
    updated_at = Column(DateTime(timezone=True), default=_now, onupdate=_now)

    workspace = relationship("Workspace", back_populates="products")
    crawl_jobs = relationship("CrawlJob", back_populates="product")
    pages = relationship("CrawledPage", back_populates="product")
    features = relationship("Feature", back_populates="product")
    screenshots = relationship("PageScreenshot", back_populates="product")
    modules = relationship("Module", back_populates="product")
    campaigns = relationship("Campaign", back_populates="product")
    linkedin_page = relationship("LinkedInProductPage", back_populates="product", uselist=False)
    assets = relationship("CampaignAsset", back_populates="product")
    ai_usage = relationship("AIUsage", back_populates="product")


class CrawlJob(Base):
    """Tracks a single crawl run. Created by the API, executed by the worker."""
    __tablename__ = "crawl_jobs"

    id = Column(String, primary_key=True, default=_uuid)
    product_id = Column(String, ForeignKey("products.id"), nullable=False, index=True)

    # Lifecycle
    status = Column(String, default="QUEUED")
    # QUEUED → RUNNING → COMPLETED | COMPLETED_WITH_WARNINGS | FAILED
    progress = Column(Integer, default=0)          # 0–100
    current_url = Column(String, nullable=True)
    error_message = Column(Text, nullable=True)
    celery_task_id = Column(String, nullable=True)

    # Stats
    pages_discovered = Column(Integer, default=0)
    pages_processed = Column(Integer, default=0)
    failed_pages = Column(Integer, default=0)
    screenshots_captured = Column(Integer, default=0)
    features_detected = Column(Integer, default=0)

    # Configuration snapshot (so we know what settings were used)
    max_pages = Column(Integer, default=50)
    max_depth = Column(Integer, default=3)
    timeout = Column(Integer, default=30_000)

    created_at = Column(DateTime(timezone=True), default=_now)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    product = relationship("Product", back_populates="crawl_jobs")


class CrawledPage(Base):
    __tablename__ = "crawled_pages"

    id = Column(String, primary_key=True, default=_uuid)
    product_id = Column(String, ForeignKey("products.id"), nullable=False, index=True)
    crawl_job_id = Column(String, ForeignKey("crawl_jobs.id"), nullable=True, index=True)
    url = Column(String, nullable=False)
    parent_url = Column(String, nullable=True)
    title = Column(String, nullable=True)
    meta_description = Column(Text, nullable=True)
    h1 = Column(Text, nullable=True)               # JSON array
    h2 = Column(Text, nullable=True)               # JSON array
    nav_labels = Column(Text, nullable=True)        # JSON array
    button_texts = Column(Text, nullable=True)      # JSON array
    visible_text = Column(Text, nullable=True)      # Truncated at 5 000 chars
    http_status = Column(Integer, nullable=True)
    depth = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    crawled_at = Column(DateTime(timezone=True), default=_now)

    product = relationship("Product", back_populates="pages")
    screenshots = relationship("PageScreenshot", back_populates="page")
    feature_evidence = relationship("FeatureEvidence", back_populates="page")


class PageScreenshot(Base):
    __tablename__ = "page_screenshots"

    id = Column(String, primary_key=True, default=_uuid)
    product_id = Column(String, ForeignKey("products.id"), nullable=False)
    crawl_job_id = Column(String, ForeignKey("crawl_jobs.id"), nullable=True)
    page_id = Column(String, ForeignKey("crawled_pages.id"), nullable=True)
    storage_key = Column(String, nullable=False)   # S3 key or local relative path
    viewport_width = Column(Integer, default=1280)
    viewport_height = Column(Integer, default=800)
    created_at = Column(DateTime(timezone=True), default=_now)

    product = relationship("Product", back_populates="screenshots")
    page = relationship("CrawledPage", back_populates="screenshots")


# ─── Product Intelligence ─────────────────────────────────────────────────────

class Module(Base):
    """AI-generated logical grouping of features."""
    __tablename__ = "modules"

    id = Column(String, primary_key=True, default=_uuid)
    product_id = Column(String, ForeignKey("products.id"), nullable=False, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    display_order = Column(Integer, default=0)

    product = relationship("Product", back_populates="modules")
    features = relationship("Feature", back_populates="module")


class Feature(Base):
    __tablename__ = "features"

    id = Column(String, primary_key=True, default=_uuid)
    product_id = Column(String, ForeignKey("products.id"), nullable=False, index=True)
    module_id = Column(String, ForeignKey("modules.id"), nullable=True)
    name = Column(String, nullable=False)
    confidence = Column(String, default="candidate")
    # candidate → detected → confirmed

    product = relationship("Product", back_populates="features")
    module = relationship("Module", back_populates="features")
    evidence = relationship("FeatureEvidence", back_populates="feature")


class FeatureEvidence(Base):
    __tablename__ = "feature_evidence"

    id = Column(String, primary_key=True, default=_uuid)
    feature_id = Column(String, ForeignKey("features.id"), nullable=False)
    page_id = Column(String, ForeignKey("crawled_pages.id"), nullable=True)
    evidence_text = Column(Text, nullable=False)
    source = Column(String, default="Heading")     # Heading | NavLink | Button | Meta

    feature = relationship("Feature", back_populates="evidence")
    page = relationship("CrawledPage", back_populates="feature_evidence")


# ─── Campaigns & Content ──────────────────────────────────────────────────────

class Campaign(Base):
    __tablename__ = "campaigns"

    id = Column(String, primary_key=True, default=_uuid)
    product_id = Column(String, ForeignKey("products.id"), nullable=False, index=True)
    headline = Column(String, nullable=True)
    about = Column(Text, nullable=True)
    status = Column(String, default="Draft")
    # Draft | In Review | Approved | Archived
    created_at = Column(DateTime(timezone=True), default=_now)
    updated_at = Column(DateTime(timezone=True), default=_now, onupdate=_now)

    product = relationship("Product", back_populates="campaigns")
    posts = relationship("CampaignPost", back_populates="campaign", cascade="all, delete-orphan")
    social_posts = relationship("SocialPost", back_populates="campaign")


class CampaignPost(Base):
    __tablename__ = "campaign_posts"

    id = Column(String, primary_key=True, default=_uuid)
    campaign_id = Column(String, ForeignKey("campaigns.id"), nullable=False, index=True)
    topic = Column(String, nullable=True)
    hook = Column(Text, nullable=True)
    body = Column(Text, nullable=True)
    cta = Column(Text, nullable=True)
    hashtags = Column(Text, nullable=True)
    status = Column(String, default="Draft")
    # Draft | In Review | Approved | Rejected
    created_at = Column(DateTime(timezone=True), default=_now)

    campaign = relationship("Campaign", back_populates="posts")


class CampaignAsset(Base):
    """Generated marketing images / media assets linked to a product."""
    __tablename__ = "campaign_assets"

    id = Column(String, primary_key=True, default=_uuid)
    product_id = Column(String, ForeignKey("products.id"), nullable=False, index=True)
    asset_type = Column(String, default="image")   # image | video | banner
    storage_key = Column(String, nullable=False)
    source_screenshot_id = Column(String, ForeignKey("page_screenshots.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=_now)

    product = relationship("Product", back_populates="assets")


class LinkedInProductPage(Base):
    __tablename__ = "linkedin_product_pages"

    id = Column(String, primary_key=True, default=_uuid)
    product_id = Column(String, ForeignKey("products.id"), nullable=False, unique=True)
    name = Column(String, nullable=True)
    tagline = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    website = Column(String, nullable=True)
    target_audience = Column(String, nullable=True)
    highlights = Column(Text, nullable=True)
    status = Column(String, default="Draft")
    # Draft | In Review | Approved
    created_at = Column(DateTime(timezone=True), default=_now)
    updated_at = Column(DateTime(timezone=True), default=_now, onupdate=_now)

    product = relationship("Product", back_populates="linkedin_page")


# ─── Social Publishing ────────────────────────────────────────────────────────

class SocialAccount(Base):
    """OAuth-connected social media account belonging to a workspace."""
    __tablename__ = "social_accounts"

    id = Column(String, primary_key=True, default=_uuid)
    workspace_id = Column(String, ForeignKey("workspaces.id"), nullable=False, index=True)
    platform = Column(String, nullable=False)      # linkedin | twitter | instagram
    account_id = Column(String, nullable=False)    # Platform user/page ID
    account_name = Column(String, nullable=True)
    access_token = Column(Text, nullable=False)    # Encrypted at rest in production
    refresh_token = Column(Text, nullable=True)
    token_expires_at = Column(DateTime(timezone=True), nullable=True)
    scopes = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    connected_at = Column(DateTime(timezone=True), default=_now)

    workspace = relationship("Workspace", back_populates="social_accounts")
    social_posts = relationship("SocialPost", back_populates="social_account")


class SocialPost(Base):
    """A CampaignPost adapted for a specific social platform and account."""
    __tablename__ = "social_posts"

    id = Column(String, primary_key=True, default=_uuid)
    campaign_id = Column(String, ForeignKey("campaigns.id"), nullable=False, index=True)
    campaign_post_id = Column(String, ForeignKey("campaign_posts.id"), nullable=True)
    social_account_id = Column(String, ForeignKey("social_accounts.id"), nullable=False)
    platform = Column(String, nullable=False)
    content = Column(Text, nullable=True)
    status = Column(String, default="Draft")
    # Draft | Scheduled | Published | Failed
    scheduled_at = Column(DateTime(timezone=True), nullable=True)
    published_at = Column(DateTime(timezone=True), nullable=True)
    platform_post_id = Column(String, nullable=True)  # ID returned by platform API
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=_now)

    campaign = relationship("Campaign", back_populates="social_posts")
    social_account = relationship("SocialAccount", back_populates="social_posts")


# ─── Jobs (generic async task tracking) ──────────────────────────────────────

class AsyncJob(Base):
    """
    Generic job record for every background operation (crawl, AI analysis,
    media generation, publish). The frontend polls GET /api/jobs/{id}.
    """
    __tablename__ = "async_jobs"

    id = Column(String, primary_key=True, default=_uuid)
    workspace_id = Column(String, ForeignKey("workspaces.id"), nullable=True, index=True)
    product_id = Column(String, ForeignKey("products.id"), nullable=True, index=True)
    job_type = Column(String, nullable=False)
    # crawl | ai_analyze | media_generate | campaign_generate | publish
    status = Column(String, default="queued")
    # queued | running | succeeded | failed | retrying
    progress = Column(Integer, default=0)           # 0–100
    result = Column(Text, nullable=True)            # JSON result payload
    error = Column(Text, nullable=True)
    celery_task_id = Column(String, nullable=True, unique=True)
    created_at = Column(DateTime(timezone=True), default=_now)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    retry_count = Column(Integer, default=0)


# ─── Observability & Billing ──────────────────────────────────────────────────

class AIUsage(Base):
    """Tracks every Gemini API call for billing and quota enforcement."""
    __tablename__ = "ai_usage"

    id = Column(String, primary_key=True, default=_uuid)
    workspace_id = Column(String, ForeignKey("workspaces.id"), nullable=False, index=True)
    product_id = Column(String, ForeignKey("products.id"), nullable=True)
    job_type = Column(String, nullable=True)        # analyze | campaign | posts | page
    model = Column(String, nullable=False)
    input_tokens = Column(Integer, default=0)
    output_tokens = Column(Integer, default=0)
    latency_ms = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), default=_now)

    workspace = relationship("Workspace", back_populates="ai_usage")
    product = relationship("Product", back_populates="ai_usage")
