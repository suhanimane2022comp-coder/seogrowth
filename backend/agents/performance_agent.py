"""
performance_agent.py

Measures Performance, GEO (Generative Engine Optimization), and Usability
signals for each crawled page — the categories that crawler_agent.py and
score_agent.py never measured at all, which is why the SEO Growth Report
could show 100/100 on a site that an external audit (HOTH) graded D on
Performance and D on GEO.

Run this after run_crawler_agent (it needs state["crawled_pages"] to know
which URLs to measure). Output is merged back into each page dict under a
"performance" key, plus site-level checks (llms.txt, HTTPS redirect, HTTP
protocol version) added to top-level state, mirroring how robots_txt/
sitemap are already handled in crawler_agent.py.
"""

import requests
import asyncio
import concurrent.futures
import time
from typing import List, Optional
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 SEOGrowthBot/1.0"
}

# Thresholds aligned to Google's published "good" Core Web Vitals targets
# and HOTH's stated rules of thumb (5MB page weight, 500-word content floor).
MAX_PAGE_WEIGHT_MB = 5.0
MAX_LCP_SECONDS = 2.5
MAX_TTI_SECONDS = 3.8
LARGE_IMAGE_BYTES = 300_000  # single image over this = flagged as unoptimized
RENDERING_GAP_WARN_PCT = 15


# --------------------------------------------------------------------------
# Site-level checks (one per site, not per page)
# --------------------------------------------------------------------------

def check_llms_txt(base_url: str) -> dict:
    llms_url = urljoin(base_url, "/llms.txt")
    try:
        r = requests.get(llms_url, headers=HEADERS, timeout=5)
        exists = r.status_code == 200 and len(r.text.strip()) > 0
        return {"exists": exists, "url": llms_url if exists else ""}
    except Exception:
        return {"exists": False, "url": ""}


def check_https_redirect(domain: str) -> dict:
    """Does the http:// version of the site actually redirect to https://?"""
    http_url = f"http://{domain}"
    try:
        r = requests.get(http_url, headers=HEADERS, timeout=8, allow_redirects=True)
        return {"redirects_to_https": urlparse(r.url).scheme == "https", "final_url": r.url}
    except Exception:
        return {"redirects_to_https": None, "final_url": None}


def check_http_protocol(url: str) -> Optional[bool]:
    """
    True if HTTP/2+, False if HTTP/1.x, None if undetermined.

    Caveat worth knowing: Python's requests/urllib3 stack often negotiates
    HTTP/1.1 regardless of what the server actually supports for browsers,
    so a False/None here means "unconfirmed via this method," not
    necessarily "the server has no HTTP/2 support." Treat this as a
    starting signal to verify (e.g. `curl -I --http2 <url>`), the same way
    HOTH's own audit presumably has access to richer measurement tooling
    than a single Python request.
    """
    try:
        r = requests.get(url, headers=HEADERS, timeout=8, stream=True)
        raw_version = getattr(r.raw, "version", None)  # 11 = HTTP/1.1, 20 = HTTP/2
        r.close()
        return None if raw_version is None else raw_version >= 20
    except Exception:
        return None


def check_raw_html_word_count(url: str) -> Optional[int]:
    """
    Word count from the raw server response, with NO JavaScript executed —
    this is what an LLM/AI crawler typically sees, per HOTH's GEO section.
    Compared against the Playwright-rendered word count to compute the
    "rendering gap" percentage HOTH reports (Indmark's was 26%).
    """
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(r.text, "lxml")
        return len(soup.get_text(separator=" ", strip=True).split())
    except Exception:
        return None


# --------------------------------------------------------------------------
# Per-page performance measurement (Playwright, full resource loading)
# --------------------------------------------------------------------------

