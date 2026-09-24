import os
import zipfile
import json
from io import BytesIO
from sqlalchemy.orm import Session
import models

def create_export_zip(product_id: str, db: Session):
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product:
        return None
        
    modules = db.query(models.Module).filter(models.Module.product_id == product_id).all()
    
    zip_buffer = BytesIO()
    
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        # 1. Product Intelligence JSON
        intelligence_data = {
            "product_url": product.base_url,
            "modules": []
        }
        for m in modules:
            mod_data = {
                "name": m.name,
                "description": m.description,
                "features": [{"name": f.name} for f in m.features]
            }
            intelligence_data["modules"].append(mod_data)
            
        zf.writestr("product_intelligence.json", json.dumps(intelligence_data, indent=2))
        
        # 2. LinkedIn Campaign
        campaign = db.query(models.Campaign).filter(models.Campaign.product_id == product_id).first()
        campaign_data = {}
        if campaign:
            posts = db.query(models.CampaignPost).filter(models.CampaignPost.campaign_id == campaign.id).all()
            campaign_data = {
                "product_page": {
                    "headline": campaign.headline,
                    "about": campaign.about
                },
                "launch_posts": [p.content for p in posts]
            }
        zf.writestr("linkedin_campaign.json", json.dumps(campaign_data, indent=2))
        
        # 3. Raw Screenshots
        screenshots_dir = "screenshots"
        if os.path.exists(screenshots_dir):
            for filename in os.listdir(screenshots_dir):
                if filename.startswith(product_id):
                    filepath = os.path.join(screenshots_dir, filename)
                    zf.write(filepath, f"assets/screenshots/{filename}")
                    
        # 4. Marketing Media
        media_dir = "media_assets"
        if os.path.exists(media_dir):
            for filename in os.listdir(media_dir):
                if filename.startswith(f"marketing_{product_id}"):
                    filepath = os.path.join(media_dir, filename)
                    zf.write(filepath, f"assets/marketing_media/{filename}")
                    
    zip_buffer.seek(0)
    return zip_buffer
