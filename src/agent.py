"""Main agent orchestrator."""

import logging
import yaml
from pathlib import Path
from typing import List, Dict
import schedule
import time

from src.sources import search_ebay, search_forums, search_facebook, scrape_m3post_sections
from src.cache import Cache
from src.notifiers import SMSNotifier, StdoutNotifier
from src import db

logger = logging.getLogger(__name__)

CONFIG_PATH = Path(__file__).parent / "config.yaml"


class Agent:
    """Main parts-finding agent that orchestrates searches and notifications."""

    def __init__(self, config_path: str = None):
        self.config_path = config_path or CONFIG_PATH
        self.config = self._load_config()
        self.cache = Cache()
        self.notifiers = self._init_notifiers()
        self.headers = {
            "User-Agent": self.config.get("user_agent", "Mozilla/5.0")
        }

    def _load_config(self) -> dict:
        """Load configuration from YAML."""
        try:
            with open(self.config_path, "r") as f:
                cfg = yaml.safe_load(f)
            logger.info(f"Loaded config from {self.config_path}")
            return cfg
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return {}

    def _init_notifiers(self) -> List:
        """Initialize configured notifiers."""
        notifiers = []
        cfg = self.config.get("notifications", {})
        
        if cfg.get("sms_enabled"):
            notifiers.append(SMSNotifier())
        
        if cfg.get("stdout_enabled", True):
            notifiers.append(StdoutNotifier())
        
        return notifiers

    def search_all_sources(self) -> List[Dict]:
        """Search all configured sources."""
        results = []
        keywords = self.config.get("parts", [])

        # --- M3Post: scrape all threads from configured forum sections ---
        # This runs once per cycle (not per keyword) and grabs everything,
        # skipping posts without a price.
        try:
            m3post_results = scrape_m3post_sections(headers=self.headers)
            results.extend(m3post_results)
            logger.info(f"M3Post sections: {len(m3post_results)} results")
        except Exception as e:
            logger.error(f"M3Post section scrape failed: {e}")

        if not keywords:
            logger.warning("No parts configured in config.yaml")
            return results

        # --- Keyword-based searches (eBay, other forums, Facebook) ---
        for keyword in keywords:
            logger.info(f"Searching for: {keyword}")

            # eBay
            try:
                ebay_results = search_ebay(keyword, headers=self.headers)
                results.extend(ebay_results)
                logger.info(f"  eBay: {len(ebay_results)} results")
            except Exception as e:
                logger.error(f"  eBay search failed: {e}")

            # Other forums (e90post, m3cutters, bimmerpost — m3post handled above)
            try:
                forum_results = search_forums(keyword, headers=self.headers)
                results.extend(forum_results)
                logger.info(f"  Forums: {len(forum_results)} results")
            except Exception as e:
                logger.error(f"  Forum search failed: {e}")

            # Facebook (placeholder)
            try:
                fb_results = search_facebook(keyword, headers=self.headers)
                results.extend(fb_results)
                logger.info(f"  Facebook: {len(fb_results)} results")
            except Exception as e:
                logger.error(f"  Facebook search failed: {e}")

        return results

    def run_once(self):
        """Execute a single search cycle."""
        logger.info("Starting search cycle...")
        results = self.search_all_sources()
        logger.info(f"Total results: {len(results)}")
        
        # Filter for new items
        new_items = self.cache.get_unseen(results)
        logger.info(f"New items: {len(new_items)}")
        
        # Save to database
        db.init_db()
        saved_count = db.add_items(new_items)
        logger.info(f"Saved {saved_count} new items to database")
        
        # Notify for new items
        if new_items:
            for notifier in self.notifiers:
                try:
                    notifier.send_items(new_items)
                except Exception as e:
                    logger.error(f"Notification failed: {e}")

    def schedule_runs(self):
        """Schedule recurring searches (requires external run loop)."""
        interval_secs = self.config.get("search_interval", 1800)
        schedule.every(interval_secs).seconds.do(self.run_once)
        logger.info(f"Scheduled searches every {interval_secs} seconds")

    def run_scheduled(self):
        """Blocking loop for scheduled searches."""
        self.schedule_runs()
        while True:
            schedule.run_pending()
            time.sleep(1)
