import json
from groq import Groq
from core.config import settings

client = Groq(api_key=settings.GROQ_API_KEY)


def run_business_agent(state: dict) -> dict:
    """Analyze business information to understand industry, audience, and intent."""
    prompt = f"""
You are an expert SEO strategist and business analyst.

Analyze the following business information and return a structured JSON response.

Business Name: {state.get('business_name')}
Business Description: {state.get('business_description')}
Products/Services: {state.get('products_services')}
Target Audience: {state.get('target_audience')}
Target Location: {state.get('target_location')}

Return ONLY valid JSON with this exact structure:
{{
  "industry": "industry name",
  "target_audience": ["audience segment 1", "audience segment 2"],
  "pain_points": ["pain point 1", "pain point 2", "pain point 3"],
  "services": ["service 1", "service 2", "service 3"],
  "intent": "primary search intent description",
  "unique_value_proposition": "what makes this business unique",
  "local_seo_focus": true or false,
  "business_type": "B2B or B2C or both"
}}
"""
    try:
        response = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=1000,
        )
        raw = response.choices[0].message.content.strip()
        # Clean potential markdown fences
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        raw = raw.strip()
        business_analysis = json.loads(raw)
    except Exception as e:
        print(f"[business_agent] Groq call/parse failed, using fallback: {e}")
        business_analysis = {
            "industry": "General Business",
            "target_audience": [state.get('target_audience', 'General')],
            "pain_points": ["Finding reliable services", "Cost efficiency", "Quality assurance"],
            "services": [state.get('products_services', 'Various services')],
            "intent": "commercial",
            "unique_value_proposition": state.get('business_description', ''),
            "local_seo_focus": bool(state.get('target_location')),
            "business_type": "B2C"
        }

    state["business_analysis"] = business_analysis
    return state