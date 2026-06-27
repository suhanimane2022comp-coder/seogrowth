from services.ai_client import ai_json


def find_competitors(profile: dict) -> list:
    prompt = f"""
You are a competitive market intelligence analyst.

Identify 4-6 real, well-known competitors for this business based on its industry and location.

Business Name: {profile.get('business_name')}
Industry: {profile.get('industry')}
Business Type: {profile.get('business_type')}
Description: {profile.get('business_description')}
Products/Services: {profile.get('products_services')}
Target Location: {profile.get('target_location')}

Return ONLY a valid JSON array, each item with this exact structure:
[
  {{
    "name": "Competitor Name",
    "website_url": "https://competitor.com",
    "category": "category name",
    "domain_authority": "High/Medium/Low or a number estimate",
    "relevance_reason": "why this competitor is relevant, 1-2 sentences"
  }}
]
"""
    data = ai_json(prompt, temperature=0.4, max_tokens=1200)
    if isinstance(data, dict):
        data = data.get("competitors", []) or list(data.values())[0] if data else []
    if not data or not isinstance(data, list):
        industry = (profile.get("industry") or "").lower()
        if "skincare" in industry or "beauty" in industry or "cosmetic" in industry:
            data = [
                {"name": "Nykaa", "website_url": "https://www.nykaa.com", "category": "Beauty & Skincare", "domain_authority": "High", "relevance_reason": "Leading beauty e-commerce platform in the same market."},
                {"name": "Purplle", "website_url": "https://www.purplle.com", "category": "Beauty & Skincare", "domain_authority": "Medium", "relevance_reason": "Direct competitor in the online beauty retail space."},
                {"name": "Mamaearth", "website_url": "https://mamaearth.in", "category": "Natural Skincare", "domain_authority": "High", "relevance_reason": "Popular natural skincare brand targeting a similar audience."},
            ]
        elif "fitness" in industry or "health" in industry:
            data = [
                {"name": "Cult.fit", "website_url": "https://www.cult.fit", "category": "Fitness", "domain_authority": "High", "relevance_reason": "Major fitness brand with strong digital presence."},
                {"name": "HealthKart", "website_url": "https://www.healthkart.com", "category": "Health & Nutrition", "domain_authority": "High", "relevance_reason": "Competing in health and nutrition products."},
                {"name": "Decathlon", "website_url": "https://www.decathlon.in", "category": "Sports & Fitness", "domain_authority": "High", "relevance_reason": "Strong presence in fitness equipment and apparel."},
            ]
        elif "fashion" in industry or "apparel" in industry or "clothing" in industry:
            data = [
                {"name": "Myntra", "website_url": "https://www.myntra.com", "category": "Fashion E-commerce", "domain_authority": "High", "relevance_reason": "Largest fashion e-commerce competitor."},
                {"name": "Ajio", "website_url": "https://www.ajio.com", "category": "Fashion E-commerce", "domain_authority": "High", "relevance_reason": "Direct competitor in online fashion retail."},
                {"name": "Zara", "website_url": "https://www.zara.com", "category": "Fashion Retail", "domain_authority": "High", "relevance_reason": "Global fashion brand competing on style and pricing."},
            ]
        else:
            biz = profile.get("business_name", "your business")
            data = [
                {"name": f"Top {profile.get('industry', 'Industry')} Brand A", "website_url": "https://example.com", "category": profile.get("industry", "General"), "domain_authority": "Medium", "relevance_reason": f"A leading player in the same industry as {biz}."},
                {"name": f"Top {profile.get('industry', 'Industry')} Brand B", "website_url": "https://example.com", "category": profile.get("industry", "General"), "domain_authority": "Medium", "relevance_reason": "Targets a similar audience and keyword set."},
            ]
    return data
