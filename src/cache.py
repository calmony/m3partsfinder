"""Cache and deduplication logic using Redis."""

import logging
import hashlib
from typing import Dict, List

logger = logging.getLogger(__name__)


class Cache:
    """In-memory cache with deduplication."""

    def __init__(self):
        self.seen_urls = set()
        self.items = {}

    def get_hash(self, url: str) -> str:
        return hashlib.md5(url.encode()).hexdigest()

    def has_seen(self, url: str) -> bool:
        return url in self.seen_urls

    def mark_seen(self, url: str):
        self.seen_urls.add(url)

    def store_item(self, item: Dict):
        url = item.get("url")
        if url:
            item_hash = self.get_hash(url)
            self.items[item_hash] = item
            self.mark_seen(url)

    def get_unseen(self, items: List[Dict]) -> List[Dict]:
        """Filter items we haven't seen before."""
        new_items = []
        for item in items:
            url = item.get("url")
            if url and not self.has_seen(url):
                new_items.append(item)
                self.mark_seen(url)
        return new_items
