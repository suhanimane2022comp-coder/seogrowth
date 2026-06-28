from typing import List, Dict
from agents.score_agent import build_seo_issues


def run_audit_agent(state: dict) -> dict:
    """
    Build the final state["seo_issues"] list.

    Per-page issues (missing title/meta/H1, thin content, missing alt text,
    missing canonical, etc.) are already detected by crawler_agent.py and
    performance_agent.py and stored on each page's "issues" list. This agent
    converts those into structured records via score_agent.build_seo_issues
    (the single source of truth for issue_key -> severity -> description),
    then adds the checks that genuinely can't be done per-page:
      - site-level: robots.txt / sitemap.xml existence
      - cross-page: duplicate <title> tags

    PREVIOUSLY this file ALSO re-detected title/meta/h1/alt/thin-content
    issues from scratch, on a different dict schema than build_seo_issues
    produces (page_url/issue_type vs url/issue/issue_key). Whichever code
    path's issues ended up in state["seo_issues"] determined behavior, and
    real bugs were traced directly to that duplication:
      1. Severity mismatch: this file scored missing_meta_description as
         "critical"; score_agent.ISSUE_SEVERITY scores it "warning". Same
         real-world issue, two different severities depending on which
         agent's copy of it survived.
      2. Technical score collapse: with the same issues effectively counted
         under this file's harsher severities, technical_score's
         per-critical/-warning deductions stacked up far higher than the
         site's real problems warranted (this is why a site with one
         missing meta description here, a 32-word page there, showed
         Technical SEO at 0/100).
      3. "Unspecified issue" in the Improvement Plan: report_agent.py reads
         i.get("issue") / i.get("issue_key"); this file's dicts had neither
         (only "issue_type"), so every Priority 1 bullet silently fell back
         to the placeholder string.
      4. Untraceable issues in the PDF: this file used "page_url" while
         pdf_service.py / report_agent.py expect "url" — so issues in the
         generated report couldn't be reliably tied back to which page they
         were actually about.
    """
    pages = state.get("crawled_pages", [])

    all_issues = build_seo_issues(pages)

    # Cross-page check: duplicate titles can't be detected by crawler_agent
    # (it only sees one page at a time), so it stays here.
    title_seen = {}
    for page in pages:
        t = page.get("title")
        url = page.get("url")
        if not t:
            continue
        if t in title_seen:
            all_issues.append({
                "url": url,
                "issue": f"duplicate_title:{title_seen[t]}",
                "issue_key": "duplicate_title",
                "issue_type": "duplicate_title",
                "description": f"Duplicate title also found on: {title_seen[t]}",
                "severity": "warning",
            })
        else:
            title_seen[t] = url

    # Site-level checks: robots.txt / sitemap.xml — not page-specific, and
    # nothing else in the pipeline checks these. Same schema as
    # build_seo_issues' output so report_agent/pdf_service don't need to
    # special-case them.
    website_url = state.get("website_url", "")

    if not state.get("robots_txt", {}).get("exists"):
        all_issues.append({
            "url": website_url,
            "issue": "missing_robots_txt",
            "issue_key": "missing_robots_txt",
            "issue_type": "missing_robots_txt",
            "description": "robots.txt file not found.",
            "severity": "critical",
        })

    if not state.get("sitemap", {}).get("exists"):
        all_issues.append({
            "url": website_url,
            "issue": "missing_sitemap",
            "issue_key": "missing_sitemap",
            "issue_type": "missing_sitemap",
            "description": "sitemap.xml not found.",
            "severity": "critical",
        })

    state["seo_issues"] = all_issues
    state["total_issues"] = len(all_issues)
    state["critical_issues"] = len([i for i in all_issues if i["severity"] == "critical"])
    state["warning_issues"] = len([i for i in all_issues if i["severity"] == "warning"])

    return state