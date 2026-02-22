# CLAUDE.md — BMW E9X M3 Parts Finder

This file provides guidance for AI assistants working in this codebase.

---

## Project Overview

**m3partsfinder** is a Python-based parts-hunting tool for BMW E90/E92/E93 M3 vehicles. It periodically searches eBay and enthusiast forums for user-configured keywords, deduplicates results, sends SMS alerts via Twilio, and serves a local Flask web dashboard for browsing discovered listings.

---

## Repository Layout

```
m3partsfinder/
├── main.py                    # CLI entry point (Click commands)
├── requirements.txt           # All Python dependencies
├── seed_db.py                 # One-shot script to seed test data
├── src/
│   ├── agent.py               # Main search orchestrator / scheduler
│   ├── db.py                  # SQLite data-access layer
│   ├── cache.py               # In-memory URL deduplication
│   ├── web.py                 # Flask web application
│   ├── config.yaml            # Search keywords, intervals, settings
│   ├── parts.db               # SQLite database (runtime, gitignored)
│   ├── sources/               # Pluggable search adapters
│   │   ├── ebay.py            # eBay Browse API client
│   │   ├── forum.py           # BeautifulSoup forum scraper
│   │   ├── facebook.py        # Facebook Marketplace stub (placeholder)
│   │   └── __init__.py
│   ├── notifiers/             # Pluggable alert handlers
│   │   ├── sms.py             # Twilio SMS notifier
│   │   ├── stdout.py          # Console/log notifier
│   │   └── __init__.py
│   ├── templates/             # Jinja2 HTML templates
│   │   ├── base.html          # Base layout (dark theme, responsive)
│   │   ├── index.html         # All parts (paginated)
│   │   ├── recent.html        # Parts found in last N hours
│   │   ├── search.html        # Full-text search UI
│   │   ├── category.html      # Category browser
│   │   ├── stats.html         # Database statistics
│   │   ├── 404.html
│   │   └── 500.html
│   └── static/
│       ├── header-bg.jpg      # Default header background
│       └── header-bg.svg      # Vector fallback
└── tests/
    ├── test_agent.py          # pytest unit tests
    └── __init__.py
```

---

## Technology Stack

| Layer | Technology |
|---|---|
| Language | Python 3.x |
| CLI framework | Click |
| Web framework | Flask 2.3+ |
| Templating | Jinja2 (bundled with Flask) |
| Database | SQLite3 (stdlib) |
| HTML parsing | BeautifulSoup4 + lxml |
| HTTP | Requests |
| Scheduling | Schedule |
| SMS alerts | Twilio |
| Config | PyYAML + python-dotenv |
| Testing | pytest + pytest-cov |

---

## Development Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Copy and populate environment variables
cp .env.example .env   # edit with real API keys
```

### Environment Variables (`.env`)

```bash
# eBay Browse API (OAuth 2.0 Client Credentials)
EBAY_CLIENT_ID=
EBAY_CLIENT_SECRET=
EBAY_ENVIRONMENT=PRODUCTION   # or SANDBOX

# Twilio SMS
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
TWILIO_FROM_PHONE=+1234567890
ALERT_PHONE=+0987654321

# Web dashboard customization (optional)
HEADER_IMAGE_URL=/static/header-bg.jpg
HEADER_LOGO_URL=/static/logo.png
```

---

## Running the Application

```bash
# One-off search cycle (useful for testing)
python main.py search

# Continuous daemon (searches every 30 min by default)
python main.py daemon

# Web dashboard on http://localhost:5000
python main.py web --host 127.0.0.1 --port 5000

# Print multi-process instructions (daemon + web)
python main.py all
```

**Typical development workflow:** run `daemon` in one terminal, `web` in another, and open `http://localhost:5000`.

**Production:** use Gunicorn in front of Flask:
```bash
gunicorn -w 4 -b 0.0.0.0:5000 'src.web:app'
```

---

## Configuration (`src/config.yaml`)

```yaml
regions:
  - US

parts:                     # Keywords passed to each search source
  - xpipe
  - eisenmann
  - E92
  # ... add/remove keywords here

search_interval: 1800      # Seconds between search cycles (default: 30 min)
retention_hours: 168       # Hours to keep items before pruning (default: 1 week)
rate_limit: 0.5            # Max requests per second to external sites
user_agent: "Mozilla/5.0 ..."
```

---

## Database Schema

Single SQLite table — auto-created on first run by `src/db.py:init_db()`.

```sql
CREATE TABLE items (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    source      TEXT NOT NULL,          -- 'ebay' | 'forum:<name>'
    title       TEXT NOT NULL,
    price       TEXT,                   -- Raw string, e.g. "1500.00 USD"
    url         TEXT UNIQUE NOT NULL,   -- Primary dedup key
    image       TEXT,                   -- Image URL
    keyword     TEXT,                   -- Search keyword that matched
    category    TEXT DEFAULT 'Other',   -- Auto-categorized (see below)
    found_date  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    archived    BOOLEAN DEFAULT 0       -- Soft-delete / "seen" flag
);
```

**Auto-categories** (keyword matching on `title`): Exterior, Wheels, Suspension, Interior, Engine, Electronics, Detailing, Other.

---

## Web Routes

