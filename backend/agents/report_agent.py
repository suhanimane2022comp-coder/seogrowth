from datetime import datetime


def get_improvement_plan(state: dict) -> list:
    scores = state.get("seo_scores", {})
    issues = state.get("seo_issues", [])
    content_gaps = state.get("content_gaps", {})
    plan = []

    # Priority 1: Critical issues
    # NOTE: issue dicts from score_agent.build_seo_issues() use the key
    # "issue" (e.g. "thin_content:429_words"), not "description" — that key
    # never existed, so this previously failed silently: critical issues
    # would only ever show up here if any existed AND the key matched, and
    # since most real-world issues are "warning" severity, this block was
    # rarely even reached. Using "issue" (falling back to "issue_key", then
    # a placeholder) so a real list always renders instead of an empty bullet.
    critical = [i for i in issues if i.get("severity") == "critical"]
    if critical:
        # audit_agent.py now always populates "description" (human-readable)
        # alongside "issue" (raw key, e.g. "thin_content:294_words") for
        # every entry, so prefer description for plan tasks -- it reads as
        # "Page is missing a meta description." instead of the raw key, and
        # includes which URL it's about where relevant.
        plan.append({
            "priority": 1,
            "timeframe": "Week 1-2",
            "action": "Fix Critical Technical Issues",
            "tasks": [
                f"{i.get('description') or i.get('issue') or i.get('issue_key') or 'Unspecified issue'}"
                f"{' (' + i['url'] + ')' if i.get('url') else ''}"
                for i in critical[:5]
            ]
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

    # Count unique issue types (not per-page occurrences).
    # e.g. "missing_canonical" on 11 pages = 1 unique issue, not 11.
    unique_issue_types = set(i.get("issue_type", i.get("issue_key", "")) for i in issues)
    total_issues = len(unique_issue_types)
    critical_issues_count = len(
        set(i.get("issue_type", i.get("issue_key", ""))
            for i in issues if i.get("severity") == "critical")
    )

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
            "total_issues": total_issues,
            "critical_issues": critical_issues_count,
            "keyword_opportunities": state.get("total_keywords", 0),
            "summary": f"{state.get('business_name')} received an SEO score of {overall}/100 ({grade_label}). "
                       f"We found {total_issues} issues across {len(pages)} pages analyzed, "
                       f"with {critical_issues_count} critical issues requiring immediate attention. "
                       f"We identified {state.get('total_keywords', 0)} keyword opportunities and "
                       f"{len(content_gaps.get('missing_pages', []))} missing page opportunities."
        },
        "business_overview": business_analysis,
        "seo_scores": scores,
        "technical_seo": {
            "robots_txt": state.get("robots_txt", {}),
            "sitemap": state.get("sitemap", {}),
            "llms_txt": state.get("llms_txt", {}),
            "https_redirect": state.get("https_redirect", {}),
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