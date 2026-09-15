import json
import os
import re
import xml.etree.ElementTree as ET
from xml.dom import minidom
import urllib.parse
from datetime import datetime
import requests
from bs4 import BeautifulSoup

IMPACT_BASE_LINK = "https://appsumo.8odi.net/1GKLRx"
DEALS_JSON_PATH = "deals.json"
SITEMAP_PATH = "sitemap.xml"
SITE_DOMAIN = "https://novacore.deals"

# AppSumo specific category endpoints to guarantee targeted deal scraping
CATEGORY_TARGETS = {
    "Freebies": "https://appsumo.com/browse/?query=free",
    "AI Tools": "https://appsumo.com/browse/?query=ai",
    "SaaS": "https://appsumo.com/browse/?query=software",
    "Marketing": "https://appsumo.com/browse/?query=marketing",
    "Hosting": "https://appsumo.com/browse/?query=hosting",
    "Apps": "https://appsumo.com/browse/?query=app",
    "Downloads": "https://appsumo.com/browse/?query=template"
}

def wrap_affiliate_link(original_url):
    encoded_url = urllib.parse.quote(original_url, safe='')
    return f"{IMPACT_BASE_LINK}?u={encoded_url}"

def categorize_deal(title, description="", target_category=None):
    if target_category:
        return target_category

    text = f"{title} {description}".lower()

    free_keywords = ["free", "freebie", "$0", "zero", "giveaway"]
    ai_keywords = ["ai", "gpt", "bot", "generator", "writer", "prompt", "llm", "copilot", "chat", "avatar", "transcribe", "voice"]
    marketing_keywords = ["seo", "marketing", "email", "social", "ads", "lead", "funnel", "crm", "analytics", "traffic", "copy", "rank", "outreach"]
    hosting_keywords = ["host", "hosting", "domain", "vps", "server", "cloud", "wordpress", "storage", "cdn", "dns"]
    apps_keywords = ["app", "desktop", "mobile", "ios", "android", "windows", "mac", "extension", "plugin", "software tool"]
    downloads_keywords = ["template", "course", "ebook", "pdf", "guide", "vector", "graphic", "asset", "notion", "audio", "font", "bundle", "kit", "sheet"]

    if any(kw in text for kw in free_keywords):
        return "Freebies"
    elif any(kw in text for kw in ai_keywords):
        return "AI Tools"
    elif any(kw in text for kw in marketing_keywords):
        return "Marketing"
    elif any(kw in text for kw in hosting_keywords):
        return "Hosting"
    elif any(kw in text for kw in downloads_keywords):
        return "Downloads"
    elif any(kw in text for kw in apps_keywords):
        return "Apps"
    else:
        return "SaaS"

def generate_reliable_logo(title):
    clean_title = urllib.parse.quote(title.strip())
    return f"https://ui-avatars.com/api/?name={clean_title}&background=0284c7&color=ffffff&bold=true&size=128"

def fetch_product_details(clean_url, headers, title, is_freebie=False):
    details = {
        "deal_price": "$0" if is_freebie else "$49",
        "original_price": "$99" if is_freebie else "$199",
        "description": "",
        "image": generate_reliable_logo(title)
    }
    try:
        res = requests.get(clean_url, headers=headers, timeout=5)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")
            
            meta_desc = soup.find("meta", attrs={"name": "description"}) or soup.find("meta", attrs={"property": "og:description"})
            if meta_desc and meta_desc.get("content"):
                details["description"] = meta_desc["content"].strip()

            og_img = soup.find("meta", attrs={"property": "og:image"}) or soup.find("meta", attrs={"name": "twitter:image"})
            if og_img and og_img.get("content") and "placeholder" not in og_img["content"]:
                details["image"] = og_img["content"]

            price_matches = re.findall(r"\$\d+", soup.get_text())
            if not is_freebie:
                if len(price_matches) >= 2:
                    details["deal_price"] = price_matches[0]
                    details["original_price"] = price_matches[1]
                elif len(price_matches) == 1:
                    details["deal_price"] = price_matches[0]

    except Exception as e:
        print(f"⚠️ Detail fetch skipped for {clean_url}: {e}")

    return details