| Route | Method | Description |
|---|---|---|
| `/` | GET | All items, paginated (`?page=N`) |
| `/recent` | GET | Items from last 24 h (`?hours=N`) |
| `/search` | GET | Full-text search (`?q=term`) |
| `/category/<name>` | GET | Items for one category (`?page=N`) |
| `/stats` | GET | Database statistics |
| `/api/items` | GET | JSON — paginated items (`?page=N&limit=X`) |
| `/api/archive/<id>` | POST | JSON — soft-delete an item |

**No authentication** — intended for local network or trusted environments only.

---

## Key Modules

### `src/agent.py` — Orchestrator

- `run_search_cycle(config)` — iterates keywords × sources, deduplicates via `cache.py`, persists to DB, triggers notifiers.
- `start_daemon(config)` — wraps `run_search_cycle` with the `schedule` library.

### `src/db.py` — Data Access

All database interaction goes through this module. Never write raw SQL elsewhere.

Key functions:
- `init_db()` — create/migrate schema
- `add_item(item)` / `add_items(items)` — insert with dedup (URL UNIQUE constraint)
- `get_items(limit, offset)`, `get_recent_items(hours, limit)`, `search_items(query, limit)`
- `get_items_by_category(category, limit, offset)`
- `archive_item(id)` — sets `archived = 1`
- `get_stats()`, `get_category_stats()`

### `src/cache.py` — In-Memory Dedup

Wraps a Python `set` of seen URLs. Resets on process restart — intentional, since the DB URL `UNIQUE` constraint is the persistent guard.

### `src/sources/ebay.py` — eBay Adapter

Uses the official eBay Browse API (`/buy/browse/v1/item_summary/search`) with OAuth 2.0 client-credentials token caching. Returns `List[dict]` with keys: `source`, `title`, `price`, `url`, `image`, `keyword`.

### `src/sources/forum.py` — Forum Scraper

BeautifulSoup scraper targeting BMW enthusiast forums (e.g., e90post.com FS/FT threads). Fragile to HTML changes — check selectors after forum software updates.

### `src/notifiers/sms.py` — Twilio SMS

Sends one SMS per new item (or batched). Requires `TWILIO_*` env vars. Gracefully no-ops if vars are absent.

### `src/web.py` — Flask App

Thin controller layer — reads from `db.py`, renders Jinja2 templates. All template context is passed as keyword arguments to `render_template()`.

---

## Adding a New Search Source

1. Create `src/sources/mysite.py` with a function matching the signature:
   ```python
   def search_mysite(keyword: str, config: dict) -> list[dict]:
       """Returns list of items: {source, title, price, url, image, keyword}"""
   ```
2. Import and call it inside `src/agent.py:run_search_cycle()`.
3. Add any required env vars / config keys.
4. Write tests in `tests/test_agent.py`.

## Adding a New Notifier

1. Create `src/notifiers/mynotifier.py` implementing `send_item(item)` and `send_items(items)`.
2. Instantiate it in `src/agent.py` alongside the existing notifiers.

---

## Testing

```bash
# Run all tests
pytest tests/

# With coverage report
pytest tests/ -v --cov=src

# Skip tests that require live network/API credentials (default behavior)
# Tests needing real credentials are marked @pytest.mark.skip
```

Test file: `tests/test_agent.py` covers:
- `TestCache` — URL deduplication logic
- `TestNotifiers` — stdout notifier
- `TestEbayScraper` — live eBay search (skipped by default)

When adding new features, add corresponding tests. Mock external HTTP calls with `unittest.mock.patch` or `responses`.

---

## Code Conventions

- **Style:** PEP 8, snake_case for functions/variables, PascalCase for classes.
- **Logging:** Use `logging.getLogger(__name__)` in every module. Never use `print()` for runtime output.
- **Error handling:** Catch specific exceptions where possible; always log errors before returning a safe default (`[]`, `None`, etc.).
- **Type hints:** Use them on new public functions.
- **Docstrings:** Required for public functions — include `Args:` and `Returns:` sections.
- **Database access:** Only through `src/db.py`. Do not import `sqlite3` anywhere else.
- **Config access:** Pass the parsed `config` dict as a parameter; do not read `config.yaml` in multiple places.
- **No secrets in code:** All credentials via environment variables loaded by `python-dotenv`.

---

## Known Limitations

- **No authentication** on the web dashboard — do not expose to the public internet.
- **In-memory cache** resets on restart; the SQLite URL UNIQUE constraint is the true dedup guard.
- **Forum scraper** (`src/sources/forum.py`) is fragile to markup changes.
- **Facebook source** (`src/sources/facebook.py`) is a non-functional placeholder.
- **No database indices** beyond the primary key — add indices on `keyword`, `category`, `found_date` if the table grows large.
- **Single-threaded scheduler** — a long-running source can delay the next cycle.
- **No CI/CD** configured — tests must be run manually.

---

## Roadmap / Areas for Contribution

- Add indices to `items` table for `keyword`, `category`, `found_date`.
- Implement Facebook Marketplace scraper (`src/sources/facebook.py`).
- Persist deduplication cache to Redis (env-gated, fall back to in-memory).
- Add Discord/Slack notifier.
- Add GitHub Actions CI for automated test runs.
- Add Flask-Login for optional authentication.
- Expand test coverage with integration tests using a temp SQLite DB.
