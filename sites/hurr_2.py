import requests
import json
from urllib.parse import urlparse

# ---------------------------
# CONFIG
# ---------------------------
BEARER_TOKEN = "search-kms28ixa6p378p4d4fvm53r3"
HEADERS = {
    "Authorization": f"Bearer {BEARER_TOKEN}",
    "Content-Type": "application/json",
    "Accept": "*/*",
}

API_URL = "https://hurr-eu.ent.eu-west-2.aws.cloud.es.io/api/as/v1/engines/search-production-hurr-listings-v4/multi_search.json"

# ---------------------------
# FUNCTIONS
# ---------------------------
def extract_slug_from_url(url: str) -> str:
    """Extract slug from full HURR listing URL."""
    path = urlparse(url).path  # e.g., /listings/cecelia-dress-8860
    parts = path.strip("/").split("/")
    if len(parts) >= 2 and parts[0] == "listings":
        return parts[1]
    return ""

def generate_rental_periods(daily_rate: float):
    """Generate rental periods with total price, price per day, and discount."""
    periods = [4, 8, 16, 30]
    rental_data = []

    for days in periods:
        if days == 4:
            total = daily_rate * 4
            discount = None
        elif days == 8:
            total = daily_rate * 8 * 0.64  # 36% off
            discount = 36
        elif days == 16:
            total = daily_rate * 16 * 0.55  # 45% off
            discount = 45
        elif days == 30:
            total = daily_rate * 30 * 0.36  # 64% off
            discount = 64

        rental_data.append({
            "period_days": days,
            "total_price": round(total, 2),
            "price_per_day": round(total / days, 2),
            "discount_percent": discount
        })
    return rental_data

def get_details(url: str) -> dict:
    """Fetch a HURR listing from a full URL and return detailed info."""
    slug = extract_slug_from_url(url)
    if not slug:
        print("✗ Could not extract slug from URL")
        return {}

    payload = {
        "queries": [
            {
                "query": slug,
                "page": {"current": 1, "size": 1}
            }
        ]
    }

    r = requests.post(API_URL, headers=HEADERS, json=payload, timeout=15)
    if r.status_code != 200:
        print("✗ API request failed")
        return {}

    data = r.json()
    results = data[0].get("results", [])
    if not results:
        print("✗ No listing found in API")
        return {}

    item = results[0]

    # Extract fields
    slug_value = item.get("slug", {}).get("raw", "")
    title = item.get("item_name", {}).get("raw")
    brand = item.get("designer_brand", {}).get("raw")
    description = item.get("details_style_notes", {}).get("raw")
    sizes = item.get("available_sizes", {}).get("raw")

    images = []
    if item.get("cl_image_url", {}).get("raw"):
        images.append(item.get("cl_image_url", {}).get("raw"))
    if item.get("second_image_url", {}).get("raw"):
        images.append(item.get("second_image_url", {}).get("raw"))

    daily_rate = item.get("listing_view_price", {}).get("raw")
    rental_periods = generate_rental_periods(daily_rate) if daily_rate else None
    retail_price = item.get("rrp", {}).get("raw")

    product = {
        "url": f"https://www.hurrcollective.com/listings/{slug_value}",
        "title": title,
        "brand": brand,
        "description": description,
        "sizes": sizes,
        "images": images,
        "rental_periods": rental_periods,
        "retail_price": retail_price
    }

    return product