def fetch_category_deals(cat_name, target_url, headers):
    print(f"🔍 Scraping category target: {cat_name} ...")
    category_deals = []
    try:
        response = requests.get(target_url, headers=headers, timeout=10)
        if response.status_code != 200:
            return category_deals

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

            if len(raw_deals) >= 10:
                break

        for idx, (title, clean_url) in enumerate(raw_deals, start=1):
            print(f" 📦 [{cat_name}] [{idx}/{len(raw_deals)}]: {title}")
            is_freebie = (cat_name == "Freebies")
            details = fetch_product_details(clean_url, headers, title, is_freebie=is_freebie)
            aff_link = wrap_affiliate_link(clean_url)
            
            desc = details["description"] if details["description"] else f"Access {title} for free on AppSumo." if is_freebie else f"Lifetime access offer to {title} on AppSumo."
            assigned_category = categorize_deal(title, desc, target_category=cat_name)

            deal_id = f"deal-appsumo-{re.sub(r'[^a-zA-Z0-9]', '', title).lower()}"

            # Dynamic badge assignment
            if assigned_category == "Freebies":
                badge_text = "🎁 100% FREEBIE"
            elif idx <= 2:
                badge_text = "🔥 TRENDING NOW"
            else:
                badge_text = "LIFETIME DEAL"

            deal_data = {
                "id": deal_id,
                "title": title,
                "name": title,
                "description": desc,
                "snippet": desc[:110] + "..." if len(desc) > 110 else desc,
                "category": assigned_category,
                "tag": assigned_category,
                "badge": badge_text,
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
            category_deals.append(deal_data)

    except Exception as e:
        print(f"❌ Error scraping category {cat_name}: {e}")

    return category_deals

def load_existing_deals():
    if os.path.exists(DEALS_JSON_PATH):
        try:
            with open(DEALS_JSON_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️ Error reading existing deals.json: {e}")
    return []

def merge_deals(existing_deals, newly_scraped_deals):
    deals_map = {deal["id"]: deal for deal in existing_deals}
    for deal in newly_scraped_deals:
        deals_map[deal["id"]] = deal
    return list(deals_map.values())

def generate_sitemap(deals):
    """Automated Sitemap XML Builder for Search Engines"""
    urlset = ET.Element("urlset", xmlns="http://www.sitemaps.org/schemas/sitemap/0.9")
    
    # Root domain entry
    url_elem = ET.SubElement(urlset, "url")
    ET.SubElement(url_elem, "loc").text = f"{SITE_DOMAIN}/"
    ET.SubElement(url_elem, "lastmod").text = datetime.now().strftime("%Y-%m-%d")
    ET.SubElement(url_elem, "changefreq").text = "daily"
    ET.SubElement(url_elem, "priority").text = "1.0"

    # Deal anchors entry
    for deal in deals:
        deal_slug = re.sub(r'[^a-zA-Z0-9]', '-', deal.get("title", "")).lower()
        deal_url = f"{SITE_DOMAIN}/#{deal_slug}"
        
        u_elem = ET.SubElement(urlset, "url")
        ET.SubElement(u_elem, "loc").text = deal_url
        ET.SubElement(u_elem, "lastmod").text = deal.get("updated_at", datetime.now().strftime("%Y-%m-%d"))
        ET.SubElement(u_elem, "changefreq").text = "weekly"
        ET.SubElement(u_elem, "priority").text = "0.8"

    xml_str = minidom.parseString(ET.tostring(urlset)).toprettyxml(indent="  ")
    with open(SITEMAP_PATH, "w", encoding="utf-8") as f:
        f.write(xml_str)
    print(f"🗺️ Generated updated {SITEMAP_PATH} with {len(deals) + 1} URLs!")

def ping_search_engines():
    """IndexNow API ping to notify Bing & Yandex of website updates"""
    try:
        indexnow_url = "https://api.indexnow.org/indexnow"
        payload = {
            "host": "novacore.deals",
            "key": "novacoreindexkey123",
            "keyLocation": f"{SITE_DOMAIN}/novacoreindexkey123.txt",
            "urlList": [f"{SITE_DOMAIN}/"]
        }
        res = requests.post(indexnow_url, json=payload, timeout=5)
        print(f"⚡ IndexNow Ping Status: {res.status_code}")
    except Exception as e:
        print(f"⚠️ IndexNow ping skipped: {e}")

def main():
    print("🚀 Running Novacore Scraper Engine with Per-Category 10-Deal Collector...")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    scraped_batch = []
    for cat_name, cat_url in CATEGORY_TARGETS.items():
        batch = fetch_category_deals(cat_name, cat_url, headers)
        scraped_batch.extend(batch)

    if not scraped_batch:
        print("⚠️ No new deals fetched.")
        return

    existing_deals = load_existing_deals()
    final_deals_list = merge_deals(existing_deals, scraped_batch)

    with open(DEALS_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(final_deals_list, f, indent=2, ensure_ascii=False)

    print(f"✅ Exported successfully! Total Database Size: {len(final_deals_list)} deals in {DEALS_JSON_PATH}!")
    
    # Auto-generate Sitemap & Ping Engine
    generate_sitemap(final_deals_list)
    ping_search_engines()

if __name__ == "__main__":
    main()