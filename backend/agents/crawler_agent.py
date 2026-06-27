import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, urlunparse
from typing import List, Optional
import time
import asyncio
import concurrent.futures
from playwright.async_api import async_playwright

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 SEOGrowthBot/1.0"
}

COMMON_PATHS = [
    "/contact", "/contact-us", "/about", "/about-us", "/services",
    "/pricing", "/faq", "/blog", "/privacy-policy", "/terms",
]

# --- Thresholds (aligned to industry-standard audit tools, not arbitrary) ---
MIN_WORD_COUNT = 500          # below this = "thin content" (was 300 — too lenient)
MAX_PAGE_WEIGHT_MB = 5.0      # total downloadable page size budget
MAX_LCP_SECONDS = 2.5         # Google "good" LCP threshold
MAX_TTI_SECONDS = 3.8         # Google "good" TTI threshold
MIN_IMAGE_COMPRESSION_SAVINGS = 0.30  # flag images that could shrink >30%
RENDERING_GAP_WARN_PCT = 15   # % of content only appearing after JS render


def normalize_domain(netloc: str) -> str:
    netloc = netloc.lower()
    return netloc[4:] if netloc.startswith("www.") else netloc


def normalize_url(url: str) -> str:
    parsed = urlparse(url)
    path = parsed.path.rstrip("/") or "/"
    netloc = normalize_domain(parsed.netloc)
    return urlunparse((parsed.scheme, netloc, path, parsed.params, parsed.query, ""))


def check_robots_txt(base_url: str) -> dict:
    robots_url = urljoin(base_url, "/robots.txt")
    try:
        r = requests.get(robots_url, headers=HEADERS, timeout=5)
        exists = r.status_code == 200 and len(r.text.strip()) > 0
        return {"exists": exists, "content": r.text if exists else ""}
    except Exception:
        return {"exists": False, "content": ""}


def check_sitemap(base_url: str) -> dict:
    for path in ("/sitemap.xml", "/sitemap_index.xml"):
        sitemap_url = urljoin(base_url, path)
        try:
            r = requests.get(sitemap_url, headers=HEADERS, timeout=5)
            content_type_xml = "xml" in r.headers.get("Content-Type", "").lower()
            looks_like_xml = "<urlset" in r.text[:500].lower() or "<sitemapindex" in r.text[:500].lower()
            if r.status_code == 200 and (content_type_xml or looks_like_xml):
                return {"exists": True, "url": sitemap_url}
        except Exception:
            continue
    return {"exists": False, "url": ""}


def check_llms_txt(base_url: str) -> dict:
    llms_url = urljoin(base_url, "/llms.txt")
    try:
        r = requests.get(llms_url, headers=HEADERS, timeout=5)
        exists = r.status_code == 200 and len(r.text.strip()) > 0
        return {"exists": exists, "url": llms_url if exists else ""}
    except Exception:
        return {"exists": False, "url": ""}


def check_https_redirect(domain: str) -> dict:
    """Does the http:// version actually redirect to https://?"""
    http_url = f"http://{domain}"
    try:
        r = requests.get(http_url, headers=HEADERS, timeout=8, allow_redirects=True)
        final_scheme = urlparse(r.url).scheme
        return {"redirects_to_https": final_scheme == "https", "final_url": r.url}
    except Exception:
        return {"redirects_to_https": None, "final_url": None}


def check_raw_html_word_count(url: str) -> Optional[int]:
    """
    Fetch the page WITHOUT JS execution (raw server response), the way an
    LLM/AI crawler typically would. Used to compute the rendering gap vs
    the Playwright-rendered version of the same page.
    """
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(r.text, "lxml")
        text = soup.get_text(separator=" ", strip=True)
        return len(text.split())
    except Exception:
        return None


