import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from typing import List, Dict, Optional
import time


def fetch_page(url: str, timeout: int = 10) -> Optional[BeautifulSoup]:
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; SEOGrowthBot/1.0; +http://localhost)"
    }
    try:
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
        return BeautifulSoup(response.text, "lxml")
    except Exception as e:
        print(f"Failed to fetch {url}: {e}")
        return None


def check_robots_txt(base_url: str) -> dict:
    robots_url = urljoin(base_url, "/robots.txt")
    try:
        r = requests.get(robots_url, timeout=5)
        exists = r.status_code == 200
        return {"exists": exists, "content": r.text if exists else ""}
    except Exception:
        return {"exists": False, "content": ""}


def check_sitemap(base_url: str) -> dict:
    sitemap_url = urljoin(base_url, "/sitemap.xml")
    try:
        r = requests.get(sitemap_url, timeout=5)
        exists = r.status_code == 200
        return {"exists": exists, "url": sitemap_url if exists else ""}
    except Exception:
        return {"exists": False, "url": ""}


def extract_page_data(url: str, soup: BeautifulSoup) -> dict:
    title_tag = soup.find("title")
    title = title_tag.get_text(strip=True) if title_tag else None

    meta_desc_tag = soup.find("meta", attrs={"name": "description"})
    meta_description = meta_desc_tag.get("content", "") if meta_desc_tag else None

    h1_tags = [h.get_text(strip=True) for h in soup.find_all("h1")]
    h2_tags = [h.get_text(strip=True) for h in soup.find_all("h2")]
    h3_tags = [h.get_text(strip=True) for h in soup.find_all("h3")]

    images = soup.find_all("img")
    missing_alt = [img for img in images if not img.get("alt")]

    canonical_tag = soup.find("link", attrs={"rel": "canonical"})
    canonical = canonical_tag.get("href") if canonical_tag else None

    base_domain = urlparse(url).netloc
    all_links = soup.find_all("a", href=True)
    internal_links = []
    external_links = []
    for a in all_links:
        href = a["href"]
        full_url = urljoin(url, href)
        parsed = urlparse(full_url)
        if parsed.netloc == base_domain:
            internal_links.append(full_url)
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
        "internal_links": list(set(internal_links))[:20],
        "canonical": canonical,
        "word_count": word_count,
        "body_text": body_text[:5000],
        "issues": issues
    }


def crawl_website(base_url: str, max_pages: int = 10) -> List[dict]:
    parsed = urlparse(base_url)
    base_domain = parsed.netloc
    visited = set()
    to_visit = [base_url]
    pages_data = []

    while to_visit and len(visited) < max_pages:
        url = to_visit.pop(0)
        if url in visited:
            continue
        visited.add(url)

        soup = fetch_page(url)
        if not soup:
            continue

        page_data = extract_page_data(url, soup)
        pages_data.append(page_data)

        # Add internal links to crawl queue
        for link in page_data.get("internal_links", []):
            if link not in visited and urlparse(link).netloc == base_domain:
                to_visit.append(link)

        time.sleep(0.5)  # Be polite

    return pages_data


def run_crawler_agent(state: dict) -> dict:
    website_url = state.get("website_url")

    if not website_url:
        state["crawled_pages"] = []
        state["robots_txt"] = {"exists": False}
        state["sitemap"] = {"exists": False}
        state["pages_crawled"] = 0
        return state

    # Ensure URL has scheme
    if not website_url.startswith("http"):
        website_url = "https://" + website_url

    robots = check_robots_txt(website_url)
    sitemap = check_sitemap(website_url)
    pages = crawl_website(website_url, max_pages=10)

    state["crawled_pages"] = pages
    state["robots_txt"] = robots
    state["sitemap"] = sitemap
    state["pages_crawled"] = len(pages)

    return state
