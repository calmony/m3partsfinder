"""Facebook Marketplace scraper (placeholder).

NOTE: Full Facebook Marketplace scraping is challenging because:
- JavaScript-heavy rendering (requires Selenium/Playwright)
- Most public content requires authentication
- ToS may restrict automated scraping
- Anti-bot measures and rate limiting

For production, consider:
1. Using Meta's official Graph API (requires business approval)
2. Browser automation (Selenium/Playwright) with headless browser
3. Manual RSS feeds or integration with marketplace aggregators
"""

import logging
from typing import List, Dict

logger = logging.getLogger(__name__)


def search_facebook(keyword: str, headers: dict = None, max_results: int = 10) -> List[Dict]:
    """Placeholder for Facebook Marketplace search.
    
    Args:
        keyword: Search term
        headers: HTTP headers
        max_results: Max results to return
    
    Returns:
        Empty list (not implemented)
    """
    logger.info(
        f"Facebook Marketplace search for '{keyword}' not yet implemented. "
        "Consider using official APIs or browser automation."
    )
    return []
