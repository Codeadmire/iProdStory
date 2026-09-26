from pydantic import BaseModel
from typing import List, Optional, Any
from datetime import datetime

class ProductCreate(BaseModel):
    url: str

class ProductResponse(BaseModel):
    id: str
    name: Optional[str]
    base_url: str
    category: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True

class CrawlStartRequest(BaseModel):
    max_pages: Optional[int] = 50
    max_depth: Optional[int] = 3
    timeout: Optional[int] = 30000

class CrawlJobResponse(BaseModel):
    id: str
    product_id: str
    status: str
    current_url: Optional[str]
    pages_discovered: int
    pages_processed: int
    failed_pages: int
    screenshots_captured: int
    features_detected: int
    error_message: Optional[str] = None
    max_pages: int
    max_depth: int
    timeout: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class CrawledPageResponse(BaseModel):
    id: str
    url: str
    parent_url: Optional[str]
    title: Optional[str]
    status: Optional[int]
    depth: int
    crawled_at: datetime
    error_message: Optional[str]
    
    class Config:
        from_attributes = True

class FeatureResponse(BaseModel):
    id: str
    name: str
    confidence: str
    
    class Config:
        from_attributes = True

class CampaignPostResponse(BaseModel):
    id: str
    topic: str | None = None
    hook: str | None = None
    body: str | None = None
    cta: str | None = None
    hashtags: str | None = None
    status: str = "Draft"
    
    class Config:
        from_attributes = True

class CampaignPostUpdate(BaseModel):
    topic: str | None = None
    hook: str | None = None
    body: str | None = None
    cta: str | None = None
    hashtags: str | None = None
    status: str = "Draft"

class PostGenerationSettings(BaseModel):
    num_posts: int = 3
    tone: str = "Professional B2B"
    audience: str = "Business Owners"
    content_types: List[str] = ["Product launch", "Feature", "Educational"]
    model: str = "gemini-3.8-flash"

class CampaignUpdate(BaseModel):
    headline: str
    about: str
    posts: List[CampaignPostUpdate]

class CampaignResponse(BaseModel):
    id: str
    headline: str
    about: str
    posts: List[CampaignPostResponse]
    
    class Config:
        from_attributes = True

class AIModelConfig(BaseModel):
    model: str = "gemini-3.8-flash"

class ProductPageBase(BaseModel):
    name: str
    tagline: str
    description: str
    website: str
    target_audience: str
    highlights: str
    status: str = "Draft"

class ProductPageCreate(ProductPageBase):
    pass

class ProductPageUpdate(ProductPageBase):
    pass

class ProductPageResponse(ProductPageBase):
    id: str
    product_id: str
    
    class Config:
        from_attributes = True
