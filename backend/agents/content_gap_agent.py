import json
import re
from groq import Groq
from core.config import settings

client = Groq(api_key=settings.GROQ_API_KEY)

# Maps a "missing page" category name to keywords we'd expect to see in a URL
# path, link, or title if that page actually exists on the site.
PAGE_KEYWORD_MAP = {
    "contact": ["contact", "get-in-touch", "reach-us", "reach us"],
    "about": ["about", "our-story", "who-we-are"],
    "faq": ["faq", "frequently-asked", "help"],
    "pricing": ["pricing", "plans", "packages"],
    "testimonial": ["testimonial", "review", "case-stud"],
    "service": ["service", "what-we-do", "solutions"],
    "blog": ["blog", "articles", "news", "insights"],
    "privacy": ["privacy"],
    "terms": ["terms", "tos"],
    "team": ["team", "our-team", "staff"],
    "career": ["career", "jobs", "hiring"],
    "portfolio": ["portfolio", "our-work", "projects"],
}


EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
PHONE_RE = re.compile(r"(\+?\d[\d\-\s().]{7,}\d)")


def _page_exists(page_name: str, signals: list, body_texts: list = None) -> bool:
    """Best-effort check for whether a 'missing' page actually already exists,
    using URLs/titles/links/body text discovered during crawling (not just the AI's guess)."""
    name = page_name.lower()
    matched_keywords = []
    for category, keywords in PAGE_KEYWORD_MAP.items():
        if category in name:
            matched_keywords = keywords
            break
    if not matched_keywords:
        # fall back to using the page name itself (minus generic words) as the keyword
        cleaned = re.sub(r"\b(page|section)\b", "", name).strip()
        matched_keywords = [cleaned] if cleaned else []

    for signal in signals:
        signal_lower = (signal or "").lower()
        if any(kw in signal_lower for kw in matched_keywords if kw):
            return True

    # "Contact" is satisfied not just by the word itself, but by an actual
    # email address or phone number visible on the page.
    if "contact" in name and body_texts:
        for text in body_texts:
            if not text:
                continue
            if EMAIL_RE.search(text) or PHONE_RE.search(text):
                return True

    return False


def run_content_gap_agent(state: dict) -> dict:
    """Identify missing content opportunities."""
    crawled_pages = state.get("crawled_pages", [])
    business_analysis = state.get("business_analysis", {})
    existing_urls = [p["url"] for p in crawled_pages]
    existing_titles = [p.get("title", "") for p in crawled_pages if p.get("title")]

    # Gather every signal we have that a page/section already exists: crawled
    # page URLs/titles, plus every internal link discovered on those pages
    # (covers cases where the crawler only fetched the homepage but the page
    # links to /contact, /about, etc. — or to same-page anchors like #contact).
    existing_signals = list(existing_urls) + list(existing_titles)
    body_texts = []
    for p in crawled_pages:
        existing_signals.extend(p.get("internal_links", []) or [])
        existing_signals.extend(p.get("h2_tags", []) or [])
        existing_signals.extend(p.get("h3_tags", []) or [])
        if p.get("body_text"):
            body_texts.append(p["body_text"])

    prompt = f"""
You are an expert SEO content strategist.

Analyze the content gaps for this business:

Business: {state.get('business_name')}
Industry: {business_analysis.get('industry')}
Services: {', '.join(business_analysis.get('services', []))}
Target Audience: {', '.join(business_analysis.get('target_audience', []))}
Location: {state.get('target_location')}
Pain Points: {', '.join(business_analysis.get('pain_points', []))}

Existing pages found: {', '.join(existing_titles[:10]) if existing_titles else 'No website provided'}
Existing internal links found: {', '.join(existing_urls[:15])}
Competitor URLs: {', '.join(state.get('competitor_urls', []))}

Only list a page under "missing_pages" if there is no reasonable evidence it already
exists among the existing pages/links above. Do not guess that common pages like
Contact, About, or FAQ are missing if a link or title already suggests they exist.

Identify content gaps and return ONLY valid JSON:
{{
  "missing_pages": ["Page Name 1", "Page Name 2", "Page Name 3", "Page Name 4", "Page Name 5"],
  "missing_topics": ["Topic 1", "Topic 2", "Topic 3", "Topic 4", "Topic 5"],
  "missing_faqs": ["FAQ topic 1", "FAQ topic 2", "FAQ topic 3", "FAQ topic 4", "FAQ topic 5"],
  "missing_services": ["Service page 1", "Service page 2", "Service page 3"],
  "missing_landing_pages": ["Landing page 1", "Landing page 2", "Landing page 3"]
}}
"""

    try:
        response = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4,
            max_tokens=1000,
        )
        raw = response.choices[0].message.content.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        raw = raw.strip()
        content_gaps = json.loads(raw)
    except Exception as e:
        print(f"[content_gap_agent] Groq call/parse failed, using fallback: {e}")
        content_gaps = {
            "missing_pages": ["Pricing Page", "FAQ Page", "Case Studies", "Testimonials", "Contact Page"],
            "missing_topics": ["How we work", "Our process", "Industry insights", "Success stories", "Team page"],
            "missing_faqs": ["How much does it cost?", "How long does it take?", "What areas do you serve?", "Do you offer guarantees?", "How do I get started?"],
            "missing_services": ["Service detail pages", "Package comparison", "Custom solutions"],
            "missing_landing_pages": ["Location-specific landing page", "Campaign landing page", "Free consultation page"]
        }

    # Deterministic safety net: drop any "missing" page the AI suggested if we
    # actually have evidence (a link, URL path, or heading) that it exists.
    if existing_signals or body_texts:
        content_gaps["missing_pages"] = [
            p for p in content_gaps.get("missing_pages", []) if not _page_exists(p, existing_signals, body_texts)
        ]
        content_gaps["missing_services"] = [
            p for p in content_gaps.get("missing_services", []) if not _page_exists(p, existing_signals, body_texts)
        ]

    state["content_gaps"] = content_gaps
    return state