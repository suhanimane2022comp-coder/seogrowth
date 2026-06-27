from typing import List, Dict


# --------------------------------------------------------------------------
# Issue severity map. This is the missing link: the crawler detects real
# problems (multiple_h1, thin_content, etc.) and writes them into each
# page's `issues` list as flat strings, but nothing was ever converting
# those into state["seo_issues"] — so run_score_agent's critical/warning
# counts were always reading an empty list. That's the entire reason a
# page with 3 H1 tags and 429 words of content still scored 100/100.
# --------------------------------------------------------------------------
ISSUE_SEVERITY = {
    "missing_title": "critical",
    "missing_meta_description": "warning",
    "missing_h1": "critical",
    "multiple_h1": "warning",
    "missing_alt_text": "warning",
    "thin_content": "warning",
    "missing_canonical": "warning",
    "missing_lang_attribute": "info",
    "missing_viewport_meta": "warning",
    "missing_structured_data": "info",
    "missing_open_graph_tags": "info",
    "noindex_detected": "critical",
    "iframes_present": "info",
    "high_js_rendering_dependency": "warning",
    "page_too_large": "warning",
    "poor_lcp": "critical",
    "poor_tti": "warning",
    "unoptimized_images": "warning",
    "outdated_http_protocol": "info",
}


def _issue_key(issue: str) -> str:
    """Crawler issues are sometimes flat strings ('missing_h1') and sometimes
    carry a detail suffix ('multiple_h1:3_found', 'thin_content:429_words').
    Split on the first colon to get the lookup key either way."""
    return issue.split(":")[0] if isinstance(issue, str) else str(issue)


def build_seo_issues(pages: List[dict]) -> List[dict]:
    """
    Convert each page's flat `issues` list (written by the crawler) into the
    structured {url, issue, severity} records the rest of the pipeline
    expects in state["seo_issues"]. Previously nothing did this, so
    state["seo_issues"] stayed empty regardless of what the crawler found.
    """
    structured = []
    for page in pages:
        for issue in page.get("issues", []):
            key = _issue_key(issue)
            structured.append({
                "url": page.get("url"),
                "issue": issue,
                "issue_key": key,
                "severity": ISSUE_SEVERITY.get(key, "warning"),  # unknown issues default to warning, not silently ignored
            })
    return structured


def run_score_agent(state: dict) -> dict:
    """Calculate comprehensive SEO scores."""
    pages = state.get("crawled_pages", [])

    # Build seo_issues from the crawler's per-page issues if it wasn't
    # already populated upstream. This is the fix for the core bug: previously
    # state.get("seo_issues", []) was empty because nothing wrote to it.
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
        technical_score = 30  # No website to audit
    else:
        critical_issues = [i for i in issues if i["severity"] == "critical"]
        warning_issues = [i for i in issues if i["severity"] == "warning"]
        technical_score -= len(critical_issues) * 10
        technical_score -= len(warning_issues) * 5

        if not state.get("robots_txt", {}).get("exists"):
            technical_score -= 10
        if not state.get("sitemap", {}).get("exists"):
            technical_score -= 10

        technical_score = max(0, min(100, technical_score))

    # ---------------- Content Score (0-100) ----------------
    # Previously this only checked word_count >= 300 and h1 truthiness, which
    # can't see multiple_h1 (page.get("h1") is still truthy with 3 H1 tags)
    # and used a looser word-count threshold than the issues list does.
    # Now it penalizes directly from the same issues every page already has,
    # so a page flagged thin_content or multiple_h1 can't still score clean.
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
        content_score = 60  # Has generated content but no website

    # ---------------- Keyword Score (0-100) ----------------
    total_keywords = state.get("total_keywords", 0)
    keyword_score = min(100, (total_keywords / 30) * 100)

    # ---------------- Metadata Score (0-100) ----------------
    metadata_score = 50.0
    if pages:
        pages_with_meta = [p for p in pages if p.get("meta_description")]
        pages_with_canonical = [p for p in pages if p.get("canonical")]
        # multiple_h1 is a metadata/structure problem as much as a content one —
        # a page can have a meta description AND canonical set and still have
        # broken heading structure, so it needs its own penalty here too.
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
    # This category did not exist before. Report 2 (HOTH audit) graded this
    # site D on Performance — a 19.5s mobile LCP and 6.18MB page weight are
    # real, measurable problems that a keyword/content-only scorer can never
    # surface. If the crawler hasn't been upgraded to capture perf data yet,
    # this is explicitly marked "not measured" rather than defaulting to 100,
    # which is the same silent-100 bug being fixed here for the other categories.
    performance_score = None
    pages_with_perf = [p for p in pages if p.get("performance")]
    if pages_with_perf:
        performance_score = 100.0
        for p in pages_with_perf:
            for issue in p.get("issues", []):
                key = _issue_key(issue)
                if key == "page_too_large":
                    performance_score -= 15
                elif key == "poor_lcp":
                    performance_score -= 25
                elif key == "poor_tti":
                    performance_score -= 15
                elif key == "unoptimized_images":
                    performance_score -= 15
                elif key == "outdated_http_protocol":
                    performance_score -= 5
        performance_score = max(0, min(100, performance_score / len(pages_with_perf) if len(pages_with_perf) else performance_score))

    # ---------------- GEO Score (0-100) ----------------
    # Also did not exist before. Measures whether content is actually
    # present in raw HTML (what LLM/AI crawlers read) vs only appearing
    # after JS executes, plus presence of llms.txt and structured data.
    geo_score = None
    pages_with_geo_data = [p for p in pages if p.get("rendering_gap_pct") is not None]
    if pages_with_geo_data:
        geo_score = 100.0
        for p in pages_with_geo_data:
            gap = p.get("rendering_gap_pct", 0)
            if gap > 50:
                geo_score -= 30
            elif gap > 15:
                geo_score -= 15
            if not p.get("has_structured_data"):
                geo_score -= 10
        if not state.get("llms_txt", {}).get("exists"):
            geo_score -= 10
        geo_score = max(0, min(100, geo_score))

    # ---------------- Overall Score ----------------
    # Re-weighted to include performance and GEO when available. If either
    # is unmeasured (older crawler output without perf/GEO capture), fall
    # back to the original 4-category weighting rather than penalizing for
    # data that was never collected — that would be its own form of
    # inaccuracy in the opposite direction.
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
        "performance_score": round(performance_score, 1) if performance_score is not None else None,
        "geo_score": round(geo_score, 1) if geo_score is not None else None,
        "overall_score": round(overall_score, 1),
    }

    state["seo_scores"] = scores
    return state