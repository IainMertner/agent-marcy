import requests
from typing import List, Dict
import json

API_ENDPOINT = "https://api.byrotation.com/trpc/listing.list"
BASE_DOMAIN = "https://byrotation.com"
PAGE_SIZE = 20  # items per page

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                  "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/26.1 Safari/605.1.15",
    "Accept": "*/*",
    "Content-Type": "application/json",
    "Origin": BASE_DOMAIN,
    "Referer": BASE_DOMAIN
}

def extract_hits(data):
    """Extract hits from API response."""
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

def get_item_urls(query: str) -> List[Dict]:
    """Fetch a single page of ByRotation products matching query."""
    input_param = {
        "0": {
            "json": {
                "first": PAGE_SIZE,
                "skip": 0,
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
    hits = extract_hits(resp.json())

    products = []
    for hit in hits:
        if hit.get("status") != "ACTIVE":
            continue
        products.append({
            "url": f"{BASE_DOMAIN}/products/{hit.get('slug')}"
        })
    return products