"""initial multi-tenant schema

Revision ID: 0001
Revises:
Create Date: 2026-09-25
"""
from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── Identity ──────────────────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("hashed_password", sa.String(), nullable=False),
        sa.Column("full_name", sa.String(), nullable=True),
        sa.Column("is_active", sa.Boolean(), default=True),
        sa.Column("is_verified", sa.Boolean(), default=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "workspaces",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("slug", sa.String(), nullable=False),
        sa.Column("owner_id", sa.String(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("plan", sa.String(), default="free"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_workspaces_slug", "workspaces", ["slug"], unique=True)

    op.create_table(
        "workspace_members",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("workspace_id", sa.String(), sa.ForeignKey("workspaces.id"), nullable=False),
        sa.Column("user_id", sa.String(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("role", sa.String(), default="member"),
        sa.UniqueConstraint("workspace_id", "user_id", name="uq_workspace_member"),
    )

    # ── Product & Crawling ────────────────────────────────────────────────────
    op.create_table(
        "products",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("workspace_id", sa.String(), sa.ForeignKey("workspaces.id"), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("base_url", sa.String(), nullable=False),
        sa.Column("category", sa.String(), nullable=True),
        sa.Column("status", sa.String(), default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_products_workspace_id", "products", ["workspace_id"])

    op.create_table(
        "crawl_jobs",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("product_id", sa.String(), sa.ForeignKey("products.id"), nullable=False),
        sa.Column("status", sa.String(), default="QUEUED"),
        sa.Column("progress", sa.Integer(), default=0),
        sa.Column("current_url", sa.String(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("celery_task_id", sa.String(), nullable=True),
        sa.Column("pages_discovered", sa.Integer(), default=0),
        sa.Column("pages_processed", sa.Integer(), default=0),
        sa.Column("failed_pages", sa.Integer(), default=0),
        sa.Column("screenshots_captured", sa.Integer(), default=0),
        sa.Column("features_detected", sa.Integer(), default=0),
        sa.Column("max_pages", sa.Integer(), default=50),
        sa.Column("max_depth", sa.Integer(), default=3),
        sa.Column("timeout", sa.Integer(), default=30000),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_crawl_jobs_product_id", "crawl_jobs", ["product_id"])

    op.create_table(
        "crawled_pages",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("product_id", sa.String(), sa.ForeignKey("products.id"), nullable=False),
        sa.Column("crawl_job_id", sa.String(), sa.ForeignKey("crawl_jobs.id"), nullable=True),
        sa.Column("url", sa.String(), nullable=False),
        sa.Column("parent_url", sa.String(), nullable=True),
        sa.Column("title", sa.String(), nullable=True),
        sa.Column("meta_description", sa.Text(), nullable=True),
        sa.Column("h1", sa.Text(), nullable=True),
        sa.Column("h2", sa.Text(), nullable=True),
        sa.Column("nav_labels", sa.Text(), nullable=True),
        sa.Column("button_texts", sa.Text(), nullable=True),
        sa.Column("visible_text", sa.Text(), nullable=True),
        sa.Column("http_status", sa.Integer(), nullable=True),
        sa.Column("depth", sa.Integer(), default=0),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("crawled_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_crawled_pages_product_id", "crawled_pages", ["product_id"])

    op.create_table(
        "page_screenshots",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("product_id", sa.String(), sa.ForeignKey("products.id"), nullable=False),
        sa.Column("crawl_job_id", sa.String(), sa.ForeignKey("crawl_jobs.id"), nullable=True),
        sa.Column("page_id", sa.String(), sa.ForeignKey("crawled_pages.id"), nullable=True),
        sa.Column("storage_key", sa.String(), nullable=False),
        sa.Column("viewport_width", sa.Integer(), default=1280),
        sa.Column("viewport_height", sa.Integer(), default=800),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
    )

    # ── Intelligence ──────────────────────────────────────────────────────────
    op.create_table(
        "modules",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("product_id", sa.String(), sa.ForeignKey("products.id"), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("display_order", sa.Integer(), default=0),
    )
    op.create_index("ix_modules_product_id", "modules", ["product_id"])

    op.create_table(
        "features",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("product_id", sa.String(), sa.ForeignKey("products.id"), nullable=False),
        sa.Column("module_id", sa.String(), sa.ForeignKey("modules.id"), nullable=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("confidence", sa.String(), default="candidate"),
    )
    op.create_index("ix_features_product_id", "features", ["product_id"])

    op.create_table(
        "feature_evidence",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("feature_id", sa.String(), sa.ForeignKey("features.id"), nullable=False),
        sa.Column("page_id", sa.String(), sa.ForeignKey("crawled_pages.id"), nullable=True),
        sa.Column("evidence_text", sa.Text(), nullable=False),
        sa.Column("source", sa.String(), default="Heading"),
    )

    # ── Campaigns ─────────────────────────────────────────────────────────────
    op.create_table(
        "campaigns",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("product_id", sa.String(), sa.ForeignKey("products.id"), nullable=False),
        sa.Column("headline", sa.String(), nullable=True),
        sa.Column("about", sa.Text(), nullable=True),
        sa.Column("status", sa.String(), default="Draft"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_campaigns_product_id", "campaigns", ["product_id"])

    op.create_table(
        "campaign_posts",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("campaign_id", sa.String(), sa.ForeignKey("campaigns.id"), nullable=False),
        sa.Column("topic", sa.String(), nullable=True),
        sa.Column("hook", sa.Text(), nullable=True),
        sa.Column("body", sa.Text(), nullable=True),
        sa.Column("cta", sa.Text(), nullable=True),
        sa.Column("hashtags", sa.Text(), nullable=True),
        sa.Column("status", sa.String(), default="Draft"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_campaign_posts_campaign_id", "campaign_posts", ["campaign_id"])

    op.create_table(
        "campaign_assets",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("product_id", sa.String(), sa.ForeignKey("products.id"), nullable=False),
        sa.Column("asset_type", sa.String(), default="image"),
        sa.Column("storage_key", sa.String(), nullable=False),
        sa.Column("source_screenshot_id", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "linkedin_product_pages",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("product_id", sa.String(), sa.ForeignKey("products.id"), nullable=False, unique=True),
        sa.Column("name", sa.String(), nullable=True),
        sa.Column("tagline", sa.String(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("website", sa.String(), nullable=True),
        sa.Column("target_audience", sa.String(), nullable=True),
        sa.Column("highlights", sa.Text(), nullable=True),
        sa.Column("status", sa.String(), default="Draft"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )

    # ── Social Publishing ─────────────────────────────────────────────────────
    op.create_table(
        "social_accounts",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("workspace_id", sa.String(), sa.ForeignKey("workspaces.id"), nullable=False),
        sa.Column("platform", sa.String(), nullable=False),
        sa.Column("account_id", sa.String(), nullable=False),
        sa.Column("account_name", sa.String(), nullable=True),
        sa.Column("access_token", sa.Text(), nullable=False),
        sa.Column("refresh_token", sa.Text(), nullable=True),
        sa.Column("token_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("scopes", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), default=True),
        sa.Column("connected_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_social_accounts_workspace_id", "social_accounts", ["workspace_id"])

    op.create_table(
        "social_posts",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("campaign_id", sa.String(), sa.ForeignKey("campaigns.id"), nullable=False),
        sa.Column("campaign_post_id", sa.String(), sa.ForeignKey("campaign_posts.id"), nullable=True),
        sa.Column("social_account_id", sa.String(), sa.ForeignKey("social_accounts.id"), nullable=False),
        sa.Column("platform", sa.String(), nullable=False),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("status", sa.String(), default="Draft"),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("platform_post_id", sa.String(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
    )

    # ── Async Jobs ────────────────────────────────────────────────────────────
    op.create_table(
        "async_jobs",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("workspace_id", sa.String(), sa.ForeignKey("workspaces.id"), nullable=True),
        sa.Column("product_id", sa.String(), sa.ForeignKey("products.id"), nullable=True),
        sa.Column("job_type", sa.String(), nullable=False),
        sa.Column("status", sa.String(), default="queued"),
        sa.Column("progress", sa.Integer(), default=0),
        sa.Column("result", sa.Text(), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("celery_task_id", sa.String(), nullable=True, unique=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("retry_count", sa.Integer(), default=0),
    )
    op.create_index("ix_async_jobs_workspace_id", "async_jobs", ["workspace_id"])
    op.create_index("ix_async_jobs_product_id", "async_jobs", ["product_id"])

    # ── Observability ─────────────────────────────────────────────────────────
    op.create_table(
        "ai_usage",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("workspace_id", sa.String(), sa.ForeignKey("workspaces.id"), nullable=False),
        sa.Column("product_id", sa.String(), sa.ForeignKey("products.id"), nullable=True),
        sa.Column("job_type", sa.String(), nullable=True),
        sa.Column("model", sa.String(), nullable=False),
        sa.Column("input_tokens", sa.Integer(), default=0),
        sa.Column("output_tokens", sa.Integer(), default=0),
        sa.Column("latency_ms", sa.Integer(), default=0),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_ai_usage_workspace_id", "ai_usage", ["workspace_id"])


def downgrade() -> None:
    # Drop in reverse dependency order
    op.drop_table("ai_usage")
    op.drop_table("async_jobs")
    op.drop_table("social_posts")
    op.drop_table("social_accounts")
    op.drop_table("linkedin_product_pages")
    op.drop_table("campaign_assets")
    op.drop_table("campaign_posts")
    op.drop_table("campaigns")
    op.drop_table("feature_evidence")
    op.drop_table("features")
    op.drop_table("modules")
    op.drop_table("page_screenshots")
    op.drop_table("crawled_pages")
    op.drop_table("crawl_jobs")
    op.drop_table("products")
    op.drop_table("workspace_members")
    op.drop_table("workspaces")
    op.drop_table("users")
