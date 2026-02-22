"""SMS notifier using Twilio."""

import os
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)


class SMSNotifier:
    """Send SMS alerts via Twilio."""

    def __init__(self):
        self.account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        self.auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        self.from_phone = os.getenv("TWILIO_FROM_PHONE")
        self.to_phone = os.getenv("ALERT_PHONE")
        self.enabled = all([self.account_sid, self.auth_token, self.from_phone, self.to_phone])

        if self.enabled:
            try:
                from twilio.rest import Client
                self.client = Client(self.account_sid, self.auth_token)
            except ImportError:
                logger.warning("Twilio not installed, SMS disabled")
                self.enabled = False

    def send_item(self, item: Dict):
        """Send a single item as SMS."""
        if not self.enabled:
            return

        title = item.get("title", "Unknown")[:50]  # Truncate for SMS
        price = item.get("price", "N/A")
        url = item.get("url", "")
        source = item.get("source", "unknown")

        body = f"[{source}] {title} - {price}\n{url}"
        
        try:
            msg = self.client.messages.create(
                body=body,
                from_=self.from_phone,
                to=self.to_phone
            )
            logger.info(f"SMS sent: {msg.sid}")
        except Exception as e:
            logger.error(f"Failed to send SMS: {e}")

    def send_items(self, items: List[Dict]):
        """Send multiple items as SMS (batched)."""
        for item in items:
            self.send_item(item)
