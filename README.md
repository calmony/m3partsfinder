# BMW E9X M3 Parts Finder Agent

An intelligent agent that searches eBay, forums, and Facebook Marketplace for deals on BMW E9X M3 parts, with a beautiful web dashboard to browse and share results with friends.

## Features

- **Multi-source search**: eBay, popular E9x/M3 forums (e90post, m3cutters, bimmerpost)
- **Web Dashboard**: Beautiful, responsive dashboard to browse all found parts
- **Database persistence**: SQLite stores all discovered items
- **Smart deduplication**: URL-based cache prevents duplicate alerts
- **Flexible notifications**: SMS (Twilio), stdout, extensible design
- **Scheduled searches**: Runs continuously at configurable intervals
- **Search & Filter**: Find specific parts, view recent finds, archive items
- **Keyword-based**: Search for specific parts (exhaust, brakes, suspension, etc.)
- **Rate-limited**: Respects site limits with configurable delays

## Quick Start

### 1. Install Dependencies

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure

Edit `src/config.yaml` to customize:

```yaml
regions:
  - US

parts:
  - Meistershaft exhaust
  - M3 brakes
  - E9x suspension

search_interval: 1800  # 30 minutes
notifications:
  sms_enabled: true
  stdout_enabled: true
```

### 3. (Optional) Setup SMS Alerts

Set environment variables for Twilio:

```bash
export TWILIO_ACCOUNT_SID=your_sid
export TWILIO_AUTH_TOKEN=your_token
export TWILIO_FROM_PHONE=+1234567890
export ALERT_PHONE=+0987654321
```

### 4. Run

**Single search:**
```bash
python main.py search
```

**Continuous daemon (searches every 30 min):**
```bash
python main.py daemon
```

**Web dashboard (http://localhost:5000):**
```bash
python main.py web
```

**Run both (use two terminals):**
```bash
# Terminal 1: Start agent daemon
python main.py daemon

# Terminal 2: Start web server
python main.py web
```

Then visit http://localhost:5000 to see all discovered parts. Share this link with friends!

## Web Dashboard

The web interface provides:

- **All Parts**: Browse complete inventory of discovered deals
- **Last 24h**: Filter to show only recent finds
- **Search**: Look for specific parts by name
- **Stats**: View database statistics and agent info
- **Archive**: Mark items as "seen" to hide them

### Features

- Real-time updates as the agent finds new parts
- Direct links to original listings (eBay, forums, etc.)
- Item images and pricing
- Responsive design (mobile-friendly)
- Share dashboard link with friends

## Architecture

```
src/
├── agent.py          # Main orchestrator
├── cache.py          # Deduplication logic
├── db.py             # SQLite persistence
├── web.py            # Flask web app
├── config.yaml       # Configuration
├── sources/          # Search adapters
│   ├── ebay.py       # eBay scraper
│   ├── forum.py      # Forum scraper
│   └── facebook.py   # FB placeholder
├── notifiers/        # Alert adapters
│   ├── sms.py        # Twilio SMS
│   └── stdout.py     # Console output
├── templates/        # HTML templates
│   ├── base.html     # Base layout
│   ├── index.html    # All parts
│   ├── recent.html   # Recent finds
│   ├── search.html   # Search page
│   ├── stats.html    # Statistics
│   └── error pages
└── static/           # CSS, JS, images (future)
```

## Data Sources

### eBay
- Public search via web scraping (BeautifulSoup)
- Returns title, price, image, URL
- Sorted by most recent

### Forums
Searches popular BMW/M3 communities:
- **e90post.com** - Largest E90/E92 community
- **m3cutters.com** - M3-focused forum
- **bimmerpost.com** - General BMW parts discussions

### Facebook Marketplace
- **Currently a placeholder** - FB is JavaScript-heavy and requires authentication
- Future: Consider Selenium/Playwright or official Meta APIs

## Database

Items are stored in `parts.db` (SQLite) with the following schema:

```sql
CREATE TABLE items (
    id INTEGER PRIMARY KEY,
    source TEXT,           -- 'ebay', 'forum:e90post', etc.
    title TEXT,            -- Item title
    price TEXT,            -- Price (if available)
    url TEXT UNIQUE,       -- Unique identifier
    image TEXT,            -- Image URL
    keyword TEXT,          -- Search keyword
    found_date TIMESTAMP,  -- When discovered
    archived BOOLEAN       -- Hidden from view
);
```

## Testing

```bash
pytest tests/
pytest tests/ -v --cov=src
```

### Add a Custom Notifier

```python
# src/notifiers/slack.py
class SlackNotifier:
    def send_items(self, items):
        for item in items:
            # Send to Slack webhook
            pass

# Update src/agent.py
from src.notifiers.slack import SlackNotifier
# Add to _init_notifiers()
```

### Add a Forum

```python
# src/sources/forum.py
FORUMS.append({
    "name": "newforumname",
    "base_url": "https://forum.example.com",
    "search_endpoint": "/search/",
})
```

## Testing

```bash
pytest tests/
pytest tests/ -v --cov=src
```

## Deployment

### Local Network Access

To access the dashboard from other devices on your network:

```bash
python main.py web --host 0.0.0.0 --port 5000
```

Then visit `http://<your-ip>:5000` from another device.

### Production Deployment

For production, consider:

1. **Web Server**: Use Gunicorn + Nginx
   ```bash
   gunicorn -w 4 -b 0.0.0.0:5000 'src.web:app'
   ```

2. **Process Manager**: Use systemd, supervisor, or Docker

3. **Database**: Upgrade to PostgreSQL for multi-user support

4. **SSL/TLS**: Enable HTTPS with Let's Encrypt

## Notes

- **Rate Limiting**: The agent respects site ToS by limiting request rates (0.5 req/sec default)
- **Web Access**: Share-friendly dashboard (local network or deploy to server)
- **Facebook**: Official Graph API or browser automation required; not included due to complexity
- **Deduplication**: Uses URL-based caching; run state persists across restarts via database
- **Logs**: All activity logged to console; can redirect to file

## Roadmap

- [ ] Redis backing for persistent cache
- [ ] Slack/Discord integrations
- [ ] Facebook Marketplace via Selenium
- [ ] Email digest notifications
- [ ] Price tracking and alerts
- [ ] User accounts & favorites
- [ ] Docker container
- [ ] Deployment to cloud (Heroku, AWS, etc.)

## License

MIT
