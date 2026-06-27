from datetime import datetime


def get_improvement_plan(state: dict) -> list:
    scores = state.get("seo_scores", {})
    issues = state.get("seo_issues", [])
    content_gaps = state.get("content_gaps", {})
    plan = []

    # Priority 1: Critical issues
    critical = [i for i in issues if i["severity"] == "critical"]
    if critical:
        plan.append({
            "priority": 1,
            "timeframe": "Week 1-2",
            "action": "Fix Critical Technical Issues",
            "tasks": [i["description"] for i in critical[:5]]
        })

    # Priority 2: Content gaps
    missing = content_gaps.get("missing_pages", [])
    if missing:
        plan.append({
            "priority": 2,
            "timeframe": "Week 2-4",
            "action": "Create Missing Pages",
            "tasks": [f"Create {p}" for p in missing[:5]]
        })

    # Priority 3: Keyword optimization
    plan.append({
        "priority": 3,
        "timeframe": "Month 2",
        "action": "Keyword Integration & Content Optimization",
        "tasks": [
            "Integrate primary keywords into page titles and H1s",
            "Add long-tail keywords to blog content",
            "Optimize meta descriptions with target keywords",
            "Create location-specific landing pages",
            "Build internal linking structure"
        ]
    })

    # Priority 4: Content marketing
    blog_ideas = state.get("generated_content", {}).get("blog_ideas", [])
    if blog_ideas:
        plan.append({
            "priority": 4,
            "timeframe": "Month 2-3",
            "action": "Content Marketing",
            "tasks": [f"Publish: {b['title']}" for b in blog_ideas[:4]]
        })

    # Priority 5: Technical improvements
    plan.append({
        "priority": 5,
        "timeframe": "Month 3",
        "action": "Advanced Technical SEO",
        "tasks": [
            "Implement structured data (Schema.org)",
            "Optimize page speed and Core Web Vitals",
            "Add XML sitemap and submit to Google Search Console",
            "Set up Google Analytics 4",
            "Build quality backlinks"
        ]
    })

    return plan


def run_report_agent(state: dict) -> dict:
    """Generate the complete SEO report."""
    scores = state.get("seo_scores", {})
    issues = state.get("seo_issues", [])
    keywords = state.get("keywords", {})
    content_gaps = state.get("content_gaps", {})
    generated_content = state.get("generated_content", {})
    business_analysis = state.get("business_analysis", {})
    pages = state.get("crawled_pages", [])

    improvement_plan = get_improvement_plan(state)

    # Score grade
    overall = scores.get("overall_score", 0)
    if overall >= 80:
        grade = "A"
        grade_label = "Excellent"
    elif overall >= 60:
        grade = "B"
        grade_label = "Good"
    elif overall >= 40:
        grade = "C"
        grade_label = "Average"
    elif overall >= 20:
        grade = "D"
        grade_label = "Poor"
    else:
        grade = "F"
        grade_label = "Critical"

    report = {
        "generated_at": datetime.utcnow().isoformat(),
        "executive_summary": {
            "business_name": state.get("business_name"),
            "overall_score": overall,
            "grade": grade,
            "grade_label": grade_label,
            "pages_analyzed": len(pages),
            "total_issues": state.get("total_issues", 0),
            "critical_issues": state.get("critical_issues", 0),
            "keyword_opportunities": state.get("total_keywords", 0),
            "summary": f"{state.get('business_name')} received an SEO score of {overall}/100 ({grade_label}). "
                       f"We found {state.get('total_issues', 0)} issues across {len(pages)} pages analyzed, "
                       f"with {state.get('critical_issues', 0)} critical issues requiring immediate attention. "
                       f"We identified {state.get('total_keywords', 0)} keyword opportunities and "
                       f"{len(content_gaps.get('missing_pages', []))} missing page opportunities."
        },
        "business_overview": business_analysis,
        "seo_scores": scores,
        "technical_seo": {
            "robots_txt": state.get("robots_txt", {}),
            "sitemap": state.get("sitemap", {}),
            "pages_crawled": len(pages),
            "issues": issues
        },
        "keyword_opportunities": keywords,
        "content_gaps": content_gaps,
        "generated_content": generated_content,
        "improvement_plan": improvement_plan,
        "pages_summary": [
            {
                "url": p["url"],
                "title": p.get("title"),
                "word_count": p.get("word_count", 0),
                "issues_count": len(p.get("issues", []))
            }
            for p in pages[:20]
        ]
    }

    state["report"] = report
    return state