def extract_page_data(url: str, soup: BeautifulSoup, perf: Optional[dict] = None,
                       raw_word_count: Optional[int] = None) -> dict:
    title_tag = soup.find("title")
    title = title_tag.get_text(strip=True) if title_tag else None
    title_length = len(title) if title else 0

    meta_desc_tag = soup.find("meta", attrs={"name": "description"})
    meta_description = meta_desc_tag.get("content", "").strip() if meta_desc_tag else None
    meta_description = meta_description or None
    meta_length = len(meta_description) if meta_description else 0

    h1_tags = [h.get_text(strip=True) for h in soup.find_all("h1") if h.get_text(strip=True)]
    h2_tags = [h.get_text(strip=True) for h in soup.find_all("h2") if h.get_text(strip=True)]
    h3_tags = [h.get_text(strip=True) for h in soup.find_all("h3") if h.get_text(strip=True)]

    images = soup.find_all("img")
    missing_alt = [img for img in images if not img.get("alt")]

    canonical_tag = soup.find("link", attrs={"rel": "canonical"})
    canonical = canonical_tag.get("href") if canonical_tag else None

    lang_attr = soup.find("html")
    has_lang = bool(lang_attr and lang_attr.get("lang"))

    has_viewport = bool(soup.find("meta", attrs={"name": "viewport"}))

    json_ld_scripts = soup.find_all("script", attrs={"type": "application/ld+json"})
    has_schema = len(json_ld_scripts) > 0

    og_tags = soup.find_all("meta", attrs={"property": lambda v: v and v.startswith("og:")})
    has_open_graph = len(og_tags) > 0

    noindex_meta = soup.find("meta", attrs={"name": "robots", "content": lambda c: c and "noindex" in c.lower()})
    has_noindex = bool(noindex_meta)

    base_domain = normalize_domain(urlparse(url).netloc)
    all_links = soup.find_all("a", href=True)
    internal_links = []
    external_links = []
    for a in all_links:
        href = a["href"].strip()
        if not href or href.startswith(("mailto:", "tel:", "javascript:")):
            continue
        full_url = urljoin(url, href)
        parsed = urlparse(full_url)
        if normalize_domain(parsed.netloc) == base_domain:
            internal_links.append(normalize_url(full_url))
        elif parsed.scheme in ("http", "https"):
            external_links.append(full_url)

    body_text = soup.get_text(separator=" ", strip=True)
    word_count = len(body_text.split())

    iframes = soup.find_all("iframe")

    # --- Rendering gap (GEO signal): how much content ONLY appears after JS runs ---
    rendering_gap_pct = None
    if raw_word_count is not None and word_count > 0:
        rendering_gap_pct = round(max(0, (word_count - raw_word_count) / word_count * 100), 1)

    # --- Issue detection (each issue maps to a specific, real signal) ---
    issues = []
    if not title:
        issues.append("missing_title")
    elif not (50 <= title_length <= 60):
        issues.append(f"title_length_suboptimal:{title_length}_chars")

    if not meta_description:
        issues.append("missing_meta_description")
    elif not (120 <= meta_length <= 160):
        issues.append(f"meta_description_length_suboptimal:{meta_length}_chars")

    if len(h1_tags) == 0:
        issues.append("missing_h1")
    elif len(h1_tags) > 1:
        issues.append(f"multiple_h1:{len(h1_tags)}_found")

    if missing_alt:
        issues.append(f"missing_alt_text:{len(missing_alt)}_images")

    if word_count < MIN_WORD_COUNT:
        issues.append(f"thin_content:{word_count}_words")

    if not canonical:
        issues.append("missing_canonical")

    if not has_lang:
        issues.append("missing_lang_attribute")

    if not has_viewport:
        issues.append("missing_viewport_meta")

    if not has_schema:
        issues.append("missing_structured_data")

    if not has_open_graph:
        issues.append("missing_open_graph_tags")

    if has_noindex:
        issues.append("noindex_detected")

    if iframes:
        issues.append(f"iframes_present:{len(iframes)}_found")

    if rendering_gap_pct is not None and rendering_gap_pct > RENDERING_GAP_WARN_PCT:
        issues.append(f"high_js_rendering_dependency:{rendering_gap_pct}pct_content_js_only")

    # --- Performance issues (from perf dict, populated by Playwright pass) ---
    if perf:
        if perf.get("page_weight_mb") and perf["page_weight_mb"] > MAX_PAGE_WEIGHT_MB:
            issues.append(f"page_too_large:{perf['page_weight_mb']}MB")
        if perf.get("lcp_seconds") and perf["lcp_seconds"] > MAX_LCP_SECONDS:
            issues.append(f"poor_lcp:{perf['lcp_seconds']}s")
        if perf.get("tti_seconds") and perf["tti_seconds"] > MAX_TTI_SECONDS:
            issues.append(f"poor_tti:{perf['tti_seconds']}s")
        if perf.get("uses_http2") is False:
            issues.append("outdated_http_protocol")
        if perf.get("unoptimized_images"):
            issues.append(f"unoptimized_images:{len(perf['unoptimized_images'])}_found")

    return {
        "url": url,
        "title": title,
        "title_length": title_length,
        "meta_description": meta_description,
        "meta_description_length": meta_length,
        "h1": h1_tags[0] if h1_tags else None,
        "h1_count": len(h1_tags),
        "h1_all": h1_tags,
        "h2_tags": h2_tags[:10],
        "h3_tags": h3_tags[:10],
        "images_count": len(images),
        "missing_alt_count": len(missing_alt),
        "internal_links_count": len(internal_links),
        "external_links_count": len(external_links),
        "internal_links": list(set(internal_links))[:30],
        "canonical": canonical,
        "has_lang_attribute": has_lang,
        "has_viewport_meta": has_viewport,
        "has_structured_data": has_schema,
        "has_open_graph": has_open_graph,
        "has_noindex": has_noindex,
        "iframe_count": len(iframes),
        "word_count": word_count,
        "raw_html_word_count": raw_word_count,
        "rendering_gap_pct": rendering_gap_pct,
        "body_text": body_text[:5000],
        "performance": perf or {},
        "issues": issues,
    }


