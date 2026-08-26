import json
import os
import re
import urllib.parse
from datetime import datetime
import requests
from bs4 import BeautifulSoup

try:
    from pytrends.request import TrendReq
    PYTRENDS_AVAILABLE = True
except ImportError:
    PYTRENDS_AVAILABLE = False

IMPACT_BASE_LINK = "https://appsumo.8odi.net/1GKLRx"
DEALS_JSON_PATH = "deals.json"

def wrap_affiliate_link(original_url):
    encoded_url = urllib.parse.quote(original_url, safe='')
    return f"{IMPACT_BASE_LINK}?u={encoded_url}"

def categorize_deal(title, description=""):
    text = f"{title} {description}".lower()

    hosting_keywords = ["host", "hosting", "domain", "vps", "server", "cloud", "wordpress", "storage", "cdn", "dns"]
    marketing_keywords = ["seo", "marketing", "email", "social", "ads", "lead", "funnel", "crm", "analytics", "traffic", "copy", "rank", "outreach"]
    ai_keywords = ["ai", "gpt", "bot", "generator", "writer", "prompt", "llm", "copilot", "chat", "avatar", "transcribe"]

    if any(kw in text for kw in ai_keywords):
        return "AI Tools"
    elif any(kw in text for kw in marketing_keywords):
        return "Marketing"
    elif any(kw in text for kw in hosting_keywords):
        return "Hosting"
    else:
        return "SaaS"

def fetch_product_details(clean_url, headers):
    """Deep scrapes individual AppSumo deal page cleanly using attrs dict."""
    details = {
        "deal_price": "$49",
        "original_price": "$199",
        "description": "",
        "image": ""
    }
    try:
        res = requests.get(clean_url, headers=headers, timeout=5)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")
            
            # Extract Meta Description cleanly
            meta_desc = soup.find("meta", attrs={"name": "description"}) or soup.find("meta", attrs={"property": "og:description"})
            if meta_desc and meta_desc.get("content"):
                details["description"] = meta_desc["content"].strip()

            # Extract Image / Og:image
            og_img = soup.find("meta", attrs={"property": "og:image"}) or soup.find("meta", attrs={"name": "twitter:image"})
            if og_img and og_img.get("content"):
                details["image"] = og_img["content"]

            # Extract Prices using regex patterns
            price_matches = re.findall(r"\$\d+", soup.get_text())
            if len(price_matches) >= 2:
                details["deal_price"] = price_matches[0]
                details["original_price"] = price_matches[1]
            elif len(price_matches) == 1:
                details["deal_price"] = price_matches[0]

    except Exception as e:
        print(f"⚠️ Detail fetch skipped for {clean_url}: {e}")
    
    # Clean fallback domain logo icon
    if not details["image"]:
        tool_slug = clean_url.rstrip("/").split("/")[-1].replace("-", "")
        details["image"] = f"https://www.google.com/s2/favicons?domain={tool_slug}.com&sz=128"

    return details

def fetch_appsumo_deals():
    print("🔍 Deep Scrape: Fetching AppSumo SaaS deals, live prices & images...")
    url = "https://appsumo.com/browse/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    new_deals = []
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            return new_deals

        soup = BeautifulSoup(response.text, "html.parser")
        product_links = soup.find_all("a", href=re.compile(r"/products/"))
        
        seen_urls = set()
        raw_deals = []

        for a in product_links:
            href = a.get("href", "")
            if "#" in href or "reviews" in href.lower() or "/products/" not in href:
                continue

            full_url = href if href.startswith("http") else f"https://appsumo.com{href}"
            clean_url = full_url.split("?")[0]

            if clean_url in seen_urls:
                continue
            
            raw_title = a.get_text(strip=True)
            clean_title = raw_title.replace("View deal:", "").replace("View deal", "").strip()

            if not clean_title or len(clean_title) < 3 or re.search(r"^\d+\s*reviews?", clean_title, re.I):
                continue

            seen_urls.add(clean_url)
            raw_deals.append((clean_title, clean_url))

            if len(raw_deals) >= 20:
                break

        for idx, (title, clean_url) in enumerate(raw_deals, start=1):
            print(f"📦 Processing [{idx}/{len(raw_deals)}]: {title}")
            details = fetch_product_details(clean_url, headers)
            aff_link = wrap_affiliate_link(clean_url)
            
            desc = details["description"] if details["description"] else f"Lifetime access offer to {title} on AppSumo."
            category = categorize_deal(title, desc)

            deal_id = f"deal-appsumo-{re.sub(r'[^a-zA-Z0-9]', '', title).lower()}"

            deal_data = {
                "id": deal_id,
                "title": title,
                "name": title,
                "description": desc,
                "snippet": desc[:110] + "..." if len(desc) > 110 else desc,
                "category": category,
                "tag": category,
                "badge": "🔥 TRENDING NOW" if idx <= 4 else "LIFETIME DEAL",
                "original_price": details["original_price"],
                "old_price": details["original_price"],
                "deal_price": details["deal_price"],
                "price": details["deal_price"],
                "image": details["image"],
                "icon": details["image"],
                "affiliate_url": aff_link,
                "url": aff_link,
                "link": aff_link,
                "network": "AppSumo",
                "rating": "4.9",
                "status": "Active",
                "updated_at": datetime.now().strftime("%Y-%m-%d")
            }
            new_deals.append(deal_data)

    except Exception as e:
        print(f"❌ Error during scraping: {e}")

    return new_deals

def main():
    print("🚀 Running Novacore Scraper Engine with Clean Meta Extraction...")
    fetched_deals = fetch_appsumo_deals()

    if not fetched_deals:
        print("⚠️ No deals fetched.")
        return

    existing_deals = []
    if os.path.exists(DEALS_JSON_PATH):
        try:
            with open(DEALS_JSON_PATH, "r", encoding="utf-8") as f:
                existing_deals = json.load(f)
        except Exception as e:
            print(f"⚠️ Error reading existing deals: {e}")

    deals_dict = {d["id"]: d for d in existing_deals}
    for d in fetched_deals:
        deals_dict[d["id"]] = d

    final_deals = list(deals_dict.values())

    with open(DEALS_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(final_deals, f, indent=2, ensure_ascii=False)

    print(f"✅ Exported total {len(final_deals)} deals (New + Accumulated) to {DEALS_JSON_PATH}!")

if __name__ == "__main__":
    main()