def run_score_agent(state: dict) -> dict:
    """Calculate comprehensive SEO scores."""
    pages = state.get("crawled_pages", [])
    issues = state.get("seo_issues", [])
    keywords = state.get("keywords", {})
    content = state.get("generated_content", {})

    # Technical SEO Score (0-100)
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

    # Content Score (0-100)
    content_score = 50.0
    if pages:
        pages_with_content = [p for p in pages if p.get("word_count", 0) >= 300]
        pages_with_h1 = [p for p in pages if p.get("h1")]
        pages_with_title = [p for p in pages if p.get("title")]

        content_ratio = len(pages_with_content) / len(pages) if pages else 0
        h1_ratio = len(pages_with_h1) / len(pages) if pages else 0
        title_ratio = len(pages_with_title) / len(pages) if pages else 0

        content_score = (content_ratio * 40) + (h1_ratio * 30) + (title_ratio * 30)
        content_score = max(0, min(100, content_score))
    elif content.get("faqs") and content.get("blog_ideas"):
        content_score = 60  # Has generated content but no website

    # Keyword Score (0-100)
    total_keywords = state.get("total_keywords", 0)
    keyword_score = min(100, (total_keywords / 30) * 100)

    # Metadata Score (0-100)
    metadata_score = 50.0
    if pages:
        pages_with_meta = [p for p in pages if p.get("meta_description")]
        pages_with_canonical = [p for p in pages if p.get("canonical")]
        meta_ratio = len(pages_with_meta) / len(pages) if pages else 0
        canonical_ratio = len(pages_with_canonical) / len(pages) if pages else 0
        metadata_score = (meta_ratio * 60) + (canonical_ratio * 40)
        metadata_score = max(0, min(100, metadata_score))
    elif content.get("metadata"):
        metadata_score = 70

    # Overall Score
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
        "overall_score": round(overall_score, 1)
    }

    state["seo_scores"] = scores
    return state
