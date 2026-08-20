import json

deals = [
    {
        "title": "AI Content Suite",
        "badge": "LIFETIME DEAL",
        "description": "Automate your content creation pipeline with advanced multi-model AI workflows.",
        "price": "$49",
        "old_price": "$299",
        "link": "https://appsumo.com"
    },
    {
        "title": "Cloud Analytics Pro",
        "badge": "85% OFF",
        "description": "Privacy-first web analytics built for modern SaaS applications and e-commerce.",
        "price": "$29",
        "old_price": "$199",
        "link": "https://partnerstack.com"
    },
    {
        "title": "SEO Rank Tracker",
        "badge": "FEATURED",
        "description": "Monitor keyword trends and analyze competitors in real-time with automated reporting.",
        "price": "$39",
        "old_price": "$149",
        "link": "https://impact.com"
    }
]

def save_deals():
    with open("deals.json", "w", encoding="utf-8") as f:
        json.dump(deals, f, indent=2)
    print("Deals processed and saved to deals.json successfully!")

if __name__ == "__main__":
    save_deals()