def check_http_protocol(url: str) -> Optional[bool]:
    """
    Returns True if the server responds over HTTP/2, False if HTTP/1.x,
    None if undetermined. Playwright's high-level API doesn't expose the
    wire protocol version cleanly, so this is checked separately via a raw
    request (urllib3 exposes the underlying connection version).

    Note: Python's `requests`/urllib3 stack negotiates HTTP/1.1 by default
    regardless of what the server supports, so this can under-report HTTP/2
    support. Treat a False/None result here as "unconfirmed", not proof the
    server lacks HTTP/2 — flag it for manual verification (e.g. via
    `curl -I --http2 <url>` or browser dev tools) rather than asserting it
    as a definite issue.
    """
    try:
        r = requests.get(url, headers=HEADERS, timeout=8, stream=True)
        raw_version = getattr(r.raw, "version", None)  # 11 = HTTP/1.1, 20 = HTTP/2
        r.close()
        if raw_version is None:
            return None
        return raw_version >= 20
    except Exception:
        return None


async def fetch_page_async(url: str, browser, timeout: int = 30000):
    """
    Fetch page with full JS rendering using Playwright, and capture real
    performance + resource-weight data via the CDP/network listeners
    instead of just parsing static HTML.
    """
    page = None
    resource_log = []  # list of {url, type, size_bytes}
    nav_start = time.time()

    try:
        page = await browser.new_page(user_agent=HEADERS["User-Agent"])

        def on_response(response):
            try:
                req = response.request
                rtype = req.resource_type
                headers = response.headers
                size = int(headers.get("content-length", 0))
                resource_log.append({"url": response.url, "type": rtype, "size_bytes": size})
            except Exception:
                pass

        page.on("response", on_response)

        response = await page.goto(url, wait_until="networkidle", timeout=timeout)
        uses_http2 = False
        if response:
            try:
                # Playwright exposes this via the underlying response security details on some versions;
                # fall back gracefully if unavailable.
                uses_http2 = "h2" in (await response.server_addr() or {}).get("ipAddress", "") if False else None
            except Exception:
                uses_http2 = None

        load_complete_time = time.time() - nav_start

        await page.wait_for_timeout(2000)

        content_check = await page.evaluate("document.body.innerText.length")
        if content_check < 200:
            await page.wait_for_timeout(3000)

        # Largest Contentful Paint + Time to Interactive proxy via Performance API
        try:
            perf_metrics = await page.evaluate("""
                () => {
                    const lcpEntries = performance.getEntriesByType('largest-contentful-paint');
                    const lcp = lcpEntries.length ? lcpEntries[lcpEntries.length - 1].startTime / 1000 : null;
                    const nav = performance.getEntriesByType('navigation')[0];
                    const tti = nav ? nav.domInteractive / 1000 : null;
                    const cls = (() => {
                        let total = 0;
                        for (const entry of performance.getEntriesByType('layout-shift')) {
                            if (!entry.hadRecentInput) total += entry.value;
                        }
                        return total;
                    })();
                    return {lcp, tti, cls};
                }
            """)
        except Exception:
            perf_metrics = {"lcp": None, "tti": None, "cls": None}

        html = await page.content()
        final_url = page.url

        # --- Resource / page-weight breakdown ---
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
                # Flag any single image over 300KB as an optimization opportunity
                if size > 300_000:
                    unoptimized_images.append({"url": r["url"], "size_bytes": size})
            elif rtype == "font":
                breakdown["font"] += size
            else:
                breakdown["other"] += size

        total_bytes = sum(breakdown.values())
        page_weight_mb = round(total_bytes / (1024 * 1024), 2)
        breakdown_mb = {k: round(v / (1024 * 1024), 3) for k, v in breakdown.items()}

        perf = {
            "load_complete_seconds": round(load_complete_time, 2),
            "lcp_seconds": round(perf_metrics["lcp"], 2) if perf_metrics.get("lcp") else None,
            "tti_seconds": round(perf_metrics["tti"], 2) if perf_metrics.get("tti") else None,
            "cumulative_layout_shift": round(perf_metrics["cls"], 3) if perf_metrics.get("cls") is not None else None,
            "page_weight_mb": page_weight_mb,
            "page_weight_breakdown_mb": breakdown_mb,
            "resource_count": len(resource_log),
            "unoptimized_images": unoptimized_images,
            "uses_http2": uses_http2,  # None = undetermined in this environment; see note below
        }

        return BeautifulSoup(html, "lxml"), final_url, perf

    except Exception as e:
        print(f"Playwright failed to fetch {url}: {e}")
        return None, None, None
    finally:
        if page:
            await page.close()


