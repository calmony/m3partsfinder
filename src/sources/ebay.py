"""eBay parts searcher using official Browse REST API."""

import logging
import requests
import base64
from typing import List, Dict
from urllib.parse import urlencode
import os
from pathlib import Path

logger = logging.getLogger(__name__)

# Load environment variables
from dotenv import load_dotenv
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path)

EBAY_CLIENT_ID = os.getenv("EBAY_CLIENT_ID")
EBAY_CLIENT_SECRET = os.getenv("EBAY_CLIENT_SECRET")
EBAY_ENV = os.getenv("EBAY_ENVIRONMENT", "PRODUCTION")

# Environment URLs
EBAY_API_URLS = {
    "SANDBOX": "https://api.sandbox.ebay.com",
    "PRODUCTION": "https://api.ebay.com"
}

EBAY_BASE_URL = EBAY_API_URLS.get(EBAY_ENV, EBAY_API_URLS["PRODUCTION"])


class eBayAuthenticator:
    """Handles eBay OAuth authentication."""
    
    def __init__(self):
        self.client_id = EBAY_CLIENT_ID
        self.client_secret = EBAY_CLIENT_SECRET
        self.access_token = None
    
    def get_access_token(self) -> str:
        """Get OAuth access token using Client Credentials flow."""
        if not self.client_id or not self.client_secret:
            logger.error("eBay API credentials not configured in .env file")
            return None
        
        # Use /identity/oauth2/token endpoint (official eBay docs)
        auth_url = f"{EBAY_API_URLS.get(EBAY_ENV)}/identity/oauth2/token"
        
        # Create Basic Auth header
        credentials = f"{self.client_id}:{self.client_secret}"
        encoded = base64.b64encode(credentials.encode()).decode()
        
        headers = {
            "Authorization": f"Basic {encoded}",
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "M3PartsFinder/1.0"
        }
        
        data = {"grant_type": "client_credentials", "scope": "https://api.ebay.com/oauth/api_scope"}
        
        try:
            resp = requests.post(auth_url, headers=headers, data=data, timeout=10)
            resp.raise_for_status()
            self.access_token = resp.json().get("access_token")
            logger.info(f"eBay authentication successful ({EBAY_ENV})")
            return self.access_token
        except Exception as e:
            logger.error(f"eBay authentication failed: {e}")
            return None


def search_ebay(keyword: str, headers: dict = None, max_results: int = 20) -> List[Dict]:
    """Search eBay for parts using Browse API.
    
    Args:
        keyword: Search term (e.g., "E90 exhaust")
        headers: Unused (for API compatibility)
        max_results: Maximum number of results to return
    
    Returns:
        List of dicts with keys: source, title, price, url, image, keyword
    """
    authenticator = eBayAuthenticator()
    access_token = authenticator.get_access_token()
    
    if not access_token:
        logger.warning(f"Could not authenticate with eBay API")
        return []
    
    # Build search query
    # "E9X" category for BMW E90/E92/E93 M3 parts
    search_query = f"{keyword} E9X M3"
    
    browse_url = f"{EBAY_BASE_URL}/buy/browse/v1/item_summary/search"
    
    params = {
        "q": search_query,
        "limit": max_results,
        "sort": "newlyListed",  # Sort by newly listed
        "filter": "buyingOptions:{AUCTION|FIXED_PRICE}",  # Include both auction and fixed price
    }
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Language": "en-US",
        "User-Agent": "M3PartsFinder/1.0"
    }
    
    items = []
    try:
        url = f"{browse_url}?{urlencode(params)}"
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        
        for item in data.get("itemSummaries", []):
            # Extract item details
            item_id = item.get("itemId")
            title = item.get("title", "Unknown")
            price_info = item.get("price", {})
            price = price_info.get("value", "N/A")
            currency = price_info.get("currency", "USD")
            
            # Build eBay item URL
            item_url = f"https://www.ebay.com/itm/{item_id}"
            
            # Get image
            image = None
            image_list = item.get("image", {})
            if isinstance(image_list, dict):
                image = image_list.get("imageUrl")
            elif isinstance(image_list, list) and image_list:
                image = image_list[0].get("imageUrl") if isinstance(image_list[0], dict) else image_list[0]
            
            # Get condition
            condition = item.get("condition", "Unknown")
            
            items.append({
                "source": "ebay",
                "title": title,
                "price": f"{price} {currency}",
                "url": item_url,
                "image": image,
                "keyword": keyword,
                "condition": condition,
                "item_id": item_id,
            })
        
        logger.info(f"eBay search '{keyword}': {len(items)} results")
        
    except Exception as e:
        logger.error(f"eBay Browse API error for '{keyword}': {e}")
    
    return items
