"""Forum scraper for BMW E9x and M3 communities."""

import logging
import requests
from bs4 import BeautifulSoup
from typing import List, Dict
import time
import re

logger = logging.getLogger(__name__)

# Popular E9x/M3 forum targets
FORUMS = [
    {
        "name": "m3post",
        "base_url": "https://www.m3post.com",
        "forum_id": 182,  # E9x M3 parts/sales section
        "type": "vbulletin",
    },
    {
        "name": "e90post",
        "base_url": "https://www.e90post.com",
        "search_endpoint": "/forums/search/",
        "type": "generic",
    },
    {
        "name": "m3cutters",
        "base_url": "https://www.m3cutters.com",
        "search_endpoint": "/forum/search.php",
        "type": "generic",
    },
    {
        "name": "bimmerpost",
        "base_url": "https://www.bimmerpost.com",
        "search_endpoint": "/forums/search/",
        "type": "generic",
    },
]

# M3Post forum categories (from their site structure)
M3POST_CATEGORIES = {
    "exterior": "Exterior",
    "cosmetic": "Exterior",
    "wheel": "Wheels",
    "tire": "Wheels",
    "suspension": "Suspension",
    "brake": "Suspension",
    "chassis": "Suspension",
    "spacer": "Suspension",
    "interior": "Interior",
    "engine": "Engine",
    "drivetrain": "Engine",
    "exhaust": "Engine",
    "electronic": "Electronics",
    "audio": "Electronics",
    "video": "Electronics",
    "phone": "Electronics",
    "navigation": "Electronics",
    "detailing": "Detailing",
    "wash": "Detailing",
    "wax": "Detailing",
}

def categorize_by_forum_structure(title: str) -> str:
    """Categorize based on M3Post forum structure."""
    title_lower = title.lower()

    for keyword, category in M3POST_CATEGORIES.items():
        if keyword in title_lower:
            return category

    return "Other"


# Browser-like headers for forum requests (forums block bot user agents)
_BROWSER_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}


def _normalize_thread_url(url: str) -> str:
    """Normalize a vBulletin thread URL for deduplication.

    Strips page numbers, post anchors, and highlight params so that
    different links to the same thread resolve to one canonical URL.

    Args:
        url: Raw thread URL.

    Returns:
        Canonical URL string.
    """
    # Extract thread ID from showthread.php?t=XXXXX or showthread.php?p=XXXXX
    thread_match = re.search(r'showthread\.php\?t=(\d+)', url)
    if thread_match:
        base = url.split('/forums/')[0] if '/forums/' in url else 'https://www.m3post.com'
        return f"{base}/forums/showthread.php?t={thread_match.group(1)}"
    return url.split('#')[0].split('&highlight=')[0]


# Module-level cache so multiple keyword searches reuse the same listing
_m3post_listing_cache: Dict = {
    'threads': [],
    'timestamp': 0.0,
}

_M3POST_CACHE_TTL = 300  # seconds


def _fetch_m3post_listing_page(page_num: int, headers: dict) -> List[Dict]:
    """Fetch one page of the M3Post FS/FT forum listing.

    Args:
        page_num: 1-based page number.
        headers: HTTP headers for the request.

    Returns:
        List of dicts with 'title' and 'url' keys.
    """
    base = "https://www.m3post.com"
    url = f"{base}/forums/forumdisplay.php?f=182&order=desc&page={page_num}"
    threads: List[Dict] = []

    try:
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "lxml")

        # vBulletin 3.x: thread title links have id="thread_title_XXXX"
        thread_links = soup.find_all(
            'a', id=lambda x: x and x.startswith('thread_title_')
        )

        if not thread_links:
            # Fallback: links inside the threads table
            thread_links = soup.select('#threadslist a[href*="showthread.php"]')

        if not thread_links:
            # Broadest fallback
            thread_links = soup.find_all(
                'a', href=lambda x: x and 'showthread.php' in x
            )

        seen_urls: set = set()
        for link in thread_links:
            title = link.get_text(strip=True)
            if not title or len(title) < 5:
                continue
            if title in ('«', '»', 'Previous', 'Next', 'First', 'Last'):
                continue

            raw_url = link.get('href', '')
            if not raw_url:
                continue

            # Make absolute
            if not raw_url.startswith('http'):
                if raw_url.startswith('/'):
                    raw_url = base + raw_url
                else:
                    raw_url = base + '/forums/' + raw_url

            canonical = _normalize_thread_url(raw_url)
            if canonical in seen_urls:
                continue
            seen_urls.add(canonical)

            threads.append({'title': title, 'url': canonical})

    except Exception as e:
        logger.warning(f"Failed to fetch M3Post listing page {page_num}: {e}")

    return threads