async def measure_page_performance(url: str, browser, timeout: int = 30000) -> dict:
    """
    Loads a page with ALL resources (images, fonts, etc. — nothing blocked)
    and captures real performance + page-weight data via response listeners
    and the browser Performance API, matching what HOTH's PageSpeed-style
    section reports: LCP, TTI, CLS, page weight breakdown, resource count.
    """
    page = None
    resource_log = []
    nav_start = time.time()

    try:
        page = await browser.new_page(user_agent=HEADERS["User-Agent"])

        def on_response(response):
            try:
                req = response.request
                size = int(response.headers.get("content-length", 0))
                resource_log.append({"url": response.url, "type": req.resource_type, "size_bytes": size})
            except Exception:
                pass

        page.on("response", on_response)

        await page.goto(url, wait_until="networkidle", timeout=timeout)
        load_complete_seconds = time.time() - nav_start

        await page.wait_for_timeout(1500)

        try:
            perf_metrics = await page.evaluate("""
                () => {
                    const lcpEntries = performance.getEntriesByType('largest-contentful-paint');
                    const lcp = lcpEntries.length ? lcpEntries[lcpEntries.length - 1].startTime / 1000 : null;
                    const nav = performance.getEntriesByType('navigation')[0];
                    const tti = nav ? nav.domInteractive / 1000 : null;
                    const fcp = performance.getEntriesByType('paint').find(e => e.name === 'first-contentful-paint');
                    let cls = 0;
                    for (const entry of performance.getEntriesByType('layout-shift')) {
                        if (!entry.hadRecentInput) cls += entry.value;
                    }
                    const hasViewport = !!document.querySelector('meta[name="viewport"]');
                    return {
                        lcp, tti, cls,
                        fcp: fcp ? fcp.startTime / 1000 : null,
                        has_viewport: hasViewport,
                    };
                }
            """)
        except Exception:
            perf_metrics = {"lcp": None, "tti": None, "cls": None, "fcp": None, "has_viewport": None}

        breakdown = {"html": 0, "css": 0, "js": 0, "image": 0, "font": 0, "other": 0}
        unoptimized_images = []
        for r in resource_log:
            size = r["size_bytes"]
            rtype = r["type"]
            if rtype == "document":
                breakdown["html"] += size
            elif rtype == "stylesheet":
                breakdown["css"] += size
            elif rtype == "script":
                breakdown["js"] += size
            elif rtype == "image":
                breakdown["image"] += size
                if size > LARGE_IMAGE_BYTES:
                    unoptimized_images.append({"url": r["url"], "size_bytes": size})
            elif rtype == "font":
                breakdown["font"] += size
            else:
                breakdown["other"] += size

        total_bytes = sum(breakdown.values())

        return {
            "load_complete_seconds": round(load_complete_seconds, 2),
            "fcp_seconds": round(perf_metrics["fcp"], 2) if perf_metrics.get("fcp") else None,
            "lcp_seconds": round(perf_metrics["lcp"], 2) if perf_metrics.get("lcp") else None,
            "tti_seconds": round(perf_metrics["tti"], 2) if perf_metrics.get("tti") else None,
            "cumulative_layout_shift": round(perf_metrics["cls"], 3) if perf_metrics.get("cls") is not None else None,
            "has_viewport_meta": perf_metrics.get("has_viewport"),
            "page_weight_mb": round(total_bytes / (1024 * 1024), 2),
            "page_weight_breakdown_mb": {k: round(v / (1024 * 1024), 3) for k, v in breakdown.items()},
            "resource_count": len(resource_log),
            "unoptimized_images": unoptimized_images,
        }

    except Exception as e:
        print(f"Performance measurement failed for {url}: {e}")
        return {}
    finally:
        if page:
            await page.close()


async def _async_measure_all(urls: List[str]) -> List[dict]:
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage",
                "--disable-accelerated-2d-canvas", "--no-first-run", "--no-zygote", "--disable-gpu",
            ],
        )
        try:
            results = []
            for url in urls:
                perf = await measure_page_performance(url, browser)
                results.append({"url": url, "performance": perf})
                print(f"Measured: {url} | weight: {perf.get('page_weight_mb')}MB | "
                      f"LCP: {perf.get('lcp_seconds')}s | TTI: {perf.get('tti_seconds')}s")
                await asyncio.sleep(0.5)
            return results
        finally:
            await browser.close()


