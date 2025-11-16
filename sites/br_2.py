import requests
from bs4 import BeautifulSoup
from typing import List, Dict
import json
import time
import re

API_ENDPOINT = "https://api.byrotation.com/trpc/listing.list"
BASE_DOMAIN = "https://byrotation.com"
PAGE_SIZE = 36

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                  "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/26.1 Safari/605.1.15",
    "Accept": "*/*",
    "Content-Type": "application/json",
    "Origin": BASE_DOMAIN,
    "Referer": BASE_DOMAIN
}

def extract_hits(data):
    """Extract hits from ByRotation API whether data is list or dict."""
    if isinstance(data, list) and len(data) > 0:
        item = data[0]
        return (
            item.get("result", {})
                .get("data", {})
                .get("json", {})
                .get("hits", [])
        )
    return (
        data.get("result", {})
            .get("data", {})
            .get("json", {})
            .get("hits", [])
    )

def fetch_products(query: str, skip: int = 0) -> List[Dict]:
    """Fetch a page of products from ByRotation API."""
    input_param = {
        "0": {
            "json": {
                "first": PAGE_SIZE,
                "skip": skip,
                "query": query,
                "filters": {}
            }
        }
    }
    params = {
        "batch": 1,
        "input": json.dumps(input_param)
    }
    resp = requests.get(API_ENDPOINT, headers=HEADERS, params=params, timeout=20)
    resp.raise_for_status()
    data = resp.json()
    hits = extract_hits(data)
    return hits

def get_details(url: str) -> Dict:
    """Scrape all details from a ByRotation product page."""
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        
        html = response.text
        soup = BeautifulSoup(html, 'html.parser')
        
        # Get all text content
        page_text = soup.get_text()
        
        # Extract title - look for the dress name pattern
        title = None
        title_match = re.search(r'REISS\s+([A-Z\s,]+?)(?:The|brand)', page_text)
        if title_match:
            title = title_match.group(1).strip().rstrip(',')
        
        # Extract brand - just the brand name
        brand = None
        brand_match = re.search(r'brand(Reiss)', page_text, re.IGNORECASE)
        if brand_match:
            brand = brand_match.group(1)
        else:
            # Try from the dress name
            if 'REISS' in page_text:
                brand = "Reiss"
        
        # Extract size
        size = None
        size_match = re.search(r'sizeUK\s+(\d+)', page_text)
        if size_match:
            size = f"UK {size_match.group(1)}"
        
        # Extract location
        location = None
        location_match = re.search(r'location([^c]+?)colour', page_text)
        if location_match:
            location = location_match.group(1).strip()
        
        # Extract color
        color = None
        color_match = re.search(r'colourRed', page_text) or re.search(r'colour([A-Za-z]+)', page_text)
        if color_match:
            if 'Red' in color_match.group(0):
                color = "Red"
            else:
                color = color_match.group(1)
        
        # Extract retail price (RRP)
        retail_price = None
        rrp_match = re.search(r'RRP\s*£(\d+)', page_text)
        if rrp_match:
            retail_price = int(rrp_match.group(1))
        
        # Extract rental prices
        rental_3days = None
        rental_7days = None
        rental_28days = None
        
        # 3+ days price
        match_3 = re.search(r'3\+\s*days£([\d.]+)/day', page_text)
        if match_3:
            rental_3days = float(match_3.group(1))
        
        # 7+ days price
        match_7 = re.search(r'7\+\s*days£([\d.]+)/day', page_text)
        if match_7:
            rental_7days = float(match_7.group(1))
        
        # 28+ days price
        match_28 = re.search(r'28\+\s*days£([\d.]+)/day', page_text)
        if match_28:
            rental_28days = float(match_28.group(1))
        
        # Extract description
        description = None
        desc_match = re.search(r'DARK RED(.*?)brand', page_text, re.DOTALL)
        if desc_match:
            description = desc_match.group(1).strip()
        
        # Extract owner username
        owner = None
        owner_match = re.search(r'UK\s+\d+([a-z]+)Aberdeen', page_text)
        if owner_match:
            owner = owner_match.group(1)
        
        # Extract images from img tags (even if they're lazy loaded)
        images = []
        
        # Method 1: Look for img tags with src or data-src
        img_tags = soup.find_all('img')
        for img in img_tags:
            src = img.get('src') or img.get('data-src') or img.get('data-lazy-src')
            if src and src not in images:
                # Filter out icons, logos, etc
                if any(word in src.lower() for word in ['product', 'item', 'listing', 'upload', 'cloudinary']):
                    if src.startswith('//'):
                        src = 'https:' + src
                    elif src.startswith('/'):
                        src = BASE_DOMAIN + src
                    images.append(src)
        
        # Method 2: Look for Next.js image data in script tags
        scripts = soup.find_all('script')
        for script in scripts:
            if script.string and 'image' in script.string.lower():
                # Look for image URLs in JSON
                img_urls = re.findall(r'https?://[^"\'>\s]+\.(?:jpg|jpeg|png|webp)', script.string)
                for img_url in img_urls:
                    if img_url not in images and 'product' in img_url.lower():
                        images.append(img_url)
        
        # Method 3: Look in meta tags
        og_image = soup.find('meta', property='og:image')
        if og_image:
            img_url = og_image.get('content')
            if img_url and img_url not in images:
                images.append(img_url)
        
        return {
            "platform": "ByRotation",
            "url": url,
            "title": title or "N/A",
            "brand": brand or "N/A",
            "description": description or "",
            "size": size,
            "color": color,
            "location": location,
            "owner": owner,
            "retail_price": retail_price,
            "rental_3days": rental_3days,
            "rental_7days": rental_7days,
            "rental_28days": rental_28days,
            "images": images
        }
    
    except Exception as e:
        print(f"  ✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return {}
    