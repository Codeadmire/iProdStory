import sys
from playwright.sync_api import sync_playwright

def test_crawl():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--disable-dev-shm-usage", "--no-sandbox"])
        context = browser.new_context(ignore_https_errors=True)
        page = context.new_page()
        try:
            print("Navigating...")
            response = page.goto("https://magenta-wolf-691543.hostingersite.com/", wait_until="domcontentloaded", timeout=10000)
            print("Response:", response.status if response else None)
            
            print("Getting title...")
            print("Title:", page.title())
            
            print("Getting inner_text...")
            text = page.locator("body").inner_text(timeout=5000)
            print("Text length:", len(text))
        except Exception as e:
            print("Error:", e)
        finally:
            page.close()
            browser.close()

if __name__ == "__main__":
    test_crawl()
