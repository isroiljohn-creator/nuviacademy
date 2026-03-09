import os
import urllib.request
import json

# Minimal config
API_KEY = os.getenv("YMOVE_API_KEY", "ym_110890fa1e4682f3fc743da17b3153ff84c9b05fe8f17a2524b68c1a864339a3")
BASE_URL = "https://exercise-api.ymove.app/api/v1"

def fetch_debug():
    all_data = []
    page = 1
    
    print("DEBUG: Starting fetch...")
    try:
        while True:
            print(f"DEBUG: Fetching page {page}...")
            url = f"{BASE_URL}/exercises?limit=100&page={page}&hasVideo=true"
            req = urllib.request.Request(url)
            req.add_header("X-API-Key", API_KEY)
            
            try:
                with urllib.request.urlopen(req, timeout=10) as response:
                    print(f"DEBUG: Page {page} status: {response.status}")
                    if response.status != 200:
                        break
                    
                    data = json.loads(response.read().decode())
                    items = data.get('data', [])
                    print(f"DEBUG: Page {page} items: {len(items)}")
                    
                    if not items:
                        print("DEBUG: No items, stopping.")
                        break
                        
                    all_data.extend(items)
                    
                    pagination = data.get('pagination', {})
                    total_pages = pagination.get('totalPages', 1)
                    print(f"DEBUG: Pagination: {pagination}")
                    
                    if page >= total_pages:
                        print("DEBUG: Reached last page.")
                        break
                        
                    page += 1
            except Exception as http_err:
                 print(f"DEBUG: HTTP Error on page {page}: {http_err}")
                 break
                
        print(f"DEBUG: Total items fetched: {len(all_data)}")
        return all_data
    except Exception as e:
        print(f"Generic Error: {e}")
        return []

if __name__ == "__main__":
    fetch_debug()