def measure_all_pages(urls: List[str]) -> List[dict]:
    """Thread-isolated entry point, same pattern as crawler_agent.crawl_website."""
    def run_in_thread():
        import platform
        if platform.system() == "Windows":
            loop = asyncio.ProactorEventLoop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(_async_measure_all(urls))
            finally:
                loop.close()
        else:
            return asyncio.run(_async_measure_all(urls))

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(run_in_thread)
        return future.result()


# --------------------------------------------------------------------------
# Issue detection from measured data — same flat-string convention the
# crawler uses, so score_agent's existing issue-key parsing works unchanged.
# --------------------------------------------------------------------------

def detect_performance_issues(perf: dict, http2: Optional[bool]) -> List[str]:
    issues = []
    if not perf:
        return issues
    if perf.get("page_weight_mb") and perf["page_weight_mb"] > MAX_PAGE_WEIGHT_MB:
        issues.append(f"page_too_large:{perf['page_weight_mb']}MB")
    if perf.get("lcp_seconds") and perf["lcp_seconds"] > MAX_LCP_SECONDS:
        issues.append(f"poor_lcp:{perf['lcp_seconds']}s")
    if perf.get("tti_seconds") and perf["tti_seconds"] > MAX_TTI_SECONDS:
        issues.append(f"poor_tti:{perf['tti_seconds']}s")
    if perf.get("unoptimized_images"):
        issues.append(f"unoptimized_images:{len(perf['unoptimized_images'])}_found")
    if perf.get("has_viewport_meta") is False:
        issues.append("missing_viewport_meta")
    if http2 is False:
        issues.append("outdated_http_protocol")
    return issues


def detect_geo_issues(rendering_gap_pct: Optional[float], llms_txt_exists: bool) -> List[str]:
    issues = []
    if rendering_gap_pct is not None and rendering_gap_pct > RENDERING_GAP_WARN_PCT:
        issues.append(f"high_js_rendering_dependency:{rendering_gap_pct}pct_content_js_only")
    if not llms_txt_exists:
        issues.append("missing_llms_txt")
    return issues


# --------------------------------------------------------------------------
# Agent entry point
# --------------------------------------------------------------------------

def run_performance_agent(state: dict) -> dict:
    """
    Requires state["crawled_pages"] to already be populated by
    run_crawler_agent. Adds a "performance" dict and updated "issues" list
    to each page, plus site-level llms_txt / https_redirect checks.
    """
    pages = state.get("crawled_pages", [])
    website_url = state.get("website_url")

    if not pages or not website_url:
        state["llms_txt"] = {"exists": False}
        state["https_redirect"] = {"redirects_to_https": None}
        return state

    if not website_url.startswith("http"):
        website_url = "https://" + website_url
    domain = urlparse(website_url).netloc

    llms = check_llms_txt(website_url)
    https_redirect = check_https_redirect(domain)

    urls = [p["url"] for p in pages]
    perf_results = measure_all_pages(urls)
    perf_by_url = {r["url"]: r["performance"] for r in perf_results}

    for page in pages:
        url = page["url"]
        perf = perf_by_url.get(url, {})
        http2 = check_http_protocol(url)
        raw_word_count = check_raw_html_word_count(url)

        rendered_word_count = page.get("word_count", 0)
        rendering_gap_pct = None
        if raw_word_count is not None and rendered_word_count > 0:
            rendering_gap_pct = round(max(0, (rendered_word_count - raw_word_count) / rendered_word_count * 100), 1)

        page["performance"] = perf
        page["uses_http2"] = http2
        page["raw_html_word_count"] = raw_word_count
        page["rendering_gap_pct"] = rendering_gap_pct

        new_issues = detect_performance_issues(perf, http2) + detect_geo_issues(rendering_gap_pct, llms["exists"])
        page["issues"] = page.get("issues", []) + new_issues

    state["crawled_pages"] = pages
    state["llms_txt"] = llms
    state["https_redirect"] = https_redirect

    return state