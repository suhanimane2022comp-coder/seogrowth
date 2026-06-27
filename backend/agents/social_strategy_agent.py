import calendar as cal
from datetime import date
from services.ai_client import ai_json

ALL_PLATFORMS = ["Instagram", "Facebook", "LinkedIn", "Pinterest", "X", "YouTube", "Threads"]


def determine_platform_priority(profile: dict, audience: dict, selected_platforms: list) -> list:
    prompt = f"""
You are a social media strategist.

Business Type: {profile.get('business_type')}
Industry: {profile.get('industry')}
Audience Age Group: {(audience or {}).get('age_group')}
Audience Interests: {', '.join((audience or {}).get('interests', []))}
Platforms the user wants to use: {', '.join(selected_platforms)}

Rank these platforms by priority for this specific business (highest weight = most important).

Return ONLY a valid JSON array:
[
  {{"platform": "Instagram", "weight": 90, "reason": "short reason"}},
  ...
]
Include every platform from the user's list, weight from 0-100.
"""
    data = ai_json(prompt, temperature=0.4, max_tokens=900)
    if isinstance(data, dict):
        data = data.get("platforms") or data.get("priority") or []
    if not data or not isinstance(data, list):
        btype = (profile.get("business_type") or "").lower()
        industry = (profile.get("industry") or "").lower()
        default_weights = {p: 50 for p in selected_platforms}
        if "saas" in btype or "b2b" in industry or "agency" in btype:
            default_weights.update({"LinkedIn": 90, "X": 70})
        if "fashion" in industry or "ecommerce" in btype:
            default_weights.update({"Instagram": 90, "Pinterest": 80})
        if "skincare" in industry or "beauty" in industry or "health" in industry:
            default_weights.update({"Instagram": 90, "YouTube": 75})
        data = [
            {"platform": p, "weight": default_weights.get(p, 50), "reason": "Estimated priority based on industry and business type."}
            for p in selected_platforms
        ]
        data.sort(key=lambda x: -x["weight"])
    return data


POST_TYPES = ["Reel/Short Video", "Carousel", "Image Post", "Story", "Blog Share", "Infographic"]


def generate_content_calendar(profile: dict, audience: dict, platforms: list, month: str) -> dict:
    """Generate a lightweight monthly calendar (AI for first week's worth of captions, templated rotation for the rest to control token usage)."""
    try:
        year, mon = [int(x) for x in month.split("-")]
    except Exception:
        today = date.today()
        year, mon = today.year, today.month
        month = f"{year}-{mon:02d}"

    days_in_month = cal.monthrange(year, mon)[1]

    prompt = f"""
You are a social media content planner.

Business: {profile.get('business_name')} ({profile.get('industry')})
Brand Tone: {profile.get('brand_tone')}
Audience: {(audience or {}).get('age_group')}, interests: {', '.join((audience or {}).get('interests', [])[:4])}
Platforms: {', '.join(platforms)}

Generate 7 sample daily content ideas to seed a monthly calendar rotation. Return ONLY a valid JSON array of exactly 7 items:
[
  {{
    "platform": "Instagram",
    "post_type": "Reel/Short Video",
    "caption": "engaging caption text",
    "hashtags": ["#tag1", "#tag2", "#tag3"],
    "cta": "Shop Now"
  }}
]
"""
    seed = ai_json(prompt, temperature=0.6, max_tokens=1800)
    if isinstance(seed, dict):
        seed = seed.get("posts") or list(seed.values())[0] if seed else []
    if not seed or not isinstance(seed, list):
        seed = [
            {
                "platform": platforms[i % len(platforms)],
                "post_type": POST_TYPES[i % len(POST_TYPES)],
                "caption": f"Discover what makes {profile.get('business_name')} special. #{(profile.get('industry') or 'business').replace(' ', '')}",
                "hashtags": [f"#{(profile.get('industry') or 'business').replace(' ', '')}", "#growth", "#newpost"],
                "cta": "Learn More",
            }
            for i in range(7)
        ]

    posts = []
    for day in range(1, days_in_month + 1):
        template = seed[(day - 1) % len(seed)]
        posts.append({
            "date": f"{year}-{mon:02d}-{day:02d}",
            "platform": template.get("platform", platforms[0] if platforms else "Instagram"),
            "post_type": template.get("post_type", "Image Post"),
            "caption": template.get("caption", ""),
            "hashtags": template.get("hashtags", []),
            "cta": template.get("cta", "Learn More"),
        })

    return {"month": month, "posts": posts}


def generate_prime_times(profile: dict, audience: dict, platforms: list) -> list:
    prompt = f"""
You are a social media analytics expert.

Audience Age Group: {(audience or {}).get('age_group')}
Region/Location: {profile.get('target_location')}
Industry: {profile.get('industry')}
Platforms: {', '.join(platforms)}

For each day of the week (Monday-Sunday) and each platform, suggest the single best posting time.

Return ONLY a valid JSON array:
[
  {{"day": "Monday", "platform": "Instagram", "best_time": "7:00 PM"}}
]
"""
    data = ai_json(prompt, temperature=0.3, max_tokens=1800)
    if isinstance(data, dict):
        data = data.get("schedule") or list(data.values())[0] if data else []
    if not data or not isinstance(data, list):
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        default_times = {
            "Instagram": "7:00 PM", "Facebook": "1:00 PM", "LinkedIn": "10:00 AM",
            "Pinterest": "8:00 PM", "X": "12:00 PM", "YouTube": "6:00 PM", "Threads": "9:00 AM",
        }
        data = [{"day": d, "platform": p, "best_time": default_times.get(p, "6:00 PM")} for d in days for p in platforms]
    return data


def generate_engagement_suggestions(profile: dict, audience: dict) -> list:
    content_prefs = (audience or {}).get("content_preferences", [])
    base = [
        {"type": "Blogging", "priority_score": 70},
        {"type": "Short videos", "priority_score": 90},
        {"type": "Reels", "priority_score": 92},
        {"type": "Stories", "priority_score": 80},
        {"type": "Infographics", "priority_score": 65},
        {"type": "Email marketing", "priority_score": 60},
        {"type": "YouTube Shorts", "priority_score": 75},
    ]
    for item in base:
        if any(item["type"].lower() in pref.lower() or pref.lower() in item["type"].lower() for pref in content_prefs):
            item["priority_score"] = min(100, item["priority_score"] + 10)
    base.sort(key=lambda x: -x["priority_score"])
    return base
