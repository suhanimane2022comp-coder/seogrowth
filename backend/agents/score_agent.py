from typing import List


def _issue_key(issue: str) -> str:
    """Issues are sometimes flat ('missing_h1') and sometimes carry a detail
    suffix ('multiple_h1:3_found', 'poor_lcp:19.5s'). Split on the first
    colon to get the lookup key either way."""
    return issue.split(":")[0] if isinstance(issue, str) else str(issue)


ISSUE_SEVERITY = {
    "missing_title": "critical",
    "missing_meta_description": "warning",
    "missing_h1": "critical",
    "multiple_h1": "warning",
    "missing_alt_text": "warning",
    "thin_content": "warning",
    "missing_canonical": "warning",
    "missing_viewport_meta": "warning",
    "missing_llms_txt": "info",
    "high_js_rendering_dependency": "warning",
    "page_too_large": "warning",
    "poor_lcp": "critical",
    "poor_tti": "warning",
    "unoptimized_images": "warning",
    "outdated_http_protocol": "info",
}


def build_seo_issues(pages: List[dict]) -> List[dict]:
    """
    Converts each page's flat `issues` list (written by crawler_agent.py and
    performance_agent.py) into the structured {url, issue, severity} records
    the rest of scoring expects. This is the fix for the original bug:
    state["seo_issues"] was never populated from crawled_pages, so technical_score
    always deducted zero points regardless of what the crawler found.
    """
    structured = []
    for page in pages:
        for issue in page.get("issues", []):
            key = _issue_key(issue)
            structured.append({
                "url": page.get("url"),
                "issue": issue,
                "issue_key": key,
                "severity": ISSUE_SEVERITY.get(key, "warning"),
            })
    return structured


