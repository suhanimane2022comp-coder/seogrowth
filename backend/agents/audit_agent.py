from typing import List, Dict


def run_audit_agent(state: dict) -> dict:
    """Analyze crawled pages and generate SEO issues."""
    pages = state.get("crawled_pages", [])
    all_issues = []
    title_set = {}

    for page in pages:
        url = page["url"]
        issues = []

        # Title checks
        if not page.get("title"):
            issues.append({
                "page_url": url,
                "issue_type": "missing_title",
                "severity": "critical",
                "description": "Page is missing a title tag."
            })
        else:
            t = page["title"]
            if t in title_set:
                issues.append({
                    "page_url": url,
                    "issue_type": "duplicate_title",
                    "severity": "warning",
                    "description": f"Duplicate title found also on: {title_set[t]}"
                })
            else:
                title_set[t] = url
            if len(t) > 60:
                issues.append({
                    "page_url": url,
                    "issue_type": "title_too_long",
                    "severity": "warning",
                    "description": f"Title is {len(t)} characters (recommended: under 60)."
                })

        # Meta description checks
        if not page.get("meta_description"):
            issues.append({
                "page_url": url,
                "issue_type": "missing_meta_description",
                "severity": "critical",
                "description": "Page is missing a meta description."
            })
        elif len(page["meta_description"]) > 160:
            issues.append({
                "page_url": url,
                "issue_type": "meta_description_too_long",
                "severity": "warning",
                "description": f"Meta description is {len(page['meta_description'])} characters (recommended: under 160)."
            })

        # H1 checks
        h1 = page.get("h1")
        if not h1:
            issues.append({
                "page_url": url,
                "issue_type": "missing_h1",
                "severity": "critical",
                "description": "Page is missing an H1 tag."
            })

        # Alt text
        if page.get("missing_alt_count", 0) > 0:
            issues.append({
                "page_url": url,
                "issue_type": "missing_alt_text",
                "severity": "warning",
                "description": f"{page['missing_alt_count']} image(s) missing alt text."
            })

        # Thin content
        if page.get("word_count", 0) < 300:
            issues.append({
                "page_url": url,
                "issue_type": "thin_content",
                "severity": "warning",
                "description": f"Page has only {page.get('word_count', 0)} words. Recommended: 300+."
            })

        # Missing canonical
        if not page.get("canonical"):
            issues.append({
                "page_url": url,
                "issue_type": "missing_canonical",
                "severity": "info",
                "description": "Page is missing a canonical tag."
            })

        all_issues.extend(issues)

    # Technical checks
    if not state.get("robots_txt", {}).get("exists"):
        all_issues.append({
            "page_url": state.get("website_url", ""),
            "issue_type": "missing_robots_txt",
            "severity": "critical",
            "description": "robots.txt file not found."
        })

    if not state.get("sitemap", {}).get("exists"):
        all_issues.append({
            "page_url": state.get("website_url", ""),
            "issue_type": "missing_sitemap",
            "severity": "critical",
            "description": "sitemap.xml not found."
        })

    state["seo_issues"] = all_issues
    state["total_issues"] = len(all_issues)
    state["critical_issues"] = len([i for i in all_issues if i["severity"] == "critical"])
    state["warning_issues"] = len([i for i in all_issues if i["severity"] == "warning"])

    return state
