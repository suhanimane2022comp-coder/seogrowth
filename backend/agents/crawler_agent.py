import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, urlunparse
from typing import List
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


def normalize_domain(netloc: str) -> str:
    return netloc.lower().lstrip("www.") if netloc.lower().startswith("www.") else netloc.lower()


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
            if r.status_code == 200 and "xml" in r.headers.get("Content-Type", "").lower() or "<urlset" in r.text[:500].lower():
                return {"exists": True, "url": sitemap_url}
        except Exception:
            continue
    return {"exists": False, "url": ""}


def extract_page_data(url: str, soup: BeautifulSoup) -> dict:
    title_tag = soup.find("title")
    title = title_tag.get_text(strip=True) if title_tag else None

    meta_desc_tag = soup.find("meta", attrs={"name": "description"})
    meta_description = meta_desc_tag.get("content", "").strip() if meta_desc_tag else None
    meta_description = meta_description or None

    h1_tags = [h.get_text(strip=True) for h in soup.find_all("h1") if h.get_text(strip=True)]
    h2_tags = [h.get_text(strip=True) for h in soup.find_all("h2") if h.get_text(strip=True)]
    h3_tags = [h.get_text(strip=True) for h in soup.find_all("h3") if h.get_text(strip=True)]

    images = soup.find_all("img")
    missing_alt = [img for img in images if not img.get("alt")]

    canonical_tag = soup.find("link", attrs={"rel": "canonical"})
    canonical = canonical_tag.get("href") if canonical_tag else None

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

    issues = []
    if not title:
        issues.append("missing_title")
    if not meta_description:
        issues.append("missing_meta_description")
    if len(h1_tags) == 0:
        issues.append("missing_h1")
    elif len(h1_tags) > 1:
        issues.append(f"multiple_h1:{len(h1_tags)}_found")
    if missing_alt:
        issues.append(f"missing_alt_text:{len(missing_alt)}_images")
    if word_count < 500:  # aligned to HOTH's 500-word thin-content threshold (was 300)
        issues.append(f"thin_content:{word_count}_words")
    if not canonical:
        issues.append("missing_canonical")

    return {
        "url": url,
        "title": title,
        "meta_description": meta_description,
        "h1": h1_tags[0] if h1_tags else None,
        "h1_count": len(h1_tags),  # needed so score_agent can see multiple_h1, not just truthiness
        "h2_tags": h2_tags[:10],
        "h3_tags": h3_tags[:10],
        "images_count": len(images),
        "missing_alt_count": len(missing_alt),
        "internal_links_count": len(internal_links),
        "external_links_count": len(external_links),
        "internal_links": list(set(internal_links))[:30],
        "canonical": canonical,
        "word_count": word_count,
        "body_text": body_text[:5000],
        "issues": issues,
    }


async def fetch_page_async(url: str, browser, timeout: int = 30000):
    """
    Fetch page with full JS rendering using Playwright.

    NOTE: previously this blocked images/fonts to speed up crawling. That
    block has been removed so downstream performance measurement (see
    performance_agent.py) can see the real page weight — e.g. HOTH's audit
    found 5.82MB of images on the Indmark homepage alone, which this crawler
    could never have detected while images were aborted at the network level.
    This makes each page fetch slower; that trade-off was confirmed as
    intentional in favor of accuracy.
    """
    page = None
    try:
        page = await browser.new_page(user_agent=HEADERS["User-Agent"])

        await page.goto(url, wait_until="networkidle", timeout=timeout)

        # Wait for JS to render content
        await page.wait_for_timeout(2000)

        # Extra wait if page still has very little text
        content_check = await page.evaluate("document.body.innerText.length")
        if content_check < 200:
            await page.wait_for_timeout(3000)

        html = await page.content()
        final_url = page.url
        return BeautifulSoup(html, "lxml"), final_url

    except Exception as e:
        print(f"Playwright failed to fetch {url}: {e}")
        return None, None
    finally:
        if page:
            await page.close()


async def _async_crawl_website(base_url: str, max_pages: int = 15) -> List[dict]:
    """Full async crawl using Playwright browser."""
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
                "--single-process",
                "--disable-gpu",
            ]
        )
        try:
            # Fetch homepage
            soup, resolved_url = await fetch_page_async(base_url, browser)
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
                    page_soup, final_url = soup, resolved_url
                    first = False
                else:
                    page_soup, final_url = await fetch_page_async(url, browser)
                    if not page_soup:
                        continue
                    norm = normalize_url(final_url)
                    if norm in visited and final_url != url:
                        continue
                    visited.add(norm)

                page_data = extract_page_data(final_url, page_soup)
                pages_data.append(page_data)

                print(f"Crawled: {final_url} | words: {page_data['word_count']} | h1_count: {page_data['h1_count']}")

                for link in page_data.get("internal_links", []):
                    if link not in visited and normalize_domain(urlparse(link).netloc) == base_domain:
                        to_visit.append(link)
                        visited.add(link)

                await asyncio.sleep(0.5)

            # Probe common paths if only homepage found
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
                    page_soup, final_url = await fetch_page_async(candidate, browser)
                    if page_soup:
                        pages_data.append(extract_page_data(final_url, page_soup))
                    await asyncio.sleep(0.5)

            return pages_data

        finally:
            await browser.close()


def crawl_website(base_url: str, max_pages: int = 15) -> List[dict]:
    """
    Entry point for crawling.
    Uses asyncio.run() in a new thread to avoid event loop conflicts with
    FastAPI/uvicorn on both Windows and Linux (Railway).
    """
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


def run_crawler_agent(state: dict) -> dict:
    website_url = state.get("website_url")

    if not website_url:
        state["crawled_pages"] = []
        state["robots_txt"] = {"exists": False}
        state["sitemap"] = {"exists": False}
        state["pages_crawled"] = 0
        return state

    if not website_url.startswith("http"):
        website_url = "https://" + website_url

    robots = check_robots_txt(website_url)
    sitemap = check_sitemap(website_url)
    pages = crawl_website(website_url, max_pages=15)

    state["crawled_pages"] = pages
    state["robots_txt"] = robots
    state["sitemap"] = sitemap
    state["pages_crawled"] = len(pages)

    return state