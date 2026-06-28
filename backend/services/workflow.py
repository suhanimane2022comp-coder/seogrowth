from langgraph.graph import StateGraph, END
from typing import TypedDict, Optional, List, Dict, Any

from agents.business_agent import run_business_agent
from agents.crawler_agent import run_crawler_agent
from agents.performance_agent import run_performance_agent
from agents.audit_agent import run_audit_agent
from agents.keyword_agent import run_keyword_agent
from agents.content_gap_agent import run_content_gap_agent
from agents.content_agent import run_content_agent
from agents.score_agent import run_score_agent
from agents.report_agent import run_report_agent


class SEOState(TypedDict):
    # Input
    business_name: str
    business_description: str
    products_services: str
    target_audience: str
    target_location: str
    website_url: Optional[str]
    competitor_urls: List[str]

    # Agent outputs
    business_analysis: Dict[str, Any]
    crawled_pages: List[Dict]
    robots_txt: Dict
    sitemap: Dict
    llms_txt: Dict
    https_redirect: Dict
    pages_crawled: int
    seo_issues: List[Dict]
    total_issues: int
    critical_issues: int
    warning_issues: int
    keywords: Dict[str, List[str]]
    total_keywords: int
    content_gaps: Dict[str, List[str]]
    generated_content: Dict[str, Any]
    seo_scores: Dict[str, float]
    report: Dict[str, Any]


def build_seo_workflow():
    workflow = StateGraph(SEOState)

    # Add nodes
    workflow.add_node("business_understanding", run_business_agent)
    workflow.add_node("website_crawl", run_crawler_agent)
    # NEW NODE: performance_agent.py already implements page-weight, LCP/TTI,
    # Core-Web-Vitals-style checks, the GEO rendering-gap check, llms.txt,
    # and HTTPS-redirect/HTTP-2 checks -- everything score_agent.py needs to
    # compute performance_score and geo_score. It was simply never added to
    # the graph, so those scores always stayed None and never appeared in
    # the report. It must run after website_crawl (it needs crawled_pages)
    # and before seo_audit/seo_score (they consume page["issues"] /
    # page["performance"] that this agent writes).
    workflow.add_node("performance_check", run_performance_agent)
    workflow.add_node("seo_audit", run_audit_agent)
    workflow.add_node("keyword_research", run_keyword_agent)
    workflow.add_node("content_gap_analysis", run_content_gap_agent)
    workflow.add_node("content_generation", run_content_agent)
    workflow.add_node("seo_score", run_score_agent)
    workflow.add_node("report_generation", run_report_agent)

    # Define flow
    workflow.set_entry_point("business_understanding")
    workflow.add_edge("business_understanding", "website_crawl")
    workflow.add_edge("website_crawl", "performance_check")
    workflow.add_edge("performance_check", "seo_audit")
    workflow.add_edge("seo_audit", "keyword_research")
    workflow.add_edge("keyword_research", "content_gap_analysis")
    workflow.add_edge("content_gap_analysis", "content_generation")
    workflow.add_edge("content_generation", "seo_score")
    workflow.add_edge("seo_score", "report_generation")
    workflow.add_edge("report_generation", END)

    return workflow.compile()


def run_seo_analysis(
    business_name: str,
    business_description: str,
    products_services: str,
    target_audience: str,
    target_location: str,
    website_url: Optional[str] = None,
    competitor_urls: Optional[List[str]] = None,
) -> Dict[str, Any]:

    graph = build_seo_workflow()

    initial_state = SEOState(
        business_name=business_name,
        business_description=business_description,
        products_services=products_services,
        target_audience=target_audience,
        target_location=target_location,
        website_url=website_url,
        competitor_urls=competitor_urls or [],
        business_analysis={},
        crawled_pages=[],
        robots_txt={},
        sitemap={},
        llms_txt={},
        https_redirect={},
        pages_crawled=0,
        seo_issues=[],
        total_issues=0,
        critical_issues=0,
        warning_issues=0,
        keywords={},
        total_keywords=0,
        content_gaps={},
        generated_content={},
        seo_scores={},
        report={}
    )

    result = graph.invoke(initial_state)
    return result