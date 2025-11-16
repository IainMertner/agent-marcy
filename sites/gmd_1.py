import re
from typing import List, Dict, Optional
import requests
from bs4 import BeautifulSoup

### parse html and extract item urls
def extract_urls_from_html(html: str, BASE_DOMAIN: str, max_per_site) -> List[Dict]:
    soup = BeautifulSoup(html, "html.parser")

    item_urls = []
    seen_urls = set()
    num_urls = 0

    # loop over all <a> tags with href
    for link in soup.find_all("a", href=True):
        href = link["href"]
        if "/products/" not in href:
            continue # skip links that aren't products

        # convert relative url to absolute
        full_url = href if href.startswith("http") else BASE_DOMAIN + href

        # deduplicate
        if full_url in seen_urls:
            continue
        seen_urls.add(full_url)
        item_urls.append(full_url)
        
        num_urls += 1
        if num_urls >= max_per_site:
            break


    return item_urls

### fetch the search page for the given query and extract item urls
def get_item_urls(user_input, max_per_site) -> List[Dict]:

    # target url
    BASE_DOMAIN = "https://hire.girlmeetsdress.com"
    COLLECTION_URL = f"{BASE_DOMAIN}/search?q={user_input}&x=0&y=0"

    # headers
    HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/119.0 Safari/537.36"
        )
    }

    # fetch page and parse urls
    resp = requests.get(COLLECTION_URL, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    return extract_urls_from_html(resp.text, BASE_DOMAIN, max_per_site)