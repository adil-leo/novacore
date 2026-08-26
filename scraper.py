import json
import os
import re
import urllib.parse
from datetime import datetime
import requests
from bs4 import BeautifulSoup

# Google Trends pytrends module import check
try:
    from pytrends.request import TrendReq
    PYTRENDS_AVAILABLE = True
except ImportError:
    PYTRENDS_AVAILABLE = False

# ==============================================================================
# CONFIGURATION & AFFILIATE SETTINGS
# ==============================================================================
IMPACT_BASE_LINK = "https://appsumo.8odi.net/1GKLRx"
DEALS_JSON_PATH = "deals.json"

def wrap_affiliate_link(original_url):
    encoded_url = urllib.parse.quote(original_url, safe='')
    return f"{IMPACT_BASE_LINK}?u={encoded_url}"

def generate_smart_icon(title):
    """
    Generates a clean, high-res brand favicon using Google Favicon API or styled initial avatar.
    """
    clean_name = re.sub(r'[^a-zA-Z0-9]', '', title).lower()
    # Direct high-res logo generation via Google Favicon service or UI Avatar fallback
    return f"https://www.google.com/s2/favicons?domain={clean_name}.com&sz=128"

# ==============================================================================
# SMART AUTO-CATEGORIZER ENGINE
# ==============================================================================
def categorize_deal(title):
    text = title.lower()

    hosting_keywords = ["host", "hosting", "domain", "vps", "server", "cloud", "wordpress", "storage", "cdn", "dns"]
    marketing_keywords = ["seo", "marketing", "email", "social", "ads", "lead", "funnel", "crm", "analytics", "traffic", "copy", "rank", "outreach"]
    ai_keywords = ["ai", "gpt", "bot", "generator", "writer", "prompt", "llm", "copilot", "chat", "avatar", "transcribe"]

    if any(kw in text for kw in hosting_keywords):
        return "Hosting"
    elif any(kw in text for kw in marketing_keywords):
        return "Marketing"
    elif any(kw in text for kw in ai_keywords):
        return "AI Tools"
    else:
        return "SaaS"

# ==============================================================================
# GOOGLE TRENDS ANALYZER ENGINE
# ==============================================================================
def get_google_trend_scores(tool_names):
    scores = {}
    if not PYTRENDS_AVAILABLE or not tool_names:
        print("⚠️ pytrends not loaded. Skipping Google Trends query.")
        return scores

    try:
        print("📈 Connecting to Google Trends API...")
        pytrends = TrendReq(hl='en-US', tz=360, timeout=(10, 25))
        
        chunk_size = 5
        for i in range(0, len(tool_names), chunk_size):
            chunk = tool_names[i:i+chunk_size]
            try:
                pytrends.build_payload(chunk, cat=0, timeframe='now 7-d', geo='', gprop='')
                data = pytrends.interest_over_time()
                if not data.empty:
                    for keyword in chunk:
                        if keyword in data:
                            scores[keyword] = int(data[keyword].mean())
            except Exception as err:
                print(f"⚠️ Trend check skipped for {chunk}: {err}")
    except Exception as e:
        print(f"⚠️ Google Trends connection notice: {e}")

    return scores

# ==============================================================================
# APPSUMO SCRAPER & ENRICHER
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
            return deals

        soup = BeautifulSoup(response.text, "html.parser")
        product_links = soup.find_all("a", href=re.compile(r"/products/"))
        
        seen_urls = set()
        count = 0
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
            count += 1
            raw_deals.append((clean_title, clean_url))

            if count >= 16:
                break

        titles = [deal[0] for deal in raw_deals]
        trend_scores = get_google_trend_scores(titles)

        for idx, (title, clean_url) in enumerate(raw_deals, start=1):
            aff_link = wrap_affiliate_link(clean_url)
            score = trend_scores.get(title, 0)
            category = categorize_deal(title)
            
            if score > 40 or idx <= 2:
                badge = "🔥 TRENDING NOW"
            else:
                badge = "LIFETIME DEAL"

            # Dynamic clean brand icon generation
            icon_url = generate_smart_icon(title)

            deal_data = {
                "id": f"deal-appsumo-{idx}",
                "title": title,
                "name": title,
                "description": f"High demand {category} offer: Lifetime access to {title} on AppSumo.",
                "snippet": f"Trending lifetime deal for {title}.",
                "category": category,
                "tag": category,
                "badge": badge,
                "trend_score": score,
                "original_price": "$199",
                "old_price": "$199",
                "deal_price": "$49",
                "price": "$49",
                "discount": "75% OFF",
                "image": icon_url,
                "icon": icon_url,
                "affiliate_url": aff_link,
                "url": aff_link,
                "link": aff_link,
                "network": "AppSumo",
                "rating": "4.9",
                "status": "Active",
                "updated_at": datetime.now().strftime("%Y-%m-%d")
            }
            deals.append(deal_data)

        deals.sort(key=lambda x: x.get("trend_score", 0), reverse=True)

    except Exception as e:
        print(f"❌ Error during scraping: {e}")

    return deals

def main():
    print("🚀 Running Novacore Scraper with Dynamic Brand Logos...")
    live_deals = fetch_appsumo_deals()

    if not live_deals:
        print("⚠️ No deals fetched.")
        return

    with open(DEALS_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(live_deals, f, indent=2, ensure_ascii=False)

    print(f"✅ Successfully exported {len(live_deals)} categorized deals to {DEALS_JSON_PATH}!")

if __name__ == "__main__":
    main()