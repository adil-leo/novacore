import json
import os
import re
from datetime import datetime
import requests
from bs4 import BeautifulSoup

# ==============================================================================
# CONFIGURATION & AFFILIATE SETTINGS
# ==============================================================================
IMPACT_AFFILIATE_ID = os.getenv("IMPACT_AFFILIATE_ID", "YOUR_IMPACT_ID_HERE")
FALLBACK_REF_TAG = "novacore"
DEALS_JSON_PATH = "deals.json"

def wrap_affiliate_link(original_url):
    if IMPACT_AFFILIATE_ID != "YOUR_IMPACT_ID_HERE":
        return f"https://appsumo.8357.net/c/{IMPACT_AFFILIATE_ID}/1/appsumo?u={original_url}"
    else:
        connector = "&" if "?" in original_url else "?"
        return f"{original_url}{connector}ref={FALLBACK_REF_TAG}"

# ==============================================================================
# BULLETPROOF APPSUMO SCRAPER (Next.js Data Extraction)
# ==============================================================================
def fetch_appsumo_deals():
    print("🔍 Fetching live SaaS deals from AppSumo...")
    url = "https://appsumo.com/browse/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9"
    }

    deals = []
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            print(f"❌ Failed to fetch page. Status: {response.status_code}")
            return deals

        soup = BeautifulSoup(response.text, "html.parser")
        
        # Method 1: Next.js hidden JSON extraction (Most Reliable)
        next_data_script = soup.find("script", id="__NEXT_DATA__")
        
        if next_data_script and next_data_script.string:
            try:
                raw_json = json.loads(next_data_script.string)
                # Search recursively for products list in Next.js props
                page_props = raw_json.get("props", {}).get("pageProps", {})
                products = page_props.get("products", []) or page_props.get("initialDeals", [])
                
                for idx, prod in enumerate(products[:12]):
                    title = prod.get("name") or prod.get("title", "SaaS Lifetime Deal")
                    slug = prod.get("slug") or prod.get("url", "")
                    product_url = f"https://appsumo.com/products/{slug}/" if slug and not slug.startswith("http") else slug
                    
                    price = prod.get("price") or prod.get("plan_price") or "49"
                    image = prod.get("image_url") or prod.get("cover_image", "https://via.placeholder.com/400x250?text=SaaS+Lifetime+Deal")

                    deals.append({
                        "id": f"deal-appsumo-{idx + 1}",
                        "title": title,
                        "category": "SaaS & AI Tools",
                        "original_price": "$199",
                        "deal_price": f"${price}" if not str(price).startswith("$") else str(price),
                        "discount": "LIFETIME DEAL",
                        "image": image,
                        "affiliate_url": wrap_affiliate_link(product_url),
                        "network": "AppSumo",
                        "status": "Active",
                        "updated_at": datetime.now().strftime("%Y-%m-%d")
                    })
            except Exception as parse_err:
                print(f"⚠️ JSON parsing skipped: {parse_err}")

        # Method 2: HTML Link Fallback (Agar Next.js Script na mile)
        if not deals:
            print("⚙️ Fallback to direct HTML parser...")
            product_links = soup.find_all("a", href=re.compile(r"/products/"))
            seen_urls = set()
            count = 0

            for a in product_links:
                href = a["href"]
                full_url = href if href.startswith("http") else f"https://appsumo.com{href}"
                
                if full_url in seen_urls or "/products/" not in full_url:
                    continue
                seen_urls.add(full_url)

                title = a.get_text(strip=True)
                if not title or len(title) < 4:
                    continue

                deals.append({
                    "id": f"deal-appsumo-{count + 1}",
                    "title": title,
                    "category": "SaaS & AI Tools",
                    "original_price": "$199",
                    "deal_price": "$49",
                    "discount": "LIFETIME DEAL",
                    "image": "https://via.placeholder.com/400x250?text=SaaS+Lifetime+Deal",
                    "affiliate_url": wrap_affiliate_link(full_url),
                    "network": "AppSumo",
                    "status": "Active",
                    "updated_at": datetime.now().strftime("%Y-%m-%d")
                })
                count += 1
                if count >= 12:
                    break

    except Exception as e:
        print(f"❌ Scraping error: {e}")

    return deals

# ==============================================================================
# MAIN EXECUTION
# ==============================================================================
def main():
    print("🚀 Starting Novacore Real Engine Pipeline...")
    
    live_deals = fetch_appsumo_deals()

    if not live_deals:
        print("⚠️ No live deals fetched. Existing deals.json protected.")
        return

    # Update deals.json
    with open(DEALS_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(live_deals, f, indent=2, ensure_ascii=False)

    print(f"✅ Successfully updated {DEALS_JSON_PATH} with {len(live_deals)} real live deals!")

if __name__ == "__main__":
    main()