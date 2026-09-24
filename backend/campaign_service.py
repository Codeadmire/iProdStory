import os
import json
from sqlalchemy.orm import Session
import models
from google import genai
from google.genai import types
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

def generate_campaign(product_id: str, db: Session, model_name: str = "gemini-1.5-flash-latest"):
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product:
        return None
        
    modules = db.query(models.Module).filter(models.Module.product_id == product_id).all()
    
    module_summaries = []
    for m in modules:
        features = db.query(models.Feature).filter(models.Feature.module_id == m.id).all()
        module_summaries.append(f"- {m.name}: {m.description} ({', '.join([f.name for f in features])})")
        
    context = "\n".join(module_summaries)

    if GEMINI_API_KEY:
        try:
            client = genai.Client(api_key=GEMINI_API_KEY)
            prompt = f"""
            You are an expert LinkedIn copywriter for B2B SaaS products.
            We are launching a new product at {product.base_url}.
            
            Here are its core modules and features:
            {context}
            
            Write a complete marketing campaign. Return ONLY a JSON object with this exact structure:
            {{
                "headline": "A short, punchy 1-line headline (e.g. The modern connected system for inventory).",
                "about": "A 2-3 sentence description of the product.",
                "posts": [
                    "Post 1: Launch post introducing the platform. Use emojis and spaced out lines.",
                    "Post 2: Feature deep dive on {modules[0].name if modules else 'a feature'}.",
                    "Post 3: Feature deep dive on {modules[1].name if len(modules) > 1 else 'another feature'}."
                ]
            }}
            Generate exactly 3 posts.
            """
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                ),
            )
            text = response.text
            data = json.loads(text)
        except Exception as e:
            print(f"Error generating campaign: {e}")
            data = get_mock_campaign(product)
    else:
        print("No GEMINI_API_KEY found, using mock campaign data.")
        data = get_mock_campaign(product)
        
    # Save to DB
    # Clean up old
    old_campaign = db.query(models.Campaign).filter(models.Campaign.product_id == product_id).first()
    if old_campaign:
        db.query(models.CampaignPost).filter(models.CampaignPost.campaign_id == old_campaign.id).delete()
        db.delete(old_campaign)
        db.commit()
        
    new_campaign = models.Campaign(
        product_id=product_id,
        headline=data.get("headline", ""),
        about=data.get("about", "")
    )
    db.add(new_campaign)
    db.commit()
    db.refresh(new_campaign)
    
    for p_content in data.get("posts", []):
        db_post = models.CampaignPost(
            campaign_id=new_campaign.id,
            content=p_content
        )
        db.add(db_post)
        
    db.commit()
    return get_campaign_dict(new_campaign, db)

def get_mock_campaign(product):
    return {
        "headline": "The Ultimate Business Management Platform",
        "about": "A complete business management platform that brings inventory, purchasing, sales, delivery, and financial operations into one connected system. Scale your operations without adding complexity.",
        "posts": [
            "Struggling to keep track of stock across multiple warehouses? 📦\n\nWe just mapped out exactly how modern enterprises are solving this.\n\nIntroducing our new platform — the connected system for inventory, sales, and purchasing.",
            "Are you tired of manually syncing your sales and inventory data? 🤦‍♂️\n\nCheck out the new automated workflows we just released! From Purchase Order to Final Delivery, everything is connected in real-time. ⚡",
            "Data silos are killing your growth. 📉\n\nWhen your purchasing team doesn't talk to your sales team, you end up with stockouts or dead inventory.\n\nHere is how we fixed the B2B supply chain operations loop 👇"
        ]
    }

def get_campaign_dict(campaign, db):
    posts = db.query(models.CampaignPost).filter(models.CampaignPost.campaign_id == campaign.id).all()
    return {
        "id": campaign.id,
        "headline": campaign.headline,
        "about": campaign.about,
        "posts": [{"id": p.id, "topic": p.topic, "hook": p.hook, "body": p.body, "cta": p.cta, "hashtags": p.hashtags, "status": p.status} for p in posts]
    }

