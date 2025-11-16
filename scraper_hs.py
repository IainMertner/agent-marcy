import requests
import json

ENDPOINT = "https://www.hirestreetuk.com/api/2025-01/graphql.json"

HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json",
    "x-shopify-storefront-access-token": "abbba5e66dc038ed6b2291353aedccf5",
    "User-Agent": "Mozilla/5.0"
}

GRAPHQL_QUERY = """
query getSearchResults($query: String!, $productFilters: [ProductFilter!], $productLimitFirst: Int, $afterCursor: String) {
  search(
    query: $query
    first: $productLimitFirst
    after: $afterCursor
    types: PRODUCT
    productFilters: $productFilters
    sortKey: RELEVANCE
  ) {
    totalCount
    pageInfo {
      hasNextPage
      endCursor
    }
    edges {
      cursor
      node {
        ... on Product {
          title
          handle
          vendor
          id
          images(first: 2) {
            nodes { url }
          }
          priceRange {
            minVariantPrice { amount }
          }
          variants(first: 250) {
            edges {
              node {
                id
                price { amount }
                quantityAvailable
                selectedOptions { name value }
                available: metafield(key: "is_available", namespace: "zoa") { value }
              }
            }
          }
        }
      }
    }
  }
}
"""

def fetch_page(search_term, cursor=None, page_size=28):
    variables = {
        "query": search_term,
        "productLimitFirst": page_size,
        "afterCursor": cursor,
        "productFilters": [
            {"variantMetafield": {
                "namespace": "zoa",
                "key": "primary_variant",
                "value": "true"
            }},
            {"variantMetafield": {
                "namespace": "zoa",
                "key": "is_available",
                "value": "true"
            }}
        ]
    }

    response = requests.post(
        ENDPOINT,
        headers=HEADERS,
        json={"query": GRAPHQL_QUERY, "variables": variables}
    )

    response.raise_for_status()
    data = response.json()

    return data["data"]["search"]


def scrape_all(search_term="red", max_pages=20):
    all_products = []
    cursor = None

    for page in range(max_pages):
        print(f"Fetching page {page+1}...")

        result = fetch_page(search_term, cursor)

        edges = result["edges"]

        if not edges:
            print("No items found.")
            break

        for edge in edges:
            node = edge["node"]

            # Build the public product URL
            node["url"] = f"https://www.hirestreetuk.com/products/{node['handle']}"

            all_products.append(node)

            # Print product URL
            print(node["url"])

        if not result["pageInfo"]["hasNextPage"]:
            break

        cursor = result["pageInfo"]["endCursor"]

    return all_products

if __name__ == "__main__":
    products = scrape_all("red")
    print(f"Total scraped: {len(products)} items")
