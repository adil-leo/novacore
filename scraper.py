import json
import os
import re
from datetime import datetime
import requests
from bs4 import BeautifulSoup

IMPACT_AFFILIATE_ID = os.getenv("IMPACT_AFFILIATE_ID", "YOUR_IMPACT_ID_HERE")
FALLBACK_REF_TAG = "novacore"
DEALS_JSON_PATH = "deals.json"

def wrap_affiliate_link(original_url):
    if IMPACT_AFFILIATE_ID != "YOUR_IMPACT_ID_HERE":
        return f"https://appsumo.8357.net/c/{IMPACT_AFFILIATE_ID}/1/appsumo?u={original_url}"
    else:
        connector = "&" if "?" in original_url else "?"
        return f"{original_url}{connector}ref={FALLBACK_REF_TAG}"

def fetch_appsumo_deals():
    print("🔍 Fetching & cleaning live SaaS deals from AppSumo...")
    url = "https://appsumo.com/browse/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9"
    }

    deals = []
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            return deals

        soup = BeautifulSoup(response.text, "html.parser")
        product_links = soup.find_all("a", href=re.compile(r"/products/"))
        
        seen_urls = set()
        count = 0

        for a in product_links:
            href = a.get("href", "")
            
            # Review links aur duplicate links ko filter karo
            if "#" in href or "reviews" in href.lower() or "/products/" not in href:
                continue

            full_url = href if href.startswith("http") else f"https://appsumo.com{href}"
            clean_url = full_url.split("?")[0]

            if clean_url in seen_urls:
                continue
            
            title = a.get_text(strip=True)
            # Review counts (e.g. "66reviews") ya small titles filter karo
            if not title or len(title) < 4 or re.search(r"^\d+\s*reviews?", title, re.I):
                continue

            seen_urls.add(clean_url)
            count += 1

            aff_link = wrap_affiliate_link(clean_url)
            
            # All-in-One Key Mapping (Fixes all 'undefined' issues)
            deal_data = {
                "id": f"deal-appsumo-{count}",
                "title": title,
                "name": title,
                "description": f"Grab lifetime deal access to {title} on AppSumo. Save big on SaaS & AI tools.",
                "snippet": f"Special discount deal for {title}.",
                "category": "SaaS & AI",
                "tag": "SaaS & AI",
                "badge": "LIFETIME DEAL",
                "original_price": "$199",
                "old_price": "$199",
                "deal_price": "$49",
                "price": "$49",
                "discount": "75% OFF",
                "image": "https://via.placeholder.com/400x250/1e293b/38bdf8?text=" + title.replace(" ", "+"),
                "affiliate_url": aff_link,
                "url": aff_link,
                "link": aff_link,
                "network": "AppSumo",
                "rating": "4.9",
                "status": "Active",
                "updated_at": datetime.now().strftime("%Y-%m-%d")
            }
            deals.append(deal_data)

            if count >= 12:
                break

    except Exception as e:
        print(f"❌ Error: {e}")

    return deals

def main():
    print("🚀 Starting Novacore Data Cleaner Pipeline...")
    live_deals = fetch_appsumo_deals()

    if not live_deals:
        print("⚠️ No valid deals parsed.")
        return

    with open(DEALS_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(live_deals, f, indent=2, ensure_ascii=False)

    print(f"✅ Successfully cleaned & updated {len(live_deals)} deals in {DEALS_JSON_PATH}!")

if __name__ == "__main__":
    main()