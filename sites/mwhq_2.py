import requests
from bs4 import BeautifulSoup
import json
import re
import time

def get_details(url: str) -> dict:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-GB,en;q=0.9"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        
        title = None
        og_title = soup.find("meta", property="og:title")
        if og_title:
            title_full = og_title.get("content", "")
            # Remove " | MY WARDROBE HQ" and "Rent Buy" prefix
            title = title_full.replace("| MY WARDROBE HQ", "").replace("Rent Buy", "").strip()
        
        if not title:
            title_tag = soup.find("title")
            if title_tag:
                title = title_tag.get_text().replace("| MY WARDROBE HQ", "").replace("Rent Buy", "").strip()
        
        designer = None
        if title:
            # Designer is typically the first part before the product name
            parts = title.split()
            # Look for all-caps words at the start (designer names)
            designer_parts = []
            for part in parts:
                if part.isupper() and len(part) > 1:
                    designer_parts.append(part)
                else:
                    break
            if designer_parts:
                designer = " ".join(designer_parts)
        
        image = None
        og_image = soup.find("meta", property="og:image")
        if og_image:
            image = og_image.get("content")
            # Convert to full size if it's a thumb
            if image and 'thumb_' in image:
                image = image.replace('thumb_', '')
        
        description = None
        og_desc = soup.find("meta", property="og:description")
        if og_desc:
            description = og_desc.get("content", "").strip()
        
        if not description:
            desc_meta = soup.find("meta", attrs={"name": "description"})
            if desc_meta:
                description = desc_meta.get("content", "").strip()
        
        page_text = soup.get_text()
        
        # Sale price (current price)
        sale_price = None
        sale_matches = re.findall(r'(?:SALE|BUY NOW)[:\s]*£([\d,]+)', page_text, re.IGNORECASE)
        if sale_matches:
            sale_price = int(sale_matches[0].replace(',', ''))
        
        # Retail price (RRP)
        retail_price = None
        rrp_matches = re.findall(r'RRP[:\s]*£([\d,]+)', page_text, re.IGNORECASE)
        if rrp_matches:
            retail_price = int(rrp_matches[0].replace(',', ''))
        
        # Rent/Hire price
        hire_price = None
        rent_matches = re.findall(r'(?:Rent|Rental|Hire)[:\s]*(?:from[:\s]*)?£([\d,]+)', page_text, re.IGNORECASE)
        if rent_matches:
            hire_price = int(rent_matches[0].replace(',', ''))
        
        sizes = []
        
        # Method 1: Look in select dropdowns
        selects = soup.find_all("select")
        for select in selects:
            select_name = str(select.get('name', '')).lower()
            select_id = str(select.get('id', '')).lower()
            
            if 'size' in select_name or 'size' in select_id or 'variant' in select_name:
                options = select.find_all("option")
                for opt in options:
                    opt_text = opt.get_text(strip=True)
                    opt_value = opt.get('value', '')
                    
                    if opt_text and opt_text.lower() not in ['select', 'select size', 'please select', '']:
                        if opt_text not in sizes:
                            sizes.append(opt_text)
        
        # Method 2: Look in script tags for product data
        scripts = soup.find_all("script")
        for script in scripts:
            if script.string and 'size' in script.string.lower():
                # Look for size patterns like "UK 6", "UK 8", etc
                size_matches = re.findall(r'UK\s*(\d+)', script.string, re.IGNORECASE)
                for size in size_matches:
                    size_str = f"UK {size}"
                    if size_str not in sizes:
                        sizes.append(size_str)
        
        # Method 3: Look for size buttons/divs
        size_elements = soup.find_all(['button', 'div', 'span'], class_=lambda x: x and 'size' in str(x).lower())
        for elem in size_elements:
            size_text = elem.get_text(strip=True)
            if size_text and len(size_text) < 15 and size_text not in sizes:
                # Check if it looks like a size
                if re.match(r'^(UK\s*)?\d+$', size_text) or size_text.upper() in ['XXS', 'XS', 'S', 'M', 'L', 'XL', 'XXL']:
                    sizes.append(size_text)
        
        material_info = ""
        sizing_info = ""
        
        # Look in divs that might contain this info
        for div in soup.find_all(['div', 'section', 'article']):
            div_text = div.get_text("\n", strip=True)
            
            if len(div_text) > 20:  # Substantial content
                if any(word in div_text.lower() for word in ['material', 'fabric', 'composition', 'cotton', 'polyester']):
                    if len(div_text) < 500:  # Not too long
                        material_info = div_text
                
                if any(word in div_text.lower() for word in ['model', 'height', 'wearing', 'size guide']):
                    if len(div_text) < 500:
                        sizing_info = div_text
        
        result = {
            "platform": "MyWardrobeHQ",
            "url": url,
            "title": title or "N/A",
            "designer": designer or "N/A",
            "description": description or "",
            "material_info": material_info,
            "sizing_info": sizing_info,
            "sizes": sizes,
            "sale_price": sale_price,
            "hire_price": hire_price,
            "retail_price": retail_price,
            "image": image
        }
        
        return result
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return {}