def _get_m3post_threads(headers: dict, pages: int = 3) -> List[Dict]:
    """Return M3Post forum threads, using a short-lived cache.

    Args:
        headers: HTTP headers.
        pages: Number of listing pages to scrape.

    Returns:
        List of thread dicts with 'title' and 'url' keys.
    """
    now = time.time()
    cache = _m3post_listing_cache

    if cache['threads'] and (now - cache['timestamp']) < _M3POST_CACHE_TTL:
        logger.debug("Using cached M3Post threads (%d threads)", len(cache['threads']))
        return cache['threads']

    all_threads: List[Dict] = []
    seen_urls: set = set()

    for page_num in range(1, pages + 1):
        page_threads = _fetch_m3post_listing_page(page_num, headers)
        for t in page_threads:
            if t['url'] not in seen_urls:
                seen_urls.add(t['url'])
                all_threads.append(t)
        logger.debug("M3Post page %d: %d threads", page_num, len(page_threads))

        if not page_threads:
            break
        if page_num < pages:
            time.sleep(0.5)

    cache['threads'] = all_threads
    cache['timestamp'] = now
    logger.info("Cached %d M3Post threads from %d pages", len(all_threads), pages)
    return all_threads


def search_m3post(keyword: str, headers: dict = None, max_results: int = 20) -> List[Dict]:
    """Search M3Post forum by scraping the FS/FT listing and filtering by keyword.

    Uses the forum listing page (forumdisplay.php) instead of the search
    endpoint, which is more reliable and avoids vBulletin search
    session/cookie requirements.

    Args:
        keyword: Search term to match in thread titles.
        headers: HTTP headers (a browser-like UA is always used for forums).
        max_results: Maximum number of results to return.

    Returns:
        List of item dicts ready for database insertion.
    """
    # Always use browser-like headers for forum requests
    req_headers = dict(_BROWSER_HEADERS)
    if headers:
        # Keep any extra headers but override User-Agent
        for k, v in headers.items():
            if k.lower() != 'user-agent':
                req_headers[k] = v

    items: List[Dict] = []
    base = "https://www.m3post.com"

    # --- Strategy 1: Scrape forum listing pages and filter by keyword ---
    all_threads = _get_m3post_threads(req_headers, pages=3)
    keyword_lower = keyword.lower()

    matching_threads = [
        t for t in all_threads
        if keyword_lower in t['title'].lower()
    ]
    logger.info(
        "M3Post: %d/%d threads match keyword '%s'",
        len(matching_threads), len(all_threads), keyword,
    )

    seen_urls: set = set()
    for thread in matching_threads:
        if len(items) >= max_results:
            break

        canonical = _normalize_thread_url(thread['url'])
        if canonical in seen_urls:
            continue
        seen_urls.add(canonical)

        # Fetch thread page for price + image
        thread_details = extract_thread_details(canonical, headers=req_headers)

        price = (
            extract_price(thread['title'])
            or thread_details.get("price")
            or "Contact"
        )
        category = categorize_by_forum_structure(thread['title'] + " " + keyword)

        items.append({
            "source": "forum:m3post",
            "title": thread['title'],
            "price": price,
            "url": canonical,
            "image": thread_details.get("image"),
            "keyword": keyword,
            "category": category,
        })

        time.sleep(0.3)

    # --- Strategy 2: Fall back to search.php if listing produced nothing ---
    if not items:
        logger.debug("M3Post listing returned 0 matches for '%s', trying search", keyword)
        search_url = (
            f"{base}/forums/search.php?query={keyword}"
            f"&forumchoice=182&searchdate=7&resultorder=lastpost"
        )
        try:
            resp = requests.get(search_url, headers=req_headers, timeout=15)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "lxml")

            result_links = soup.find_all(
                'a', href=lambda x: x and 'showthread.php' in x
            )

            for link in result_links:
                if len(items) >= max_results:
                    break

                title = link.get_text(strip=True)
                if not title or len(title) < 5:
                    continue
                if title in ('«', '»', 'Previous', 'Next', 'First', 'Last'):
                    continue

                raw_url = link.get("href", "")
                if not raw_url:
                    continue
                if not raw_url.startswith("http"):
                    if raw_url.startswith("/"):
                        raw_url = base + raw_url
                    else:
                        raw_url = base + "/forums/" + raw_url

                canonical = _normalize_thread_url(raw_url)
                if canonical in seen_urls:
                    continue
                seen_urls.add(canonical)

                thread_details = extract_thread_details(canonical, headers=req_headers)
                price = (
                    extract_price(title)
                    or thread_details.get("price")
                    or "Contact"
                )
                category = categorize_by_forum_structure(title + " " + keyword)

                items.append({
                    "source": "forum:m3post",
                    "title": title,
                    "price": price,
                    "url": canonical,
                    "image": thread_details.get("image"),
                    "keyword": keyword,
                    "category": category,
                })

                time.sleep(0.3)

        except Exception as e:
            logger.debug("M3Post search fallback error: %s", e)

    return items