async def _async_crawl_website(base_url: str, max_pages: int = 15) -> List[dict]:
    """Full async crawl using Playwright browser, with performance + GEO checks per page."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-accelerated-2d-canvas",
                "--no-first-run",
                "--no-zygote",
                "--disable-gpu",
            ]
        )
        try:
            soup, resolved_url, perf = await fetch_page_async(base_url, browser)
            if not soup:
                print(f"Failed to fetch homepage: {base_url}")
                return []

            base_domain = normalize_domain(urlparse(resolved_url).netloc)
            visited = set()
            pages_data = []

            to_visit = [resolved_url]
            visited.add(normalize_url(resolved_url))

            first = True
            while to_visit and len(pages_data) < max_pages:
                url = to_visit.pop(0)

                if first:
                    page_soup, final_url, page_perf = soup, resolved_url, perf
                    first = False
                else:
                    page_soup, final_url, page_perf = await fetch_page_async(url, browser)
                    if not page_soup:
                        continue
                    norm = normalize_url(final_url)
                    if norm in visited and final_url != url:
                        continue
                    visited.add(norm)

                raw_wc = check_raw_html_word_count(final_url)
                page_data = extract_page_data(final_url, page_soup, perf=page_perf, raw_word_count=raw_wc)
                pages_data.append(page_data)

                print(f"Crawled: {final_url} | words: {page_data['word_count']} | "
                      f"h1_count: {page_data['h1_count']} | weight: {page_perf.get('page_weight_mb') if page_perf else 'NA'}MB | "
                      f"issues: {len(page_data['issues'])}")

                for link in page_data.get("internal_links", []):
                    if link not in visited and normalize_domain(urlparse(link).netloc) == base_domain:
                        to_visit.append(link)
                        visited.add(link)

                await asyncio.sleep(0.5)

            if len(pages_data) <= 1:
                print("Only homepage found, probing common paths...")
                for path in COMMON_PATHS:
                    if len(pages_data) >= max_pages:
                        break
                    candidate = urljoin(f"https://{urlparse(resolved_url).netloc}", path)
                    norm = normalize_url(candidate)
                    if norm in visited:
                        continue
                    visited.add(norm)
                    page_soup, final_url, page_perf = await fetch_page_async(candidate, browser)
                    if page_soup:
                        raw_wc = check_raw_html_word_count(final_url)
                        pages_data.append(extract_page_data(final_url, page_soup, perf=page_perf, raw_word_count=raw_wc))
                    await asyncio.sleep(0.5)

            return pages_data

        finally:
            await browser.close()


def crawl_website(base_url: str, max_pages: int = 15) -> List[dict]:
    def run_in_thread():
        import platform
        if platform.system() == "Windows":
            loop = asyncio.ProactorEventLoop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(_async_crawl_website(base_url, max_pages))
            finally:
                loop.close()
        else:
            return asyncio.run(_async_crawl_website(base_url, max_pages))

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(run_in_thread)
        return future.result()


# --------------------------------------------------------------------------
# SCORING — previously missing/disconnected. Issues were detected upstream
# but nothing converted them into the 0-100 category scores shown in the
# report, which is the root cause of pages with real problems (multiple H1s,
# thin content, slow load) still showing 100/100.
# --------------------------------------------------------------------------

ISSUE_WEIGHTS = {
    # Technical SEO
    "missing_title": ("technical", 20),
    "missing_meta_description": ("technical", 10),
    "missing_h1": ("technical", 15),
    "missing_canonical": ("technical", 8),
    "missing_lang_attribute": ("technical", 5),
    "missing_viewport_meta": ("technical", 10),
    "noindex_detected": ("technical", 30),
    "outdated_http_protocol": ("technical", 8),
    "iframes_present": ("technical", 5),
    # Content quality
    "thin_content": ("content", 20),
    "missing_alt_text": ("content", 10),
    # Metadata / structured data
    "title_length_suboptimal": ("metadata", 8),
    "meta_description_length_suboptimal": ("metadata", 8),
    "multiple_h1": ("metadata", 12),
    "missing_structured_data": ("metadata", 10),
    "missing_open_graph_tags": ("metadata", 6),
    # Performance
    "page_too_large": ("performance", 15),
    "poor_lcp": ("performance", 20),
    "poor_tti": ("performance", 15),
    "unoptimized_images": ("performance", 15),
    # GEO
    "high_js_rendering_dependency": ("geo", 25),
}


def _issue_key(issue: str) -> str:
    return issue.split(":")[0]


def score_page(page_data: dict) -> dict:
    """
    Convert detected issues into 0-100 category scores. Every deduction is
    tied to a specific measured signal in page_data — nothing is assumed.

    Two rules that matter for accuracy:
    1. A category with no underlying data (e.g. performance metrics weren't
       captured because the Playwright pass failed) is marked "unscored"
       rather than defaulting to 100 — an absence of bad news is not good
       news, and a silent 100 here is exactly the bug we're fixing.
    2. The worst category drags the overall score down harder than a flat
       average would. A simple average lets one bad category (e.g.
       performance at 40) get diluted by unrelated categories that happen
       to be fine, which is how a page with real, visible problems still
       ends up reporting "Excellent" overall.
    """
    categories = {"technical": 100, "content": 100, "metadata": 100, "performance": 100, "geo": 100}
    unscored = {"performance": page_data.get("performance") in (None, {}),
                "geo": page_data.get("rendering_gap_pct") is None}

    for issue in page_data.get("issues", []):
        key = _issue_key(issue)
        if key in ISSUE_WEIGHTS:
            category, penalty = ISSUE_WEIGHTS[key]
            categories[category] = max(0, categories[category] - penalty)

    def rating(score):
        if score >= 90:
            return "Excellent"
        if score >= 75:
            return "Good"
        if score >= 50:
            return "Needs Improvement"
        return "Poor"

    # Only average categories that actually had data to score against.
    scorable = {k: v for k, v in categories.items() if not unscored.get(k)}
    avg = sum(scorable.values()) / len(scorable) if scorable else 0
    worst = min(scorable.values()) if scorable else 0
    # Weighted toward the worst category so a single serious problem
    # (e.g. a D-grade performance score) is reflected in the headline number.
    overall = round((avg * 0.5) + (worst * 0.5), 1)

    category_scores = {
        k: ({"score": None, "rating": "Not Measured"} if unscored.get(k)
            else {"score": v, "rating": rating(v)})
        for k, v in categories.items()
    }

    return {
        "overall_score": overall,
        "overall_rating": rating(overall),
        "category_scores": category_scores,
    }


def run_crawler_agent(state: dict) -> dict:
    website_url = state.get("website_url")

    if not website_url:
        state["crawled_pages"] = []
        state["robots_txt"] = {"exists": False}
        state["sitemap"] = {"exists": False}
        state["llms_txt"] = {"exists": False}
        state["https_redirect"] = {"redirects_to_https": None}
        state["pages_crawled"] = 0
        return state

    if not website_url.startswith("http"):
        website_url = "https://" + website_url

    domain = urlparse(website_url).netloc

    robots = check_robots_txt(website_url)
    sitemap = check_sitemap(website_url)
    llms = check_llms_txt(website_url)
    https_redirect = check_https_redirect(domain)
    pages = crawl_website(website_url, max_pages=15)

    # Attach a score to every page so the report can show real numbers
    # instead of a flat 100/100 regardless of detected issues.
    for page in pages:
        page["scores"] = score_page(page)

    state["crawled_pages"] = pages
    state["robots_txt"] = robots
    state["sitemap"] = sitemap
    state["llms_txt"] = llms
    state["https_redirect"] = https_redirect
    state["pages_crawled"] = len(pages)

    if pages:
        avg_overall = round(sum(p["scores"]["overall_score"] for p in pages) / len(pages), 1)
        state["site_overall_score"] = avg_overall

    return state