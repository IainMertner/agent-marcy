import requests
from bs4 import BeautifulSoup
import json
import re

def get_details(url):
    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(url, headers=headers)
    if r.status_code != 200:
        print(f"✗ Failed to fetch page: {r.status_code}")
        return {}

    # Extract the JSON inside window.__INITIAL_STATE__
    match = re.search(r'window\.__INITIAL_STATE__\s*=\s*({.*});', r.text)
    if not match:
        print("✗ Could not find __INITIAL_STATE__ JSON in page")
        return {}
    
    data = json.loads(match.group(1))
    
    # Navigate to product details
    try:
        product_data = next(iter(data['listings'].values()))
    except (KeyError, StopIteration):
        print("✗ Could not find product data in JSON")
        return {}

    title = product_data.get('name')
    brand = product_data.get('designer_brand')
    description = product_data.get('description')
    images = product_data.get('images', [])
    sizes = product_data.get('available_sizes', [])
    rental_prices = product_data.get('rental_price', {})
    daily_rate = product_data.get('daily_rate')
    retail_price = product_data.get('rrp')

    product = {
        "url": url,
        "title": title,
        "brand": brand,
        "description": description,
        "rental_prices": rental_prices,
        "daily_rate": daily_rate,
        "retail_price": retail_price,
        "sizes": sizes,
        "images": images
    }
    
    return product