def generate_linkedin_posts(product_id: str, db: Session, model_name: str, settings: dict):
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product: return None
        
    modules = db.query(models.Module).filter(models.Module.product_id == product_id).all()
    context = "\n".join([f"- {m.name}: {m.description}" for m in modules])
    
    num_posts = settings.get("num_posts", 3)
    tone = settings.get("tone", "Professional B2B")
    audience = settings.get("audience", "Business Owners")
    content_types = settings.get("content_types", ["Product launch", "Feature", "Educational"])
    
    if GEMINI_API_KEY:
        try:
            client = genai.Client(api_key=GEMINI_API_KEY)
            prompt = f"""
            You are an expert LinkedIn copywriter.
            Product: {product.base_url}
            Features: {context}
            
            Audience: {audience}
            Tone: {tone}
            
            Write {num_posts} LinkedIn posts based on these themes: {', '.join(content_types)}.
            Return ONLY a JSON array of objects:
            [{{
                "topic": "E.g. Product launch",
                "hook": "The opening line to grab attention",
                "body": "The main content (use emojis and spacing)",
                "cta": "The call to action",
                "hashtags": "#hashtag1 #hashtag2"
            }}]
            """
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=types.GenerateContentConfig(response_mime_type="application/json")
            )
            posts_data = json.loads(response.text)
        except Exception as e:
            print("Error generating posts", e)
            posts_data = [{"topic": "Launch", "hook": "Check out our new product!", "body": "It's great.", "cta": "Try it today.", "hashtags": "#launch"}]
    else:
        posts_data = [{"topic": "Launch", "hook": "Check out our new product!", "body": "It's great.", "cta": "Try it today.", "hashtags": "#launch"}]
        
    campaign = db.query(models.Campaign).filter(models.Campaign.product_id == product_id).first()
    if not campaign:
        campaign = models.Campaign(product_id=product_id, headline="", about="")
        db.add(campaign)
        db.commit()
        db.refresh(campaign)
        
    # We will just append these posts to the campaign for now, or replace them.
    # The prompt says "Store these separately" but "Campaign structure: Campaign > Posts".
    # We'll just add them to the campaign.
    created_posts = []
    for p in posts_data:
        db_post = models.CampaignPost(
            campaign_id=campaign.id,
            topic=p.get("topic", ""),
            hook=p.get("hook", ""),
            body=p.get("body", ""),
            cta=p.get("cta", ""),
            hashtags=p.get("hashtags", ""),
            status="Draft"
        )
        db.add(db_post)
        created_posts.append(db_post)
    db.commit()
    
    return [
        {"id": p.id, "topic": p.topic, "hook": p.hook, "body": p.body, "cta": p.cta, "hashtags": p.hashtags, "status": p.status}
        for p in created_posts
    ]

def generate_linkedin_product_page(product_id: str, db: Session, model_name: str = "gemini-1.5-flash-latest"):
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product:
        return None
        
    modules = db.query(models.Module).filter(models.Module.product_id == product_id).all()
    
    module_summaries = []
    for m in modules:
        features = db.query(models.Feature).filter(models.Feature.module_id == m.id).all()
        module_summaries.append(f"- {m.name}: {m.description} ({', '.join([f.name for f in features])})")
        
    context = "\n".join(module_summaries)
    
    if GEMINI_API_KEY:
        try:
            client = genai.Client(api_key=GEMINI_API_KEY)
            prompt = f"""
            You are an expert LinkedIn copywriter for B2B SaaS products.
            We are launching a new product at {product.base_url}.
            
            Here are its core modules and features:
            {context}
            
            Write a complete LinkedIn Product Page. Return ONLY a JSON object with this exact structure:
            {{
                "name": "Product name (e.g. StockFlow)",
                "tagline": "A short, punchy tagline.",
                "description": "A 2-3 sentence description.",
                "target_audience": "Who this is for (e.g. Inventory Managers, Retailers)",
                "highlights": "Key highlights and benefits separated by bullets."
            }}
            Do not invent product functionality, testimonials, statistics, or integrations. Use only the provided context.
            """
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                ),
            )
            text = response.text
            data = json.loads(text)
        except Exception as e:
            print(f"Error generating product page: {e}")
            data = {
                "name": "StockFlow",
                "tagline": "Modern inventory management.",
                "description": "Manage your stock with ease.",
                "target_audience": "Business Owners",
                "highlights": "• Real-time stock\n• Easy ordering"
            }
    else:
        data = {
            "name": "StockFlow",
            "tagline": "Modern inventory management.",
            "description": "Manage your stock with ease.",
            "target_audience": "Business Owners",
            "highlights": "• Real-time stock\n• Easy ordering"
        }
        
    # Clean up old
    old_page = db.query(models.LinkedInProductPage).filter(models.LinkedInProductPage.product_id == product_id).first()
    if old_page:
        db.delete(old_page)
        db.commit()
        
    new_page = models.LinkedInProductPage(
        product_id=product_id,
        name=data.get("name", "Product Name"),
        tagline=data.get("tagline", ""),
        description=data.get("description", ""),
        website=product.base_url,
        target_audience=data.get("target_audience", ""),
        highlights=data.get("highlights", ""),
        status="Draft"
    )
    db.add(new_page)
    db.commit()
    db.refresh(new_page)
    
    return {
        "id": new_page.id,
        "product_id": new_page.product_id,
        "name": new_page.name,
        "tagline": new_page.tagline,
        "description": new_page.description,
        "website": new_page.website,
        "target_audience": new_page.target_audience,
        "highlights": new_page.highlights,
        "status": new_page.status
    }