def run_score_agent(state: dict) -> dict:
    """Calculate comprehensive SEO scores."""
    pages = state.get("crawled_pages", [])

    issues = state.get("seo_issues")
    if not issues:
        issues = build_seo_issues(pages)
        state["seo_issues"] = issues

    keywords = state.get("keywords", {})
    content = state.get("generated_content", {})

    # ---------------- Technical SEO Score (0-100) ----------------
    technical_score = 100.0
    has_website = bool(state.get("website_url"))

    if not has_website:
        technical_score = 30
    else:
        # Performance-category issues (poor_lcp, page_too_large, etc.) are
        # scored exclusively by performance_score below — counting them here
        # too would double-penalize the same problem in two categories and
        # drag technical_score down for reasons that have nothing to do with
        # technical SEO fundamentals (title/H1/canonical/robots/sitemap).
        performance_keys = {"page_too_large", "poor_lcp", "poor_tti", "unoptimized_images",
                             "outdated_http_protocol", "high_js_rendering_dependency", "missing_llms_txt"}
        technical_issues = [i for i in issues if i["issue_key"] not in performance_keys]
        critical_issues = [i for i in technical_issues if i["severity"] == "critical"]
        warning_issues = [i for i in technical_issues if i["severity"] == "warning"]
        technical_score -= len(critical_issues) * 10
        technical_score -= len(warning_issues) * 5

        if not state.get("robots_txt", {}).get("exists"):
            technical_score -= 10
        if not state.get("sitemap", {}).get("exists"):
            technical_score -= 10

        technical_score = max(0, min(100, technical_score))

    # ---------------- Content Score (0-100) ----------------
    # Reads directly from page["issues"] (thin_content, multiple_h1,
    # missing_alt_text, missing_h1) instead of recomputing a narrower,
    # blind word_count/h1-truthiness check that couldn't see multiple H1s.
    content_score = 50.0
    if pages:
        content_issue_keys = {"thin_content", "multiple_h1", "missing_alt_text", "missing_h1"}
        pages_with_content_issues = [
            p for p in pages
            if any(_issue_key(i) in content_issue_keys for i in p.get("issues", []))
        ]
        pages_with_title = [p for p in pages if p.get("title")]

        clean_content_ratio = 1 - (len(pages_with_content_issues) / len(pages))
        title_ratio = len(pages_with_title) / len(pages)

        content_score = (clean_content_ratio * 70) + (title_ratio * 30)
        content_score = max(0, min(100, content_score))
    elif content.get("faqs") and content.get("blog_ideas"):
        content_score = 60

    # ---------------- Keyword Score (0-100) ----------------
    total_keywords = state.get("total_keywords", 0)
    keyword_score = min(100, (total_keywords / 30) * 100)

    # ---------------- Metadata Score (0-100) ----------------
    metadata_score = 50.0
    if pages:
        pages_with_meta = [p for p in pages if p.get("meta_description")]
        pages_with_canonical = [p for p in pages if p.get("canonical")]
        pages_with_clean_h1 = [
            p for p in pages
            if not any(_issue_key(i) == "multiple_h1" for i in p.get("issues", []))
        ]
        meta_ratio = len(pages_with_meta) / len(pages)
        canonical_ratio = len(pages_with_canonical) / len(pages)
        h1_structure_ratio = len(pages_with_clean_h1) / len(pages)
        metadata_score = (meta_ratio * 40) + (canonical_ratio * 30) + (h1_structure_ratio * 30)
        metadata_score = max(0, min(100, metadata_score))
    elif content.get("metadata"):
        metadata_score = 70

    # ---------------- Performance Score (0-100) ----------------
    # Now wired to real data: performance_agent.py populates page["performance"]
    # and page["issues"] with poor_lcp / page_too_large / unoptimized_images /
    # outdated_http_protocol when it runs. If that agent hasn't run yet for
    # this report, this stays None (not measured) rather than silently
    # defaulting to 100 — which is the exact bug being fixed here.
    performance_score = None
    pages_with_perf = [p for p in pages if p.get("performance")]
    if pages_with_perf:
        per_page_scores = []
        for p in pages_with_perf:
            page_perf_score = 100.0
            for issue in p.get("issues", []):
                key = _issue_key(issue)
                # Weights calibrated so a page with the issues HOTH flagged for
                # Indmark (poor LCP, oversized page, unoptimized images, old
                # HTTP protocol) lands in HOTH's own D-grade range (~60-69),
                # rather than collapsing toward 0 from stacked heavy penalties.
                if key == "page_too_large":
                    page_perf_score -= 8
                elif key == "poor_lcp":
                    page_perf_score -= 12
                elif key == "poor_tti":
                    page_perf_score -= 8
                elif key == "unoptimized_images":
                    page_perf_score -= 8
                elif key == "outdated_http_protocol":
                    page_perf_score -= 4
                elif key == "missing_viewport_meta":
                    page_perf_score -= 6
            per_page_scores.append(max(0, page_perf_score))
        performance_score = round(sum(per_page_scores) / len(per_page_scores), 1)

    # ---------------- GEO Score (0-100) ----------------
    # Wired to performance_agent.py's rendering_gap_pct + llms_txt check.
    # Stays None if that data was never collected, same reasoning as above.
    geo_score = None
    pages_with_geo_data = [p for p in pages if p.get("rendering_gap_pct") is not None]
    if pages_with_geo_data:
        per_page_scores = []
        for p in pages_with_geo_data:
            page_geo_score = 100.0
            gap = p.get("rendering_gap_pct", 0)
            # Banded to match HOTH's own grading: their audit treated a 26%
            # rendering gap as D-grade (~60s), which is notably stricter than
            # it might look at first glance — JS-rendered content is content
            # an LLM/AI crawler simply never sees, so HOTH weights this heavily.
            if gap > 40:
                page_geo_score -= 45
            elif gap > 20:
                page_geo_score -= 35
            elif gap > 10:
                page_geo_score -= 15
            per_page_scores.append(max(0, page_geo_score))
        geo_score = sum(per_page_scores) / len(per_page_scores)
        if not state.get("llms_txt", {}).get("exists"):
            geo_score -= 10
        geo_score = round(max(0, min(100, geo_score)), 1)

    # ---------------- Overall Score ----------------
    # Uses the full 6-category weighting once performance + GEO data exists;
    # falls back to the original 4-category weighting when it doesn't, so
    # this works whether or not performance_agent.py has been run yet.
    if performance_score is not None and geo_score is not None:
        overall_score = (
            technical_score * 0.20 +
            content_score * 0.20 +
            keyword_score * 0.15 +
            metadata_score * 0.15 +
            performance_score * 0.20 +
            geo_score * 0.10
        )
    else:
        overall_score = (
            technical_score * 0.30 +
            content_score * 0.25 +
            keyword_score * 0.25 +
            metadata_score * 0.20
        )

    scores = {
        "technical_score": round(technical_score, 1),
        "content_score": round(content_score, 1),
        "keyword_score": round(keyword_score, 1),
        "metadata_score": round(metadata_score, 1),
        "performance_score": performance_score,
        "geo_score": geo_score,
        "overall_score": round(overall_score, 1),
    }

    state["seo_scores"] = scores
    return state