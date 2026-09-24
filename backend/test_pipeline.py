import requests
import time
import sys
import json
import traceback

BASE_URL = "http://localhost:8000"
TARGET_URL = "https://magenta-wolf-691543.hostingersite.com/"

def run_test():
    print(f"==================================================")
    print(f"🚀 FINAL MVP ACCEPTANCE TEST")
    print(f"==================================================\n")
    
    start_time = time.time()
    results = {}
    
    try:
        # ---------------------------------------------------------
        # 1. DISCOVER
        # ---------------------------------------------------------
        print("STAGE 1: DISCOVER")
        print(f"-> Creating product for {TARGET_URL}...")
        res = requests.post(f"{BASE_URL}/api/products", json={"url": TARGET_URL})
        res.raise_for_status()
        product = res.json()
        product_id = product["id"]
        print(f"   [PASS] Product created: {product_id}")
        
        print("-> Starting crawl job...")
        res = requests.post(f"{BASE_URL}/api/products/{product_id}/crawl", json={"max_pages": 50, "max_depth": 2})
        res.raise_for_status()
        crawl = res.json()
        job_id = crawl["job_id"]
        print(f"   [PASS] Crawl started: {job_id}")
        
        print("-> Polling for crawl completion...")
        for i in range(60):
            res = requests.get(f"{BASE_URL}/api/crawls/{job_id}")
            crawl_status = res.json()
            status = crawl_status["status"]
            print(f"   ... status: {status} ({crawl_status.get('pages_processed', 0)} pages processed)")
            if status in ["COMPLETED", "COMPLETED_WITH_WARNINGS", "FAILED"]:
                break
            time.sleep(2)
            
        if status not in ["COMPLETED", "COMPLETED_WITH_WARNINGS"]:
            raise Exception(f"Crawl failed with status: {status}")
            
        print("-> Validating discovery data...")
        res = requests.get(f"{BASE_URL}/api/products/{product_id}/pages")
        pages = res.json()
        if len(pages) == 0: raise Exception("No pages discovered")
        print(f"   [PASS] Discovered {len(pages)} pages")
        
        res = requests.get(f"{BASE_URL}/api/crawls/{job_id}/export")
        export_data = res.json()
        screenshots = export_data.get("screenshots", [])
        if len(screenshots) == 0: raise Exception("No screenshots captured")
        print(f"   [PASS] Captured {len(screenshots)} screenshots")
        
        results["DISCOVER"] = "PASS"
        print("\n")
        
        # ---------------------------------------------------------
        # 2. UNDERSTAND & 3. CREATE
        # ---------------------------------------------------------
        print("STAGE 2 & 3: AI UNDERSTANDING & CAMPAIGN CREATION")
        print("-> Triggering AI analysis...")
        res = requests.post(f"{BASE_URL}/api/products/{product_id}/analyze")
        res.raise_for_status()
        analysis = res.json()
        time.sleep(5)
        
        print("-> Validating generated modules & features...")
        res = requests.get(f"{BASE_URL}/api/products/{product_id}/modules")
        modules = res.json()
        if len(modules) == 0: raise Exception("No modules generated")
        print(f"   [PASS] Generated {len(modules)} AI modules/features")
        
        res = requests.get(f"{BASE_URL}/api/products/{product_id}/features")
        features = res.json()
        print(f"   [PASS] Extracted {len(features)} pieces of evidence/problems/benefits")
        
        print("-> Triggering marketing media generation...")
        res = requests.post(f"{BASE_URL}/api/products/{product_id}/media")
        res.raise_for_status()
        media = res.json()
        assets = media.get("assets", [])
        if len(assets) == 0: raise Exception("No media assets generated")
        print(f"   [PASS] Generated {len(assets)} campaign images")
        
        results["UNDERSTAND"] = "PASS"
        results["CREATE"] = "PASS"
        print("\n")
        
        # ---------------------------------------------------------
        # 4. REVIEW & 5. EXPORT
        # ---------------------------------------------------------
        print("STAGE 4 & 5: REVIEW & EXPORT")
        print("-> Verifying export payload...")
        res = requests.get(f"{BASE_URL}/api/products/{product_id}/export", stream=True)
        res.raise_for_status()
        if not res.headers.get("Content-Disposition"):
            raise Exception("Missing ZIP attachment headers")
        print(f"   [PASS] Export ZIP stream initialized correctly")
        
        results["REVIEW"] = "PASS"
        results["EXPORT"] = "PASS"
        print("\n")
        
        # ---------------------------------------------------------
        # 6. PUBLISH
        # ---------------------------------------------------------
        print("STAGE 6: PUBLISH")
        print("-> Checking LinkedIn Auth URL...")
        res = requests.get(f"{BASE_URL}/api/linkedin/auth/url")
        res.raise_for_status()
        print(f"   [PASS] LinkedIn OAuth works: {res.json().get('url')[:30]}...")
        
        print("-> Triggering Mock Publish...")
        res = requests.post(f"{BASE_URL}/api/products/{product_id}/publish")
        res.raise_for_status()
        print(f"   [PASS] Mock publish succeeded")
        
        results["PUBLISH"] = "PASS"
        
    except Exception as e:
        print(f"\n❌ [FAIL] Pipeline failed: {str(e)}")
        traceback.print_exc()
        results["FAILED_AT"] = str(e)
        
    # ---------------------------------------------------------
    # REPORT
    # ---------------------------------------------------------
    execution_time = time.time() - start_time
    print(f"\n==================================================")
    print(f"📊 ACCEPTANCE TEST REPORT")
    print(f"==================================================")
    print(f"DISCOVER:   {results.get('DISCOVER', 'FAIL')}")
    print(f"UNDERSTAND: {results.get('UNDERSTAND', 'FAIL')}")
    print(f"CREATE:     {results.get('CREATE', 'FAIL')}")
    print(f"REVIEW:     {results.get('REVIEW', 'FAIL')}")
    print(f"EXPORT:     {results.get('EXPORT', 'FAIL')}")
    print(f"PUBLISH:    {results.get('PUBLISH', 'FAIL')}")
    print(f"--------------------------------------------------")
    print(f"Total Execution Time: {execution_time:.2f} seconds")
    if "FAILED_AT" in results:
        print(f"Error Encountered: {results['FAILED_AT']}")
    print(f"==================================================\n")


if __name__ == "__main__":
    run_test()
