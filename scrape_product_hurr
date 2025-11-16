import requests
import json
import re
import traceback
from typing import Dict, Any

def scrape_single_hurr(url: str) -> Dict[str, Any]:
    """
    Scrape a single HURR listing using the Elastic App Search API.
    Uses only the valid field names that don't trigger errors.
    """
    print("=" * 60)
    print(f"Scraping: {url}")
    print("=" * 60)

    # --- 1. Extract slug ---
    match = re.search(r'/listings/([^/?#]+)', url)
    if not match:
        print("Could not extract slug from URL")
        return {}
    slug = match.group(1)

    # --- 2. API config ---
    api_url = "https://hurr-eu.ent.eu-west-2.aws.cloud.es.io/api/as/v1/engines/search-production-hurr-listings-v4/multi_search.json"
    headers = {
        "Authorization": "Bearer search-kms28ixa6p378p4d4fvm53r3",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15",
        "Origin": "https://www.hurrcollective.com",
        "Referer": "https://www.hurrcollective.com/",
        "x-elastic-client-meta": "ent=8.9.0-legacy,js=browser,t=8.9.0-legacy,ft=universal",
        "x-swiftype-client": "elastic-app-search-javascript",
        "x-swiftype-client-version": "8.9.0"
    }

    # --- 3. Payload – with ONLY valid result_fields (removed invalid ones) ---
    payload = {
        "queries": [
            {
                "query": "",
                "page": {"size": 1},
                "result_fields": {
                    "id": {"raw": {}},
                    "public_uid": {"raw": {}},
                    "slug": {"raw": {}},
                    "item_name": {"raw": {}},
                    "designer_brand": {"raw": {}},
                    "cl_image_url": {"raw": {}},
                    "second_image_url": {"raw": {}},
                    "listing_view_price": {"raw": {}},
                    "lowest_unit_purchase_price": {"raw": {}},
                    "rrp": {"raw": {}},
                    "unit_sizes_available": {"raw": {}},
                    "available_sizes": {"raw": {}},
                    "lender_name": {"raw": {}},
                    "colour_category": {"raw": {}},
                    "tag_list": {"raw": {}},
                    "exclusive": {"raw": {}},
                    "top_lender?": {"raw": {}},
                    "managed_item?": {"raw": {}},
                    "brand_name": {"raw": {}}
                },
                "filters": {
                    "all": [
                        {"slug": slug}
                    ]
                }
            }
        ]
    }

    try:
        resp = requests.post(api_url, json=payload, headers=headers, timeout=12)
        if resp.status_code != 200:
            print(f"{resp.status_code} Error – {resp.text[:300]}")
            return {}
        data = resp.json()

        if not data or not data[0].get("results"):
            print("No results in API response")
            print("Full response:", json.dumps(data, indent=2)[:1000])
            return {}

        raw = data[0]["results"][0]

        # --- Helper to get .raw ---
        def get(field, default="N/A"):
            val = raw.get(field, {})
            if isinstance(val, dict):
                return val.get("raw", default)
            return val if val is not None else default

        # --- Extract data (using available fields) ---
        title = get("item_name")
        designer = get("designer_brand") or get("brand_name")
        description = ""  # Not available in valid fields
        images = get("image_urls", [])  # Note: this was invalid, so may be empty; fallback to cl/second
        if not images:
            images = []
            if get("cl_image_url"): images.append(get("cl_image_url"))
            if get("second_image_url") and get("second_image_url") not in images: images.append(get("second_image_url"))

        hire_price = get("listing_view_price")
        retail_price = get("rrp")
        purchase_price = get("lowest_unit_purchase_price")

        # Sizes
        sizes = set()
        for field in ["unit_sizes_available", "available_sizes"]:
            lst = get(field, [])
            if isinstance(lst, list):
                sizes.update(lst)
        sizes_list = sorted(list(sizes))

        # Hire prices (single entry)
        hire_prices = []
        if hire_price:
            hire_prices.append({
                "duration": "Standard rental",
                "price": hire_price,
                "sizes": sizes_list
            })

        # Missing fields get defaults
        material_info = ""
        sizing_info = ""
        condition = "N/A"
        color = get("colour_category")
        category = "N/A"
        subcategory = "N/A"

        # Build result
        result = {
            "platform": "HURR",
            "url": url,
            "title": title,
            "designer": designer,
            "description": description,
            "material_info": material_info,
            "sizing_info": sizing_info,
            "condition": condition,
            "color": color,
            "category": category,
            "subcategory": subcategory,
            "sizes": sizes_list,
            "hire_prices": hire_prices,
            "retail_price": retail_price,
            "purchase_price": purchase_price,
            "images": images,
            "lender": get("lender_name"),
            "top_lender": get("top_lender?", False),
            "managed_item": get("managed_item?", False),
            "listing_id": get("id"),
            "slug": slug,
        }

        # --- Print ---
        print("\nRESULT:")
        for k, v in result.items():
            if isinstance(v, list) and len(v) > 5:
                print(f"{k}: [{len(v)} items] {v[:3]}...")
            elif isinstance(v, str) and len(v) > 150:
                print(f"{k}: {v[:150]}...")
            else:
                print(f"{k}: {v}")

        return result

    except Exception as e:
        print(f"Error: {e}")
        traceback.print_exc()
        return {}


# ------------------------------------------------------------------
# Test
# ------------------------------------------------------------------
if __name__ == "__main__":
    test_url = "https://www.hurrcollective.com/listings/red-short-sleeve-chiffon-midi-41682"
    result = scrape_single_hurr(test_url)