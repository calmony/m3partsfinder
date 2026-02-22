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

def search_m3post(keyword: str, headers: dict = None, max_results: int = 20) -> List[Dict]:
    """Search M3Post forum (vBulletin) using search endpoint."""
    if not headers:
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
    
    items = []
    base = "https://www.m3post.com"
    
    # Use forum search endpoint with query parameters
    # vBulletin search: /forums/search.php?query=KEYWORD&forumchoice=182&searchdate=7&resultorder=lastpost
    url = f"{base}/forums/search.php?query={keyword}&forumchoice=182&searchdate=7&resultorder=lastpost"
    
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "lxml")
        
        # Find all search result links (vBulletin uses <a> tags with href containing 'showthread.php' or 'showpost.php')
        result_links = soup.find_all('a', href=lambda x: x and ('showthread.php' in x or 'showpost.php' in x))
        
        for link in result_links:
            title = link.get_text(strip=True)
            
            # Skip empty titles, navigation links, or pagination
            if not title or len(title) < 3 or title in ['«', '»', 'Previous', 'Next']:
                continue
            
            # Get thread URL and make absolute
            thread_url = link.get("href", "")
            if thread_url:
                if not thread_url.startswith("http"):
                    if thread_url.startswith("/"):
                        thread_url = base + thread_url
                    else:
                        # Relative URL needs forums/ prefix
                        thread_url = base + "/forums/" + thread_url
                
                # Extract details from thread (price + image)
                thread_details = extract_thread_details(thread_url, headers=headers)
                
                # Try to extract price from title first, then from thread content
                price = extract_price(title) or thread_details.get("price") or "Contact"
                
                # Categorize based on title and keyword
                category = categorize_by_forum_structure(title + " " + keyword)
                
                items.append({
                    "source": "forum:m3post",
                    "title": title,
                    "price": price,
                    "url": thread_url,
                    "image": thread_details.get("image"),
                    "keyword": keyword,
                    "category": category,
                })
                
                # Rate limit to avoid hammering forum
                time.sleep(0.3)
            
            if len(items) >= max_results:
                break
    
    except Exception as e:
        logger.debug(f"M3Post search error: {e}")
    
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
    """Extract price from text like '$1,500', '1500 USD', etc."""
    # Look for $XXX, $X,XXX, €XXX patterns
    match = re.search(r'[$€][\d,]+(?:\.\d{2})?', text)
    if match:
        return match.group(0)
    return None


def extract_thread_details(thread_url: str, headers: dict = None) -> Dict:
    """Fetch thread and extract price + first image from post content.
    
    Returns dict with 'price' and 'image' keys.
    """
    if not headers:
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
    
    result = {"price": None, "image": None}
    
    try:
        resp = requests.get(thread_url, headers=headers, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "lxml")
        
        # Search all text for prices (more robust than div selectors)
        all_text = soup.get_text()
        prices = re.findall(r'\$[\d,]+(?:\.\d{2})?', all_text)
        if prices:
            result["price"] = prices[0]  # Take first price found
        
        # Find first relevant image in thread
        imgs = soup.find_all('img')
        for img in imgs:
            src = img.get('src', '') or img.get('data-src', '')
            if not src:
                continue
                
            # Skip banners, icons, and forum UI elements
            skip_patterns = ['banner', 'icon', 'logo', 'nav', 'avatar', '1x1', 'spacer', 'button', 'pixel']
            if any(pattern in src.lower() for pattern in skip_patterns):
                continue
            
            # Prefer uploaded/attachment images
            if any(pattern in src.lower() for pattern in ['attachment', 'imgix', 'image', 'photo', 'upload', 'user']):
                # Make absolute URL if needed
                if src.startswith('//'):
                    src = 'https:' + src
                elif src.startswith('/'):
                    base_url = thread_url.split('/forums/')[0]
                    src = base_url + src
                elif not src.startswith('http'):
                    base_url = '/'.join(thread_url.split('/')[:3])
                    src = base_url + '/' + src
                
                result["image"] = src
                break
    
    except Exception as e:
        logger.debug(f"Failed to extract thread details from {thread_url}: {e}")
    
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
