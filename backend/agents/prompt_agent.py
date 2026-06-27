from services.ai_client import ai_json

SEASONAL_OCCASIONS = [
    "Diwali", "Christmas", "New Year", "Valentine's Day", "Summer Sale",
    "Monsoon Season", "Mother's Day", "Independence Day", "Black Friday",
]


def generate_website_prompt(profile: dict, report: dict, keywords: dict, competitors: list) -> dict:
    """Generate a structured 'Lovable' style website + SEO prompt."""
    prompt = f"""
You are a senior conversion copywriter and SEO strategist.

Using the data below, produce a complete website + SEO content brief that can be pasted into an AI website builder (Lovable style).

Business Name: {profile.get('business_name')}
Industry: {profile.get('industry')}
Brand Tone: {profile.get('brand_tone')}
Description: {profile.get('business_description')}
Products/Services: {profile.get('products_services')}
Primary Keywords: {', '.join((keywords or {}).get('primary', [])[:5])}
Secondary Keywords: {', '.join((keywords or {}).get('secondary', [])[:5])}
Long-tail Keywords: {', '.join((keywords or {}).get('long_tail', [])[:5])}
Top Recommendations from latest SEO report: {report.get('recommendations', report) if isinstance(report, dict) else report}
Competitors: {', '.join([c.get('name','') for c in (competitors or [])][:5])}

Return ONLY valid JSON with this exact structure:
{{
  "homepage_structure": {{
    "hero_section": "headline + subheadline + CTA description",
    "about_us": "short about section copy",
    "services": "services section copy outline",
    "features": "features section copy outline",
    "testimonials": "testimonial section guidance",
    "faq": ["faq question 1", "faq question 2", "faq question 3"],
    "contact": "contact section copy"
  }},
  "seo_details": {{
    "h1": "main H1 tag",
    "h2_tags": ["H2 tag 1", "H2 tag 2", "H2 tag 3"],
    "meta_title": "meta title under 60 chars",
    "meta_description": "meta description under 160 chars",
    "cta_text": ["Primary CTA", "Secondary CTA"],
    "internal_links": ["/about", "/services", "/contact"],
    "schema_suggestions": ["LocalBusiness", "FAQPage"],
    "blog_topics": ["blog topic 1", "blog topic 2", "blog topic 3"]
  }},
  "keyword_placement": {{
    "primary_keyword": "main keyword",
    "secondary_keywords": ["keyword1", "keyword2"],
    "long_tail_keywords": ["long tail 1", "long tail 2"]
  }},
  "conversion_suggestions": {{
    "colors": ["#000000", "#FFFFFF"],
    "typography": "font pairing suggestion",
    "cta_buttons": ["Get Started", "Book a Demo"],
    "ux_recommendations": ["recommendation 1", "recommendation 2"]
  }}
}}
"""
    data = ai_json(prompt, temperature=0.5, max_tokens=2200)
    if not data:
        data = {
            "homepage_structure": {
                "hero_section": f"{profile.get('business_name')} - {profile.get('business_description', '')[:120]}",
                "about_us": profile.get("business_description", ""),
                "services": profile.get("products_services", ""),
                "features": "Highlight 3-4 key differentiators.",
                "testimonials": "Showcase 3 customer testimonials with photos.",
                "faq": ["What services do you offer?", "How can I get started?", "What areas do you serve?"],
                "contact": "Add a contact form, phone, email, and map embed.",
            },
            "seo_details": {
                "h1": f"{profile.get('business_name')} | {profile.get('industry', '')}",
                "h2_tags": ["Our Services", "Why Choose Us", "Get In Touch"],
                "meta_title": f"{profile.get('business_name')} - {profile.get('industry', '')}"[:60],
                "meta_description": (profile.get("business_description") or "")[:160],
                "cta_text": ["Get Started", "Contact Us"],
                "internal_links": ["/about", "/services", "/contact"],
                "schema_suggestions": ["LocalBusiness", "Organization", "FAQPage"],
                "blog_topics": ["Industry trends", "How-to guide", "Customer success story"],
            },
            "keyword_placement": {
                "primary_keyword": (keywords or {}).get("primary", ["service"])[0] if (keywords or {}).get("primary") else "service",
                "secondary_keywords": (keywords or {}).get("secondary", [])[:5],
                "long_tail_keywords": (keywords or {}).get("long_tail", [])[:5],
            },
            "conversion_suggestions": {
                "colors": ["#4F46E5", "#F8FAFC"],
                "typography": "Inter for body, Poppins for headings",
                "cta_buttons": ["Get Started", "Book a Free Consultation"],
                "ux_recommendations": ["Sticky CTA on mobile", "Add trust badges above the fold"],
            },
        }
    return data


def generate_seasonal_content(profile: dict, occasions: list = None) -> dict:
    """Generate social captions + image prompts for seasonal occasions."""
    occasions = occasions or SEASONAL_OCCASIONS
    prompt = f"""
You are a social media content strategist and AI image-prompt expert.

Business Name: {profile.get('business_name')}
Industry: {profile.get('industry')}
Brand Tone: {profile.get('brand_tone')}
Products/Services: {profile.get('products_services')}

For EACH of these occasions: {', '.join(occasions)}

Generate social captions for Instagram, Facebook, LinkedIn, and X (Twitter), plus one AI image generation prompt.

Return ONLY valid JSON with this exact structure (keys = occasion names exactly as given):
{{
  "Diwali": {{
    "captions": {{
      "instagram": "caption text with emojis and hashtags",
      "facebook": "caption text",
      "linkedin": "professional caption text",
      "x": "short punchy caption under 280 chars"
    }},
    "image_prompt": "detailed AI image prompt including colors, style, theme, product placement, lighting, composition"
  }}
}}
Repeat this structure for every occasion listed.
"""
    data = ai_json(prompt, temperature=0.6, max_tokens=3500)
    if not data:
        data = {}
        for occ in occasions:
            data[occ] = {
                "captions": {
                    "instagram": f"✨ Celebrate {occ} with {profile.get('business_name')}! Special offers live now. #{occ.replace(' ', '')} #{(profile.get('industry') or '').replace(' ', '')}",
                    "facebook": f"This {occ}, treat yourself with {profile.get('business_name')}. Check out our special collection today!",
                    "linkedin": f"Wishing our community a joyful {occ}. At {profile.get('business_name')}, we're celebrating with our customers and partners.",
                    "x": f"{occ} is here! 🎉 {profile.get('business_name')} has something special for you.",
                },
                "image_prompt": f"A vibrant {occ}-themed product photo for {profile.get('business_name')}, warm festive lighting, brand colors, clean composition, product centered, lifestyle background.",
            }
    return data
