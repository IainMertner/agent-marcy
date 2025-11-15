import requests
from bs4 import BeautifulSoup
import json
import re

def scrape_single_dress(url: str) -> dict:
    """Scrape a single GirlMeetsDress product URL for all relevant info."""
    print("="*60)
    print(f"Scraping: {url}")
    print("="*60)
    
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

    try:
        # Fetch page HTML
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        
        # --- Basic Info ---
        title_tag = soup.find('h1')
        title = title_tag.get_text(strip=True) if title_tag else "N/A"

        designer_tag = soup.find(class_=lambda x: x and 'vendor' in x.lower())
        designer = designer_tag.get_text(strip=True) if designer_tag else "N/A"

        img_tag = soup.find('img', class_=lambda x: x and 'product' in x.lower())
        image = None
        if img_tag:
            image = img_tag.get('src') or img_tag.get('data-src')
            if image and image.startswith('//'):
                image = 'https:' + image

        # Retail price (if mentioned)
        retail_price = None
        retail_tag = soup.find(string=re.compile(r"Retail", re.I))
        if retail_tag:
            match = re.search(r"£([\d,]+)", retail_tag)
            if match:
                retail_price = int(match.group(1).replace(',', ''))

        # --- Description & tabs ---
        description_tag = soup.find("div", id="tabs-1")
        description = description_tag.get_text(separator="\n", strip=True) if description_tag else ""

        material_tag = soup.find("div", id="tabs-2")
        material_info = material_tag.get_text(separator="\n", strip=True) if material_tag else ""

        sizing_tag = soup.find("div", id="tabs-3")
        sizing_info = sizing_tag.get_text(separator="\n", strip=True) if sizing_tag else ""

        # --- Extract JSON variant data from Shopify ---
        script_tag = soup.find("script", string=re.compile(r"var meta\s*=\s*{"))
        sizes = set()
        hire_prices = []

        if script_tag:
            js_text = script_tag.string.strip()
            js_json_match = re.search(r"var meta\s*=\s*(\{.*\});", js_text, re.DOTALL)
            if js_json_match:
                meta_json = js_json_match.group(1)
                meta_data = json.loads(meta_json)
                variants = meta_data["product"]["variants"]

                for v in variants:
                    if "PURCHASE" in v["public_title"].upper():
                        continue  # skip purchase variants
                    parts = v["public_title"].split(" - ")
                    if len(parts) == 2:
                        size, duration = parts
                        sizes.add(size.strip())
                        hire_prices.append({
                            "size": size.strip(),
                            "duration": duration.strip(),
                            "price": v["price"] / 100  # convert pence to £
                        })

        sizes = sorted(list(sizes))

        # --- Result dictionary ---
        result = {
            "platform": "GirlMeetsDress",
            "url": url,
            "title": title,
            "designer": designer,
            "description": description,
            "material_info": material_info,
            "sizing_info": sizing_info,
            "sizes": sizes,
            "hire_prices": hire_prices,
            "retail_price": retail_price,
            "image": image
        }

        # Print results
        print("\nRESULT:")
        for k, v in result.items():
            print(f"{k}: {v}")

        return result

    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return {}

# Example usage
if __name__ == "__main__":
    test_url = "https://hire.girlmeetsdress.com/products/lipstick-red-gown?_pos=2&_sid=1bf31eca9&_ss=r"
    scrape_single_dress(test_url)