def search_generic_forum(forum: dict, keyword: str, headers: dict = None, max_results: int = 10) -> List[Dict]:
    """Search a generic forum type (e90post, m3cutters, bimmerpost)."""
    if not headers:
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

    items = []
    base = forum["base_url"]
    search_ep = forum.get("search_endpoint", "/forums/search/")
    
    try:
        # Build search URL
        params = {"q": keyword}
        search_url = base.rstrip("/") + search_ep
        resp = requests.get(search_url, params=params, headers=headers, timeout=15)
        resp.raise_for_status()
        
        soup = BeautifulSoup(resp.text, "lxml")
        
        # Generic selectors for forum results
        threads = soup.select("tr.alt1, tr.alt2, div.post, article, li.searchresult")
        
        for thread in threads[:max_results]:
            # Find title link
            title_el = thread.select_one("a[href*='showthread'], a[href*='viewtopic'], h3 a, .title a")
            if not title_el:
                continue
            
            title = title_el.get_text(strip=True)
            thread_url = title_el.get("href", "")
            
            # Make absolute URL
            if thread_url and not thread_url.startswith("http"):
                thread_url = base.rstrip("/") + "/" + thread_url.lstrip("/")
            
            if thread_url:
                price = extract_price(title)
                
                # Categorize based on title and keyword
                category = categorize_by_forum_structure(title + " " + keyword)
                
                items.append({
                    "source": f"forum:{forum['name']}",
                    "title": title,
                    "price": price or "Contact",
                    "url": thread_url,
                    "image": None,
                    "keyword": keyword,
                    "category": category,
                })
    
    except Exception as e:
        logger.debug(f"Forum {forum['name']} search error: {e}")
    
    return items


def extract_price(text: str) -> str:
    """Extract price from text like '$1,500', '1500 USD', 'asking 1500', etc.

    Args:
        text: Text to search for price patterns.

    Returns:
        Price string or None if no price found.
    """
    # Pattern 1: $XXX or €XXX with optional cents
    match = re.search(r'[$€][\d,]+(?:\.\d{2})?', text)
    if match:
        return match.group(0)

    # Pattern 2: "1500 USD", "1500 obo", "asking 1500", "price 1500"
    match = re.search(
        r'(?:asking|price|obo|shipped)\s*:?\s*(\d[\d,]*)',
        text, re.IGNORECASE,
    )
    if match:
        return f"${match.group(1)}"

    # Pattern 3: number followed by price-related word
    match = re.search(r'(\d[\d,]+)\s*(?:USD|obo|shipped|firm)', text, re.IGNORECASE)
    if match:
        return f"${match.group(1)}"

    return None


