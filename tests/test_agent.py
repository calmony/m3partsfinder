"""Tests for the parts finder agent."""

import pytest
from src.cache import Cache
from src.sources.ebay import search_ebay
from src.notifiers import StdoutNotifier


class TestCache:
    """Test caching and deduplication."""

    def test_mark_seen(self):
        cache = Cache()
        url = "https://example.com/item1"
        assert not cache.has_seen(url)
        cache.mark_seen(url)
        assert cache.has_seen(url)

    def test_get_unseen(self):
        cache = Cache()
        items = [
            {"url": "https://example.com/1", "title": "Item 1"},
            {"url": "https://example.com/2", "title": "Item 2"},
        ]
        
        # All items should be new
        unseen = cache.get_unseen(items)
        assert len(unseen) == 2
        
        # Fetch again, should be empty
        unseen = cache.get_unseen(items)
        assert len(unseen) == 0


class TestNotifiers:
    """Test notifier behavior."""

    def test_stdout_notifier(self, capsys):
        notifier = StdoutNotifier()
        item = {
            "source": "ebay",
            "title": "Test Part",
            "price": "$100",
            "url": "https://example.com"
        }
        notifier.send_item(item)
        # Just verify it doesn't crash


class TestEbayScraper:
    """Test eBay scraper (network tests)."""

    @pytest.mark.skip(reason="Requires network access")
    def test_search_ebay_real(self):
        """Integration test against real eBay."""
        results = search_ebay("Meistershaft exhaust")
        assert isinstance(results, list)
        if results:
            assert all("source" in r for r in results)
            assert all("url" in r for r in results)
