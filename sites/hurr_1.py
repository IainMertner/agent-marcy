import requests
import json

API_URL = "https://hurr-eu.ent.eu-west-2.aws.cloud.es.io/api/as/v1/engines/search-production-hurr-listings-v4/multi_search.json"
BEARER_TOKEN = "search-kms28ixa6p378p4d4fvm53r3"

HEADERS = {
    "Authorization": f"Bearer {BEARER_TOKEN}",
    "Content-Type": "application/json",
    "Accept": "*/*",
}

def fetch_hurr(query, max_per_site, page=1, ):
    """Fetch results from HURR's public ElasticSearch API."""
    payload = {
        "queries": [
            {
                "query": query,
                "page": {"current": page, "size": max_per_site}
            }
        ]
    }

    try:
        r = requests.post(API_URL, headers=HEADERS, json=payload, timeout=15)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print("API Error:", e)
        return None


def correct_hurr_url(slug: str) -> str:
    """Return the REAL, WORKING HURR listing URL."""
    return f"https://www.hurrcollective.com/listings/{slug}"


def get_item_urls(query, max_per_site):

    item_urls = []
    data = fetch_hurr(query, max_per_site, page=1)

    if not data:
        print("No API data returned.")
        return []

    results = data[0].get("results", [])

    if not results:
        print("No more results.")
        return []

    for item in results:
        slug = item.get("slug", {}).get("raw", "")
        url = f"https://www.hurrcollective.com/listings/{slug}"
        item_urls.append(url)

    return item_urls