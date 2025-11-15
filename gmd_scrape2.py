import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import time
import re
import json

BASE_URL = "https://hire.girlmeetsdress.com"

class GirlMeetsDressScraper:
    def __init__(self, delay=1.0):
        """Initialize scraper with rate limiting."""
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
    
    def scrape_collection_page(self, url):
        """Scrape all items from a collection page."""
        print(f"\nFetching: {url}")
        
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            print(f"✓ Page loaded successfully")
        except Exception as e:
            print(f"✗ Error fetching page: {e}")
            return []
        
        time.sleep(self.delay)
        
        # Find all products
        items = []
        rows = soup.find_all('tr')
        
        for row in rows:
            cells = row.find_all('td')
            for cell in cells:
                # Check if this cell has a product
                product_link = cell.find('a', href=lambda x: x and '/products/' in x)
                if product_link:
                    item = self._parse_product_cell(cell)
                    if item:
                        items.append(item)
        
        print(f"✓ Found {len(items)} products")
        return items
    
    def _parse_product_cell(self, cell):
        """Extract product information from a table cell."""
        product_url = None
        designer = None
        title = None
        retail_price = None
        
        # Get all links in this cell
        links = cell.find_all('a')
        
        for link in links:
            href = link.get('href', '')
            text = link.get_text(strip=True)
            
            # Skip empty text or "Add to wishlist"
            if not text or 'Add to wishlist' in text:
                continue
            
            # Designer link
            if '/collections/vendors' in href:
                designer = text
            
            # Product link and title
            elif '/products/' in href:
                if not product_url:
                    product_url = urljoin(BASE_URL, href)
                
                # Extract title (not "Hire now" or "Retail")
                if 'Hire now' not in text and 'Retail' not in text:
                    if not title:
                        title = text
            
            # Check for retail price
            if 'Retail:' in text:
                match = re.search(r'£([\d,]+)', text)
                if match:
                    retail_price = int(match.group(1).replace(',', ''))
        
        if not product_url or not title:
            return None
        
        # Extract hire price
        hire_price = None
        cell_text = cell.get_text()
        match = re.search(r'Hire\s+now[:\s]*£(\d+)', cell_text, re.IGNORECASE)
        if match:
            hire_price = int(match.group(1))
        
        # Extract image
        image = None
        img = cell.find('img')
        if img:
            image = img.get('src') or img.get('data-src')
            if image and image.startswith('//'):
                image = 'https:' + image
            elif image and not image.startswith('http'):
                image = urljoin(BASE_URL, image)
        
        return {
            "platform": "GirlMeetsDress",
            "designer": designer,
            "title": title,
            "url": product_url,
            "image": image,
            "hire_price": hire_price,
            "retail_price": retail_price,
        }
    
    def scrape_product_page(self, url):
        """Scrape detailed information from a product page."""
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            time.sleep(self.delay)
            
            # Extract sizes
            sizes = []
            selects = soup.find_all('select')
            for select in selects:
                options = select.find_all('option')
                for opt in options:
                    size_text = opt.get_text(strip=True)
                    if size_text and size_text.lower() not in ['select size', 'select', '', 'sold out']:
                        sizes.append(size_text)
            
            # Extract description
            description = None
            for selector in ['.product-description', '.description', '[class*="description"]']:
                desc = soup.select_one(selector)
                if desc:
                    description = desc.get_text(strip=True)
                    break
            
            return {
                "sizes": list(set(sizes)),
                "description": description
            }
        
        except Exception as e:
            print(f"  Warning: Could not fetch product details - {e}")
            return {"sizes": [], "description": None}
    
    def scrape_with_details(self, collection_url, max_items=None):
        """Scrape collection and get product details."""
        print("="*60)
        print("Girl Meets Dress Scraper")
        print("="*60)
        
        # Get all products from collection page
        items = self.scrape_collection_page(collection_url)
        
        if not items:
            print("✗ No items found")
            return []
        
        # Limit items if requested
        if max_items:
            items = items[:max_items]
            print(f"\nLimiting to first {max_items} items")
        
        # Get details for each product
        print(f"\nFetching details for {len(items)} products...")
        print("-"*60)
        
        detailed_items = []
        for idx, item in enumerate(items, 1):
            print(f"\n[{idx}/{len(items)}] {item['designer']} - {item['title']}")
            
            # Get product page details
            details = self.scrape_product_page(item['url'])
            item.update(details)
            
            detailed_items.append(item)
        
        return detailed_items


def main():
    """Run the scraper."""
    # Initialize scraper
    scraper = GirlMeetsDressScraper(delay=1.0)
    
    # Scrape wedding guest dresses (change max_items as needed)
    url = "https://hire.girlmeetsdress.com/collections/wedding-guest-dresses"
    dresses = scraper.scrape_with_details(url, max_items=10)
    
    # Print results
    print("\n" + "="*60)
    print(f"RESULTS: {len(dresses)} dresses scraped")
    print("="*60)
    
    for dress in dresses:
        print(f"\nDesigner: {dress.get('designer', 'N/A')}")
        print(f"Title: {dress['title']}")
        print(f"Hire Price: £{dress['hire_price']}" if dress.get('hire_price') else "Hire Price: N/A")
        print(f"Retail Price: £{dress['retail_price']}" if dress.get('retail_price') else "Retail Price: N/A")
        print(f"Sizes: {', '.join(dress['sizes'])}" if dress.get('sizes') else "Sizes: N/A")
        print(f"URL: {dress['url']}")
        print("-"*60)
    
    # Save to JSON file
    try:
        with open('girlmeetsdress_dresses.json', 'w', encoding='utf-8') as f:
            json.dump(dresses, f, indent=2, ensure_ascii=False)
        print(f"\n✓ Data saved to girlmeetsdress_dresses.json")
    except Exception as e:
        print(f"\n✗ Could not save file: {e}")
    
    return dresses


if __name__ == "__main__":
    dresses = main()