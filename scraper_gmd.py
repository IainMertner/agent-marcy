from __future__ import annotations

import re
from typing import List, Dict, Optional

import requests
from bs4 import BeautifulSoup

BASE_DOMAIN = "https://hire.girlmeetsdress.com"
COLLECTION_URL = f"{BASE_DOMAIN}/search?q=red&x=0&y=0"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/119.0 Safari/537.36"
    )
}


def fetch_collection_html(url: str = COLLECTION_URL) -> str:
    """Fetch the raw HTML for the search/collection page."""
    resp = requests.get(url, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    return resp.text


def _extract_price_from_text(text: str) -> Optional[float]:
    """Try to pull out a price like '£45' or '£45.50' from text."""
    if not text:
        return None

    match = re.search(r"£\s*([0-9]+(?:\.[0-9]+)?)", text)
    if not match:
        return None

    try:
        return float(match.group(1))
    except ValueError:
        return None


def parse_collection_html(html: str) -> List[Dict]:
    """Parse the HTML and extract individual product items."""
    soup = BeautifulSoup(html, "html.parser")

    items: List[Dict] = []
    seen_urls = set()

    # Find all <a> tags that look like product links (/products/...)
    for link in soup.find_all("a", href=True):
        href = link["href"]
        if "/products/" not in href:
            continue

        # Build absolute URL
        if href.startswith("http"):
            full_url = href
        else:
            full_url = BASE_DOMAIN + href

        # Deduplicate
        if full_url in seen_urls:
            continue
        seen_urls.add(full_url)

        # Title: link text, or image alt, or URL tail
        title_text = link.get_text(strip=True)
        if not title_text:
            img = link.find("img")
            if img and img.has_attr("alt"):
                title_text = img["alt"].strip()
        if not title_text:
            title_text = (
                full_url.rstrip("/").split("/")[-1].replace("-", " ").title()
            )

        # Try to find a price near the link
        price: Optional[float] = None
        for ancestor in (link, link.parent, getattr(link.parent, "parent", None)):
            if ancestor is None:
                continue
            text = ancestor.get_text(separator=" ", strip=True)
            price = _extract_price_from_text(text)
            if price is not None:
                break

        item = {
            "title": title_text,
            "price": price,        # may be None
            "delivery": "Unknown", # placeholder
            "url": full_url,
        }
        items.append(item)

    return items


def scrape_new_dresses() -> List[Dict]:
    """Fetch and parse the search/collection page into item dicts."""
    html = fetch_collection_html(COLLECTION_URL)
    return parse_collection_html(html)


if __name__ == "__main__":
    print(f"Scraping collection: {COLLECTION_URL}")
    try:
        dresses = scrape_new_dresses()
    except Exception as e:
        print("Error while scraping:", e)
    else:
        print(f"Found {len(dresses)} items.\n")
        for item in dresses:
            print(item["url"])
