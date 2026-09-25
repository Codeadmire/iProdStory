from sqlalchemy.orm import Session
from playwright.sync_api import sync_playwright
import os
import json
from urllib.parse import urlparse
from collections import deque
import models
from database import SessionLocal

def normalize_url(url: str) -> str:
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}{parsed.path}".rstrip("/")

def is_same_domain(base_url: str, target_url: str) -> bool:
    base_netloc = urlparse(base_url).netloc
    target_netloc = urlparse(target_url).netloc
    return base_netloc == target_netloc

def run_crawler(job_id: str, start_url: str):
    db: Session = SessionLocal()
    job = db.query(models.CrawlJob).filter(models.CrawlJob.id == job_id).first()
    if not job:
        db.close()
        return
    
    visited = set()
    queue = deque([(start_url, 0, None)]) # (url, depth, parent_url)
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, args=["--disable-dev-shm-usage", "--no-sandbox"])
            context = browser.new_context(
                ignore_https_errors=True,
                viewport={"width": 1280, "height": 800}
            )
            os.makedirs("screenshots", exist_ok=True)
            
            while queue and job.pages_processed < job.max_pages:
                current_url, depth, parent_url = queue.popleft()
                norm_url = normalize_url(current_url)
                
                if norm_url in visited:
                    continue
                visited.add(norm_url)
                
                if depth > job.max_depth:
                    continue
                
                job.current_url = current_url
                db.commit()
                
                print(f"Crawling: {current_url} at depth {depth}")
                
                page = context.new_page()
                try:
                    response = page.goto(current_url, wait_until="domcontentloaded", timeout=job.timeout)
                    
                    if not response or response.status >= 400:
                        job.failed_pages += 1
                        job.pages_processed += 1
                        
                        # Save failed page
                        crawled_page = models.CrawledPage(
                            product_id=job.product_id,
                            url=norm_url,
                            parent_url=parent_url,
                            status=response.status if response else 500,
                            depth=depth,
                            error_message="HTTP Error"
                        )
                        db.add(crawled_page)
                        db.commit()
                        continue
                    
                    title = page.title()
                    visible_text = page.locator("body").inner_text()
                    
                    # Extract page evidence
                    meta_desc = page.evaluate("() => { const meta = document.querySelector('meta[name=\"description\"]'); return meta ? meta.content : null; }")
                    h1s = page.locator("h1").all_inner_texts()
                    h2s = page.locator("h2").all_inner_texts()
                    nav_labels = page.locator("nav a").all_inner_texts()
                    buttons = page.locator("button, a.button").all_inner_texts()
                    
                    screenshot_path = f"screenshots/{job_id}_{job.pages_processed}.png"
                    page.screenshot(path=screenshot_path)
                    
                    # Save Page
                    crawled_page = models.CrawledPage(
                        product_id=job.product_id,
                        url=norm_url,
                        parent_url=parent_url,
                        title=title,
                        meta_description=meta_desc,
                        h1=json.dumps(h1s),
                        h2=json.dumps(h2s),
                        nav_labels=json.dumps(nav_labels),
                        button_texts=json.dumps(buttons),
                        visible_text=visible_text[:2000],
                        status=response.status,
                        depth=depth
                    )
                    db.add(crawled_page)
                    db.commit()
                    db.refresh(crawled_page)
                    
                    # Save Screenshot
                    screenshot = models.PageScreenshot(
                        product_id=job.product_id,
                        page_id=crawled_page.id,
                        image_path=screenshot_path,
                        viewport_width=1280,
                        viewport_height=800
                    )
                    db.add(screenshot)
                    
                    # Basic extraction
                    headings = page.locator("h1, h2").all_inner_texts()
                    for heading in headings[:3]:
                        if heading.strip():
                            feature = models.Feature(
                                product_id=job.product_id,
                                name=heading.strip(),
                                confidence="candidate"
                            )
                            db.add(feature)
                            db.commit()
                            db.refresh(feature)
                            
                            evidence = models.FeatureEvidence(
                                feature_id=feature.id,
                                page_id=crawled_page.id,
                                evidence_text=heading.strip(),
                                source="Heading"
                            )
                            db.add(evidence)
                            job.features_detected += 1
                    
                    job.pages_discovered += 1
                    job.screenshots_captured += 1
                    job.pages_processed += 1
                    db.commit()
                    
                    # Find links for next depth
                    if depth < job.max_depth:
                        hrefs = page.evaluate("() => Array.from(document.links).map(link => link.href)")
                        for href in hrefs:
                            if href and href.startswith("http") and is_same_domain(start_url, href):
                                queue.append((href, depth + 1, norm_url))
                                
                except Exception as inner_e:
                    print(f"Error crawling {current_url}: {inner_e}")
                    job.failed_pages += 1
                    job.pages_processed += 1
                    crawled_page = models.CrawledPage(
                        product_id=job.product_id,
                        url=norm_url,
                        parent_url=parent_url,
                        depth=depth,
                        error_message=str(inner_e)
                    )
                    db.add(crawled_page)
                    db.commit()
                finally:
                    try:
                        page.close()
                    except Exception:
                        pass
                    
            if job.failed_pages > 0:
                job.status = "COMPLETED_WITH_WARNINGS"
            else:
                job.status = "COMPLETED"
                
            job.current_url = None
            db.commit()
            browser.close()
            
    except Exception as e:
        job.status = "FAILED"
        job.error_message = str(e)
        db.commit()
        print(f"Crawl job failed: {e}")
    finally:
        db.close()
