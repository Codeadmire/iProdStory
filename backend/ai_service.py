import os
import json
from sqlalchemy.orm import Session
from pydantic import BaseModel
import models

# Set up Gemini
from google import genai
from google.genai import types

def analyze_product_features(product_id: str, db: Session, model_name: str = "gemini-1.5-flash-002"):
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product:
        return
        
    features = db.query(models.Feature).filter(models.Feature.product_id == product_id).all()
    pages = db.query(models.CrawledPage).filter(models.CrawledPage.product_id == product_id).all()
    
    # We will pass the list of pages and existing features to the LLM to get a structured output
    feature_names = [f.name for f in features]
    page_urls = [p.url for p in pages]
    
    prompt = f"""
    You are an expert SaaS product marketer. We crawled a product at {product.base_url}.
    We found {len(pages)} pages and extracted {len(features)} candidate features from headings and menus.
    
    Candidate features:
    {json.dumps(feature_names[:100])}
    
    Your task:
    Group these candidate features into 3-5 logical Core Modules (e.g. "Inventory Management", "Sales", "Dashboard").
    For each module, provide a description, and select the top 3-5 best features that belong to it from the candidate list (clean up the names to sound like features).
    
    Respond in JSON format exactly like this:
    {{
        "modules": [
            {{
                "name": "Module Name",
                "description": "Module description for marketing",
                "features": ["Feature 1", "Feature 2"]
            }}
        ]
    }}
    """
    
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("No GEMINI_API_KEY found, using mock data for AI analysis.")
        return mock_analyze_features(product_id, db, product.base_url)
        
    client = genai.Client(api_key=api_key)
    
    try:
        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
            ),
        )
        data = json.loads(response.text)
        process_ai_result(data, product_id, db)
    except Exception as e:
        print(f"AI API Error: {e}")
        raise

def process_ai_result(data: dict, product_id: str, db: Session):
    # First delete old modules for idempotency
    db.query(models.Module).filter(models.Module.product_id == product_id).delete()
    db.commit()
    
    for mod in data.get("modules", []):
        db_mod = models.Module(
            product_id=product_id,
            name=mod.get("name"),
            description=mod.get("description")
        )
        db.add(db_mod)
        db.commit()
        db.refresh(db_mod)
        
        for feat_name in mod.get("features", []):
            db_feat = models.Feature(
                product_id=product_id,
                module_id=db_mod.id,
                name=feat_name,
                confidence="confirmed"
            )
            db.add(db_feat)
        db.commit()

def mock_analyze_features(product_id: str, db: Session, url: str):
    import time
    time.sleep(3) # Simulate AI thinking
    
    mock_data = {
        "modules": [
            {
                "name": "Inventory & Stock",
                "description": "Real-time visibility into stock levels, warehouses, and locations.",
                "features": ["Multi-warehouse support", "Stock adjustments", "Batch & serial tracking"]
            },
            {
                "name": "Sales & Orders",
                "description": "Manage the entire order-to-cash process seamlessly.",
                "features": ["Quotations", "Sales Orders", "Invoicing", "Point of Sale (POS)"]
            },
            {
                "name": "Purchasing & Suppliers",
                "description": "Streamline procurement and build stronger supplier relationships.",
                "features": ["Purchase Orders", "Goods Receipts", "Supplier Management"]
            }
        ]
    }
    process_ai_result(mock_data, product_id, db)
