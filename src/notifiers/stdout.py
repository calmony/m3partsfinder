"""Console/stdout notifier."""

import logging
from typing import List, Dict

logger = logging.getLogger(__name__)


class StdoutNotifier:
    """Print items to stdout."""

    def send_item(self, item: Dict):
        """Print a single item."""
        title = item.get("title", "Unknown")
        price = item.get("price", "N/A")
        url = item.get("url", "")
        source = item.get("source", "unknown")

        output = (
            f"\n{'='*70}\n"
            f"SOURCE: {source}\n"
            f"TITLE:  {title}\n"
            f"PRICE:  {price}\n"
            f"URL:    {url}\n"
            f"{'='*70}\n"
        )
        print(output)
        logger.info(f"Item found: {title} ({price})")

    def send_items(self, items: List[Dict]):
        """Print multiple items."""
        for item in items:
            self.send_item(item)
