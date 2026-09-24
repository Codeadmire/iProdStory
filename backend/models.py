from sqlalchemy import Column, String, Boolean, DateTime, Text, ForeignKey, Integer
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime
from database import Base

def generate_uuid():
    return str(uuid.uuid4())

class Product(Base):
    __tablename__ = "products"
    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String)
    base_url = Column(String)
    category = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    crawl_jobs = relationship("CrawlJob", back_populates="product")
    pages = relationship("CrawledPage", back_populates="product")
    features = relationship("Feature", back_populates="product")
    screenshots = relationship("PageScreenshot", back_populates="product")
    modules = relationship("Module", back_populates="product")

class Module(Base):
    __tablename__ = "modules"
    id = Column(String, primary_key=True, default=generate_uuid)
    product_id = Column(String, ForeignKey("products.id"))
    name = Column(String)
    description = Column(Text, nullable=True)
    
    product = relationship("Product", back_populates="modules")
    features = relationship("Feature", back_populates="module")

class CrawlJob(Base):
    __tablename__ = "crawl_jobs"
    id = Column(String, primary_key=True, default=generate_uuid)
    product_id = Column(String, ForeignKey("products.id"))
    status = Column(String, default="PENDING") # PENDING, RUNNING, COMPLETED, COMPLETED_WITH_WARNINGS, FAILED
    current_url = Column(String, nullable=True)
    pages_discovered = Column(Integer, default=0)
    pages_processed = Column(Integer, default=0)
    failed_pages = Column(Integer, default=0)
    screenshots_captured = Column(Integer, default=0)
    features_detected = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    
    # Configuration
    max_pages = Column(Integer, default=50)
    max_depth = Column(Integer, default=3)
    timeout = Column(Integer, default=30000)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    product = relationship("Product", back_populates="crawl_jobs")

class CrawledPage(Base):
    __tablename__ = "crawled_pages"
    id = Column(String, primary_key=True, default=generate_uuid)
    product_id = Column(String, ForeignKey("products.id"))
    url = Column(String)
    parent_url = Column(String, nullable=True)
    title = Column(String, nullable=True)
    meta_description = Column(Text, nullable=True)
    h1 = Column(Text, nullable=True)  # Stored as JSON or comma-separated
    h2 = Column(Text, nullable=True)
    nav_labels = Column(Text, nullable=True)
    button_texts = Column(Text, nullable=True)
    visible_text = Column(Text, nullable=True)
    status = Column(Integer, nullable=True)
    depth = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    crawled_at = Column(DateTime, default=datetime.utcnow)
    
    product = relationship("Product", back_populates="pages")
    screenshots = relationship("PageScreenshot", back_populates="page")
    features = relationship("FeatureEvidence", back_populates="page")

class PageScreenshot(Base):
    __tablename__ = "page_screenshots"
    id = Column(String, primary_key=True, default=generate_uuid)
    product_id = Column(String, ForeignKey("products.id"))
    page_id = Column(String, ForeignKey("crawled_pages.id"))
    image_path = Column(String)
    viewport_width = Column(Integer, default=1280)
    viewport_height = Column(Integer, default=800)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    product = relationship("Product", back_populates="screenshots")
    page = relationship("CrawledPage", back_populates="screenshots")
    
class Feature(Base):
    __tablename__ = "features"
    id = Column(String, primary_key=True, default=generate_uuid)
    product_id = Column(String, ForeignKey("products.id"))
    module_id = Column(String, ForeignKey("modules.id"), nullable=True)
    name = Column(String)
    confidence = Column(String, default="candidate") # candidate, detected, confirmed
    
    product = relationship("Product", back_populates="features")
    module = relationship("Module", back_populates="features")
    evidence = relationship("FeatureEvidence", back_populates="feature")

class FeatureEvidence(Base):
    __tablename__ = "feature_evidence"
    id = Column(String, primary_key=True, default=generate_uuid)
    feature_id = Column(String, ForeignKey("features.id"))
    page_id = Column(String, ForeignKey("crawled_pages.id"), nullable=True)
    evidence_text = Column(Text)
    source = Column(String, default="CRAWLED_PAGE")
    
    feature = relationship("Feature", back_populates="evidence")
    page = relationship("CrawledPage", back_populates="features")

class Campaign(Base):
    __tablename__ = "campaigns"
    id = Column(String, primary_key=True, default=generate_uuid)
    product_id = Column(String, ForeignKey("products.id"))
    headline = Column(String)
    about = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    product = relationship("Product")
    posts = relationship("CampaignPost", back_populates="campaign")

class CampaignPost(Base):
    __tablename__ = "campaign_posts"
    id = Column(String, primary_key=True, default=generate_uuid)
    campaign_id = Column(String, ForeignKey("campaigns.id"))
    topic = Column(String, nullable=True) # E.g. Product launch, Feature
    hook = Column(Text, nullable=True)
    body = Column(Text, nullable=True)
    cta = Column(Text, nullable=True)
    hashtags = Column(Text, nullable=True)
    status = Column(String, default="Draft") # Draft, In Review, Approved, Rejected
    evidence_references = Column(Text, nullable=True) # Stored as JSON string
    created_at = Column(DateTime, default=datetime.utcnow)
    
    campaign = relationship("Campaign", back_populates="posts")

class LinkedInProductPage(Base):
    __tablename__ = "linkedin_product_pages"
    id = Column(String, primary_key=True, default=generate_uuid)
    product_id = Column(String, ForeignKey("products.id"))
    name = Column(String)
    tagline = Column(String)
    description = Column(Text)
    website = Column(String)
    target_audience = Column(String)
    highlights = Column(Text)
    status = Column(String, default="Draft") # Draft, In Review, Approved
    created_at = Column(DateTime, default=datetime.utcnow)
