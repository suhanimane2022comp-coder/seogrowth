import json
from groq import Groq
from core.config import settings

client = Groq(api_key=settings.GROQ_API_KEY)


def generate_metadata(state: dict) -> list:
    business_analysis = state.get("business_analysis", {})
    keywords = state.get("keywords", {})
    primary_kws = keywords.get("primary", [])[:3]

    prompt = f"""
You are an expert SEO copywriter.

Generate SEO metadata for these pages for {state.get('business_name')}:
- Home Page
- About Page  
- Services Page
- Contact Page
- {state.get('target_location', '')} Landing Page

Business: {state.get('business_name')}
Industry: {business_analysis.get('industry')}
Primary Keywords: {', '.join(primary_kws)}
Location: {state.get('target_location')}

Return ONLY valid JSON array:
[
  {{
    "page": "Home Page",
    "title": "SEO optimized title under 60 chars",
    "description": "Compelling meta description under 155 chars"
  }}
]
"""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.5,
        max_tokens=1000,
    )

    raw = response.choices[0].message.content.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    try:
        return json.loads(raw)
    except Exception:
        return [
            {"page": "Home Page", "title": f"{state.get('business_name')} | Professional Services", "description": f"Expert services by {state.get('business_name')}. Serving {state.get('target_location')}. Contact us today!"},
            {"page": "About Page", "title": f"About {state.get('business_name')} | Our Story", "description": f"Learn about {state.get('business_name')} and our commitment to excellence."},
        ]


def generate_faqs(state: dict) -> list:
    business_analysis = state.get("business_analysis", {})
    content_gaps = state.get("content_gaps", {})

    prompt = f"""
You are an expert content writer specializing in SEO-optimized FAQ content.

Generate 8 detailed FAQs for {state.get('business_name')}.

Business: {state.get('business_name')}
Industry: {business_analysis.get('industry')}
Services: {', '.join(business_analysis.get('services', []))}
Pain Points: {', '.join(business_analysis.get('pain_points', []))}
Location: {state.get('target_location')}

FAQ topics to cover: {', '.join(content_gaps.get('missing_faqs', [])[:5])}

Return ONLY valid JSON array:
[
  {{
    "question": "Clear question a customer would ask?",
    "answer": "Detailed, helpful answer in 2-3 sentences that naturally includes keywords."
  }}
]
"""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.5,
        max_tokens=2000,
    )

    raw = response.choices[0].message.content.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    try:
        return json.loads(raw)
    except Exception:
        return [
            {"question": "What services do you offer?", "answer": f"{state.get('business_name')} offers a range of professional services tailored to your needs."},
            {"question": "Where are you located?", "answer": f"We proudly serve clients in {state.get('target_location')} and surrounding areas."},
        ]


def generate_blog_ideas(state: dict) -> list:
    business_analysis = state.get("business_analysis", {})
    keywords = state.get("keywords", {})

    prompt = f"""
You are an expert SEO content strategist.

Generate 6 blog post ideas for {state.get('business_name')}.

Industry: {business_analysis.get('industry')}
Services: {', '.join(business_analysis.get('services', []))}
Informational Keywords: {', '.join(keywords.get('informational', [])[:5])}
Target Audience: {', '.join(business_analysis.get('target_audience', []))}

Return ONLY valid JSON array:
[
  {{
    "title": "Compelling blog post title",
    "outline": "Brief 2-3 sentence description of the blog post content and angle",
    "target_keyword": "main keyword to target"
  }}
]
"""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.6,
        max_tokens=1500,
    )

    raw = response.choices[0].message.content.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    try:
        return json.loads(raw)
    except Exception:
        return [
            {"title": "10 Tips for Better Results", "outline": "A comprehensive guide helping your audience achieve better outcomes.", "target_keyword": "tips guide"},
            {"title": "Why Choose Professional Services", "outline": "Explains the value of professional expertise.", "target_keyword": "professional services"},
        ]


def generate_ctas(state: dict) -> list:
    business_name = state.get("business_name")
    location = state.get("target_location")
    return [
        {"type": "hero", "text": f"Get Your Free Consultation Today", "subtext": f"Serving {location} and beyond"},
        {"type": "contact", "text": "Book a Free Strategy Call", "subtext": "No commitment required"},
        {"type": "service", "text": "View Our Packages", "subtext": "Transparent pricing, no hidden fees"},
        {"type": "social_proof", "text": "Join 100+ Happy Clients", "subtext": f"Trusted by businesses in {location}"},
    ]


def run_content_agent(state: dict) -> dict:
    """Generate all SEO content."""
    metadata = generate_metadata(state)
    faqs = generate_faqs(state)
    blog_ideas = generate_blog_ideas(state)
    ctas = generate_ctas(state)

    state["generated_content"] = {
        "metadata": metadata,
        "faqs": faqs,
        "blog_ideas": blog_ideas,
        "ctas": ctas,
        "schema_suggestions": [
            "LocalBusiness schema for homepage",
            "Service schema for each service page",
            "FAQPage schema for FAQ section",
            "BreadcrumbList for navigation",
            "Review/AggregateRating for testimonials"
        ],
        "internal_linking_suggestions": [
            "Link from blog posts to relevant service pages",
            "Add 'Related Services' section on each service page",
            "Link footer to all main service pages",
            "Add breadcrumbs to all inner pages",
            "Create a sitemap page for users"
        ]
    }

    return state