def extract_thread_details(thread_url: str, headers: dict = None) -> Dict:
    """Fetch a thread page and extract the first price and image from post content.

    Looks inside the first post's content area (vBulletin ``post_message_*``
    div or ``alt1`` cell) so that navigation chrome, avatars, and other UI
    images are ignored.

    Args:
        thread_url: Full URL of the thread.
        headers: HTTP headers for the request.

    Returns:
        Dict with 'price' (str|None) and 'image' (str|None) keys.
    """
    if not headers:
        headers = dict(_BROWSER_HEADERS)

    result: Dict = {"price": None, "image": None}

    try:
        resp = requests.get(thread_url, headers=headers, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "lxml")

        # --- Price extraction ---
        # Look in the first post content div for prices
        first_post = (
            soup.find('div', id=lambda x: x and x.startswith('post_message_'))
            or soup.find('div', class_='postcontent')
            or soup.find('blockquote', class_='postcontent')
        )
        price_text = first_post.get_text() if first_post else soup.get_text()
        price = extract_price(price_text)
        if price:
            result["price"] = price

        # --- Image extraction ---
        # Narrow the search to the first post content area when possible
        search_area = first_post if first_post else soup

        # vBulletin UI patterns to skip (icons, smilies, status indicators, etc.)
        skip_patterns = [
            'banner', 'icon', 'logo', 'nav', 'avatar',
            '1x1', 'spacer', 'button', 'pixel',
            'smilie', 'smiley', 'emoji', 'emoticon',
            'statusicon', 'inlinemod', 'reputation',
            'clear.gif', '/misc/', '/buttons/',
            '/icons/', 'progress_bar', 'rank',
            'forum_old', 'collapse_', 'postcount',
            'vbulletin_css', '/images/ranks/',
        ]

        imgs = search_area.find_all('img')
        for img in imgs:
            src = img.get('src', '') or img.get('data-src', '')
            if not src:
                continue

            src_lower = src.lower()

            # Skip known UI / tiny images
            if any(p in src_lower for p in skip_patterns):
                continue

            # Skip images with very small dimensions
            try:
                w = img.get('width', '')
                h = img.get('height', '')
                if w and int(str(w).replace('px', '')) < 50:
                    continue
                if h and int(str(h).replace('px', '')) < 50:
                    continue
            except (ValueError, TypeError):
                pass

            # Make absolute URL
            if src.startswith('//'):
                src = 'https:' + src
            elif src.startswith('/'):
                base_url = '/'.join(thread_url.split('/')[:3])
                src = base_url + src
            elif not src.startswith('http'):
                base_url = '/'.join(thread_url.split('/')[:3])
                src = base_url + '/' + src

            result["image"] = src
            break

    except Exception as e:
        logger.debug("Failed to extract thread details from %s: %s", thread_url, e)

    return result


def search_forum(forum: dict, keyword: str, headers: dict = None, max_results: int = 10) -> List[Dict]:
    """Search a single forum by type."""
    if forum.get("type") == "vbulletin" and forum.get("name") == "m3post":
        return search_m3post(keyword, headers=headers, max_results=max_results)
    else:
        return search_generic_forum(forum, keyword, headers=headers, max_results=max_results)


def search_forums(keyword: str, headers: dict = None, max_results: int = 20) -> List[Dict]:
    """Search E9x/M3 forums for keyword.
    
    Args:
        keyword: Search term
        headers: HTTP headers
        max_results: Max total results across all forums
    
    Returns:
        List of forum threads matching keyword
    """
    results = []
    for forum in FORUMS:
        forum_results = search_forum(forum, keyword, headers=headers, max_results=max_results // len(FORUMS) + 2)
        results.extend(forum_results)
        time.sleep(0.5)  # Rate limit between forums

    return results[:max_results]
