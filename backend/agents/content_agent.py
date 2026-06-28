import json
from groq import Groq
from core.config import settings

client = Groq(api_key=settings.GROQ_API_KEY)


def generate_metadata(state: dict) -> list:
    from urllib.parse import urlparse as _urlparse
    business_analysis = state.get("business_analysis", {})
    keywords = state.get("keywords", {})
    primary_kws = keywords.get("primary", [])[:5]
    secondary_kws = keywords.get("secondary", [])[:3]
    pages = state.get("crawled_pages", [])

    def is_home(url):
        path = _urlparse(url).path.rstrip("/") or "/"
        return path in ("", "/")

    def is_about(url):
        path = _urlparse(url).path.rstrip("/").lower()
        return path in ("/about", "/about-us")

    def is_soft_404(page):
        title = (page.get("title") or "").lower()
        return any(p in title for p in ["not found", "404", "page not found", "error", "oops"])

    home_page = next((p for p in pages if is_home(p.get("url", "")) and not is_soft_404(p)), None)
    about_page = next((p for p in pages if is_about(p.get("url", "")) and not is_soft_404(p)), None)

    target_pages = []
    if home_page:
        target_pages.append(("Home Page", home_page))
    if about_page:
        target_pages.append(("About Page", about_page))

    if not target_pages:
        print("[content_agent] No valid Home/About pages found for metadata generation.")
        return []

    def build_page_context(label, page):
        body_snippet = (page.get("body_text") or "")[:800].strip()
        return (
            "Page: " + label + "\n"
            + "URL: " + str(page.get("url") or "") + "\n"
            + "Current Title: " + str(page.get("title") or "None") + "\n"
            + "Current Meta Description: " + str(page.get("meta_description") or "None") + "\n"
            + "H1: " + str(page.get("h1") or "None") + "\n"
            + "H2s: " + ", ".join(page.get("h2_tags", [])[:5]) + "\n"
            + "Word Count: " + str(page.get("word_count", 0)) + "\n"
            + "Page Content Snippet:\n" + body_snippet
        )

    pages_block = "\n\n---\n\n".join(
        build_page_context(label, page) for label, page in target_pages
    )

    rules = (
        "STRICT RULES:\n"
        "- Title: max 60 chars. Include the most relevant primary keyword naturally. Be specific to the page.\n"
        "- Description: max 155 chars. Include a keyword, describe what the page offers, give the user a reason to click.\n"
        "- NO generic filler: no 'Contact us today', 'commitment to excellence', 'Professional Services', 'Expert services'.\n"
        "- NO location stuffing like 'Serving India (Primary), Global (Secondary)'.\n"
        "- Base everything strictly on the actual page content — do NOT invent services or claims not present.\n"
    )

    prompt = (
        "You are a senior SEO copywriter. Write accurate, keyword-rich meta titles and descriptions.\n\n"
        "Business: " + str(state.get("business_name")) + "\n"
        "Industry: " + str(business_analysis.get("industry", "")) + "\n"
        "Location: " + str(state.get("target_location", "")) + "\n"
        "Primary Keywords: " + ", ".join(primary_kws) + "\n"
        "Secondary Keywords: " + ", ".join(secondary_kws) + "\n\n"
        "PAGES:\n" + pages_block + "\n\n"
        + rules +
        "\nReturn ONLY valid JSON array, no markdown:\n"
        "[{\"page\": \"Home Page\", \"url\": \"...\", \"title\": \"...\", \"description\": \"...\"}]"
    )

    try:
        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=800,
        )
        raw = response.choices[0].message.content.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        return json.loads(raw.strip())
    except Exception as e:
        print(f"[content_agent] generate_metadata failed: {e}")
        fallback = []
        for label, page in target_pages:
            h1 = page.get("h1") or label
            fallback.append({
                "page": label,
                "url": page.get("url", ""),
                "title": (h1[:40] + " | " + str(state.get("business_name", "")))[:60],
                "description": (
                    "Discover " + str(state.get("business_name", ""))
                    + ((" — " + ", ".join(primary_kws[:2])) if primary_kws else "")
                    + ". Based in " + str(state.get("target_location", "")) + "."
                )[:155],
            })
        return fallback

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

    try:
        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
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
        return json.loads(raw)
    except Exception as e:
        print(f"[content_agent] generate_faqs Groq call/parse failed, using fallback: {e}")
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

    try:
        response = client.chat.completions.create(
            model="openai/gpt-oss-20b",
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
        return json.loads(raw)
    except Exception as e:
        print(f"[content_agent] generate_blog_ideas Groq call/parse failed, using fallback: {e}")
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