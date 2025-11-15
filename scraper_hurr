import requests

API_URL = "https://hurr-eu.ent.eu-west-2.aws.cloud.es.io/api/as/v1/engines/search-production-hurr-listings-v4/multi_search.json"
BEARER_TOKEN = "search-kms28ixa6p378p4d4fvm53r3"

HEADERS = {
    "Authorization": f"Bearer {BEARER_TOKEN}",
    "Content-Type": "application/json",
    "Accept": "*/*",
}

def fetch_hurr(query="red", page=1, size=100):
    payload = {
        "queries": [
            {
                "query": query,
                "page": {"current": page, "size": size}
            }
        ]
    }

    res = requests.post(API_URL, headers=HEADERS, json=payload)
    res.raise_for_status()
    return res.json()

def scrape_hurr(query="red"):
    data = fetch_hurr(query)

    results = data[0]["results"]  # HURR returns a list of responses

    products = []

    print(f"Found {len(results)} items for '{query}':\n")

    for item in results:
        raw = item  # shortcut

        title = raw["item_name"]["raw"]
        brand = raw["designer_brand"]["raw"]
        slug = raw["slug"]["raw"]
        public_uid = raw["public_uid"]["raw"]

        img = raw["cl_image_url"]["raw"]
        size = raw.get("available_sizes", {}).get("raw")

        # Public product URL
        url = f"https://www.hurrcollective.com/listings/{slug}"

        # Save
        products.append({
            "title": title,
            "brand": brand,
            "slug": slug,
            "public_uid": public_uid,
            "image": img,
            "size": size,
            "url": url
        })

        # Print
        print(url)

    return products


if __name__ == "__main__":
    scrape_hurr("red")
