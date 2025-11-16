import requests
import json

API_URL = "https://www.hirestreetuk.com/api/2025-01/graphql.json"
HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/graphql-response+json, application/json",
    "x-shopify-storefront-access-token": "abbba5e66dc038ed6b2291353aedccf5",
    "User-Agent": "Mozilla/5.0"
}

def get_details(url):
    # Extract handle
    handle = url.split("/products/")[-1].split("?")[0]
    
    query = """
    query getProduct($handle: String!) {
      product(handle: $handle) {
        title
        vendor
        description
        images(first: 20) { nodes { url } }
        productType
        priceRange {
          minVariantPrice { amount currencyCode }
        }
        compareAtPriceRange {
          minVariantPrice { amount currencyCode }
        }
        variants(first: 250) {
          edges {
            node {
              selectedOptions { name value }
              price { amount currencyCode }
            }
          }
        }
      }
    }
    """

    payload = {"query": query, "variables": {"handle": handle}}

    try:
        r = requests.post(API_URL, headers=HEADERS, json=payload)
        r.raise_for_status()
        data = r.json()

        product = data["data"]["product"]
        if not product:
            return {}

        # Extract sizes (from variant option "Size")
        sizes = []
        for edge in product["variants"]["edges"]:
            opts = edge["node"]["selectedOptions"]
            for o in opts:
                if o["name"].lower() == "size":
                    sizes.append(o["value"])

        return {
            "url": url,
            "title": product["title"],
            "brand": product["vendor"],
            "description": product["description"],
            "rental_prices": {
                "amount": float(product["priceRange"]["minVariantPrice"]["amount"]),
                "currency": product["priceRange"]["minVariantPrice"]["currencyCode"]
            },
            "daily_rate": None,  # API does not expose daily rate
            "retail_price": (
                {
                    "amount": float(product["compareAtPriceRange"]["minVariantPrice"]["amount"]),
                    "currency": product["compareAtPriceRange"]["minVariantPrice"]["currencyCode"]
                }
                if product.get("compareAtPriceRange") and product["compareAtPriceRange"]["minVariantPrice"]
                else None
            ),
            "sizes": sorted(list(set(sizes))),
            "images": [img["url"] for img in product["images"]["nodes"]],
        }

    except Exception as e:
        print("Error:", e)
        return {}