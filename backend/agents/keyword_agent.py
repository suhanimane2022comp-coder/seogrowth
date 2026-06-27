import json
from groq import Groq
from core.config import settings

client = Groq(api_key=settings.GROQ_API_KEY)


def run_keyword_agent(state: dict) -> dict:
    """Generate comprehensive keyword research using Groq."""
    business_analysis = state.get("business_analysis", {})

    prompt = f"""
You are an expert SEO keyword researcher.

Generate a comprehensive keyword research report for this business:

Business Name: {state.get('business_name')}
Industry: {business_analysis.get('industry', 'General')}
Services: {', '.join(business_analysis.get('services', []))}
Target Audience: {', '.join(business_analysis.get('target_audience', []))}
Location: {state.get('target_location')}
Business Type: {business_analysis.get('business_type', 'B2C')}

Generate keywords for each category. Return ONLY valid JSON:
{{
  "primary": ["keyword1", "keyword2", "keyword3", "keyword4", "keyword5"],
  "secondary": ["keyword1", "keyword2", "keyword3", "keyword4", "keyword5"],
  "long_tail": ["long tail phrase 1", "long tail phrase 2", "long tail phrase 3", "long tail phrase 4", "long tail phrase 5"],
  "transactional": ["buy keyword", "hire keyword", "get keyword", "best keyword near me", "affordable keyword"],
  "informational": ["how to keyword", "what is keyword", "why keyword", "guide to keyword", "tips for keyword"],
  "local": ["keyword in {state.get('target_location', 'city')}", "best keyword {state.get('target_location', 'city')}", "top keyword near me", "keyword services {state.get('target_location', 'city')}", "local keyword provider"]
}}
"""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.4,
        max_tokens=1500,
    )

    raw = response.choices[0].message.content.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    try:
        keywords = json.loads(raw)
    except Exception:
        services = business_analysis.get('services', ['service'])
        s = services[0] if services else 'service'
        location = state.get('target_location', 'city')
        keywords = {
            "primary": [s, f"best {s}", f"{s} services", f"professional {s}", f"top {s}"],
            "secondary": [f"affordable {s}", f"{s} company", f"{s} provider", f"{s} agency", f"expert {s}"],
            "long_tail": [f"best {s} for small business", f"how to choose {s} provider", f"affordable {s} near me", f"{s} services for beginners", f"professional {s} consultation"],
            "transactional": [f"hire {s}", f"buy {s}", f"get {s} quote", f"book {s}", f"{s} pricing"],
            "informational": [f"what is {s}", f"how does {s} work", f"benefits of {s}", f"{s} guide", f"types of {s}"],
            "local": [f"{s} in {location}", f"best {s} {location}", f"{s} near me", f"top {s} {location}", f"local {s} {location}"]
        }

    state["keywords"] = keywords
    total_keywords = sum(len(v) for v in keywords.values())
    state["total_keywords"] = total_keywords

    return state
