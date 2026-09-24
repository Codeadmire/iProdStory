import os
import json
import time
from sqlalchemy.orm import Session
import models
from google import genai
from google.genai import types

def generate_linkedin_campaign(product_id: str, config: dict, db: Session):
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product:
        return
        
    modules = db.query(models.Module).filter(models.Module.product_id == product_id).all()
    
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("No GEMINI_API_KEY found, using mock data for content generation.")
        return mock_generate_content(product_id, config, db)
        
    # Example AI prompt
    prompt = f"""
    You are an expert B2B SaaS LinkedIn marketer.
    We are generating a campaign for a product at {product.base_url}.
    Audience: {config.get('audience', 'Business Owners')}
    Goal: {config.get('goal', 'Product awareness')}
    
    Product Modules discovered:
    {json.dumps([m.name for m in modules])}
    
    Generate 10 LinkedIn posts. Each post must have a Hook, Body, Value Proposition, CTA, and Hashtags.
    Generate exactly 10 posts in a JSON array.
    """
    
    client = genai.Client(api_key=api_key)
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
            ),
        )
        data = json.loads(response.text)
        # Store in DB (mocking DB structure for now since models aren't fully defined yet)
        print("Generated AI content successfully.")
    except Exception as e:
        print(f"Content AI Error: {e}")
        mock_generate_content(product_id, config, db)

def mock_generate_content(product_id: str, config: dict, db: Session):
    time.sleep(3) # Simulate AI thinking
    print(f"Mock generated content for product {product_id} with config {config}")
    # In a real implementation we would save to the DB here
