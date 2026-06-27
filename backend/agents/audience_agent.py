from services.ai_client import ai_json


def generate_audience_persona(profile: dict) -> dict:
    prompt = f"""
You are an expert market researcher and audience strategist.

Based on this business profile, generate a detailed target audience persona.

Business Name: {profile.get('business_name')}
Industry: {profile.get('industry')}
Business Type: {profile.get('business_type')}
Description: {profile.get('business_description')}
Products/Services: {profile.get('products_services')}
Target Location: {profile.get('target_location')}
Keywords: {', '.join(profile.get('keywords') or [])}
Brand Tone: {profile.get('brand_tone')}

Return ONLY valid JSON with this exact structure:
{{
  "age_group": "e.g. 25-40",
  "gender_distribution": {{"male": 45, "female": 55}},
  "interests": ["interest 1", "interest 2", "interest 3", "interest 4"],
  "occupation": ["occupation 1", "occupation 2", "occupation 3"],
  "pain_points": ["pain point 1", "pain point 2", "pain point 3"],
  "buying_behavior": "short description of how this audience makes purchase decisions",
  "preferred_platforms": ["Instagram", "YouTube"],
  "content_preferences": ["short videos", "carousels", "blogs"]
}}
"""
    data = ai_json(prompt, temperature=0.4, max_tokens=900)
    if not data:
        data = {
            "age_group": "25-40",
            "gender_distribution": {"male": 50, "female": 50},
            "interests": ["Quality products", "Value for money", "Trends"],
            "occupation": ["Working professionals", "Entrepreneurs"],
            "pain_points": ["Finding a trustworthy provider", "Price comparison", "Lack of information"],
            "buying_behavior": "Researches online, compares reviews, and prefers brands with social proof.",
            "preferred_platforms": ["Instagram", "Facebook"],
            "content_preferences": ["short videos", "infographics"],
        }
    return data
