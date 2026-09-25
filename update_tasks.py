import re

with open("backend/workers/tasks.py", "r") as f:
    content = f.read()

# Fix crawler_service -> crawler
content = content.replace("from services import crawler_service", "import crawler")

# Fix crawler.run_crawler signature
new_crawl_body = """
    import crawler
    db = SessionLocal()
    try:
        _update_job(db, job_id,
                    status="running",
                    started_at=datetime.now(timezone.utc),
                    celery_task_id=self.request.id)
        db.commit()
        
        product = db.query(models.Product).filter(models.Product.id == product_id).first()
        if product:
            crawler.run_crawler(job_id=crawl_job_id, start_url=product.base_url)
            
            # The crawler doesn't return anything or natively update the AsyncJob progress.
            # We'll just mark it 100% when done.
            _update_job(db, job_id,
                        status="succeeded",
                        progress=100,
                        completed_at=datetime.now(timezone.utc))
            db.commit()
        else:
            raise ValueError("Product not found")
            
    except Exception as exc:
"""

# Find the try block of crawl_product and replace it
content = re.sub(
    r"    from services import crawler_service.*?except Exception as exc:",
    new_crawl_body.strip("\n"),
    content,
    flags=re.DOTALL
)

# Also fix the other services imports
content = content.replace("from services import ai_service", "import ai_service")
content = content.replace("from services import media_service", "import media_service")
content = content.replace("from services import campaign_service", "import campaign_service")
content = content.replace("from services import content_service", "import content_service")
content = content.replace("from services import linkedin_service", "import linkedin_service")
content = content.replace("from services import export_service", "import export_service")

with open("backend/workers/tasks.py", "w") as f:
    f.write(content)
print("tasks.py updated!")
