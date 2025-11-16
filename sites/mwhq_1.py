import requests
from typing import List

BASE_DOMAIN = "https://www.mywardrobehq.com"
API_ENDPOINT = f"{BASE_DOMAIN}/get-products"
MW_SESSION_COOKIE = "mwhqsession=9s4huvja3jes9pj02dn4iik1c8847oaj"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                  "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/26.1 Safari/605.1.15",
    "Accept": "/",
    "X-Requested-With": "XMLHttpRequest",
    "Cookie": f"mwhqsession={MW_SESSION_COOKIE};"
}

PAGE_SIZE = 5  # API returns 5 products per page

def fetch_products_page(query: str, page: int) -> List[dict]:
    params = {
        "featured": "1",
        "selected_page": "search",
        "sort": "date_desc",
        "q": query,
        "type": "json",
        "page": page
    }
    resp = requests.get(API_ENDPOINT, headers=HEADERS, params=params, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    return data if isinstance(data, list) else []

def build_product_url(product: dict) -> str:
    brand_slug = product.get("brandName", "").lower().replace(" ", "-")
    product_slug = product.get("slug", "").lower().replace(" ", "-")
    product_id = product.get("id")
    return f"{BASE_DOMAIN}/{brand_slug}/{product_slug}/P{product_id}"

def get_item_urls(query: str, max_per_site: int) -> List[str]:
    urls = []
    pages_needed = -(-max_per_site // PAGE_SIZE)  # ceiling division

    for page in range(pages_needed):
        products = fetch_products_page(query, page)
        if not products:
            break
        for product in products:
            if product.get("overallStatus", "").upper() == "SOLD":
                continue
            urls.append(build_product_url(product))
            if len(urls) >= max_per_site:
                break
        if len(urls) >= max_per_site:
            break

    return urls