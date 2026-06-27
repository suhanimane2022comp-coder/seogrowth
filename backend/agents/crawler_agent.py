import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, urlunparse
from typing import List
import time
import os

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 SEOGrowthBot/1.0"
}

COMMON_PATHS = [
    "/contact", "/contact-us", "/about", "/about-us", "/services",
    "/pricing", "/faq", "/blog", "/privacy-policy", "/terms",
]

SCRAPER_API_KEY = os.getenv("SCRAPER_API_KEY", "")


def normalize_domain(netloc: str) -> str:
    return netloc.lower().lstrip("www.") if netloc.lower().startswith("www.") else netloc.lower()


def normalize_url(url: str) -> str:
    parsed = urlparse(url)
    path = parsed.path.rstrip("/") or "/"
    netloc = normalize_domain(parsed.netloc)
    return urlunparse((parsed.scheme, netloc, path, parsed.params, parsed.query, ""))


def fetch_page(url: str, timeout: int = 30):
    """
    Fetch page with JS rendering via ScraperAPI if key is available,
    otherwise fall back to plain requests.
    Returns (soup, final_url) or (None, None) on failure.
    """
    try:
        if SCRAPER_API_KEY:
            # ScraperAPI renders JavaScript — same result as Playwright
            api_url = "http://api.scraperapi.com"
            params = {
                "api_key": SCRAPER_API_KEY,
                "url": url,
                "render": "true",  # enables JS rendering
            }
            response = requests.get(api_url, params=params, timeout=timeout)
        else:
            # Local development fallback (no JS rendering)
            response = requests.get(url, headers=HEADERS, timeout=timeout, allow_redirects=True)

        if response.status_code == 200:
            return BeautifulSoup(response.text, "lxml"), url
        return None, None
    except Exception as e:
        print(f"Failed to fetch {url}: {e}")
        return None, None


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
        issues.append("multiple_h1")
    if missing_alt:
        issues.append(f"missing_alt_text:{len(missing_alt)}_images")
    if word_count < 300:
        issues.append("thin_content")
    if not canonical:
        issues.append("missing_canonical")

    return {
        "url": url,
        "title": title,
        "meta_description": meta_description,
        "h1": h1_tags[0] if h1_tags else None,
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
        "issues": issues
    }


def crawl_website(base_url: str, max_pages: int = 15) -> List[dict]:
    soup, resolved_url = fetch_page(base_url)
    if not soup:
        return []

    base_domain = normalize_domain(urlparse(resolved_url).netloc)
    visited = set()
    pages_data = []

    to_visit = [resolved_url]
    visited.add(normalize_url(resolved_url))

    first = True
    while to_visit and len(visited) <= max_pages:
        url = to_visit.pop(0)

        if first:
            page_soup, final_url = soup, resolved_url
            first = False
        else:
            page_soup, final_url = fetch_page(url)
            if not page_soup:
                continue
            norm = normalize_url(final_url)
            if norm in visited and final_url != url:
                continue
            visited.add(norm)

        page_data = extract_page_data(final_url, page_soup)
        pages_data.append(page_data)

        for link in page_data.get("internal_links", []):
            if link not in visited and normalize_domain(urlparse(link).netloc) == base_domain:
                to_visit.append(link)
                visited.add(link)

        time.sleep(1)  # ScraperAPI needs slightly more breathing room

    if len(pages_data) <= 1:
        for path in COMMON_PATHS:
            if len(pages_data) >= max_pages:
                break
            candidate = urljoin(f"https://{urlparse(resolved_url).netloc}", path)
            norm = normalize_url(candidate)
            if norm in visited:
                continue
            visited.add(norm)
            page_soup, final_url = fetch_page(candidate)
            if page_soup:
                pages_data.append(extract_page_data(final_url, page_soup))
            time.sleep(1)

    return pages_data


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