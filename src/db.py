"""Database models and persistence."""

import sqlite3
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

DB_PATH = Path(__file__).parent / "parts.db"


CATEGORIES = {
    "Exterior": ["bumper", "fender", "hood", "spoiler", "lip", "diffuser", "carbon fiber", "splitter", "grille", "trim", "cosmetic"],
    "Wheels": ["wheel", "rim", "tire", "tyre"],
    "Suspension": ["coilover", "suspension", "lowering", "spring", "damper", "shock", "control arm", "strut", "brake"],
    "Interior": ["seat", "interior", "dashboard", "steering wheel", "shifter", "pedal", "mat", "carpet", "trim"],
    "Engine": ["engine", "motor", "cylinder head", "valve", "piston", "clutch", "flywheel", "header", "manifold", "exhaust", "muffler", "catback", "downpipe", "intake", "supercharger", "turbo", "transmission", "differential", "driveshaft"],
    "Electronics": ["audio", "video", "phone", "alarm", "navigation", "radar"],
    "Detailing": ["wash", "wax", "detailing", "touchup"],
    "Other": [],
}


def categorize_item(title: str, keyword: str = "") -> str:
    """Auto-categorize item based on title/keyword."""
    combined = f"{title} {keyword}".lower()
    for category, keywords in CATEGORIES.items():
        if any(kw in combined for kw in keywords):
            return category
    return "Other"


def init_db():
    """Initialize SQLite database."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    # Check if table exists and has category column
    c.execute("PRAGMA table_info(items)")
    columns = {row[1] for row in c.fetchall()}
    
    if 'items' in [t[0] for t in c.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]:
        if 'category' not in columns:
            # Migrate: add category column
            c.execute("ALTER TABLE items ADD COLUMN category TEXT DEFAULT 'Other'")
            conn.commit()
    else:
        # Create new table
        c.execute("""
            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source TEXT NOT NULL,
                title TEXT NOT NULL,
                price TEXT,
                url TEXT UNIQUE NOT NULL,
                image TEXT,
                keyword TEXT,
                category TEXT DEFAULT 'Other',
                found_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                archived BOOLEAN DEFAULT 0
            )
        """)
        conn.commit()
    
    conn.close()


def add_item(item: Dict) -> bool:
    """Insert an item. Returns True if new, False if duplicate."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        category = item.get("category") or categorize_item(item.get("title", ""), item.get("keyword", ""))
        c.execute("""
            INSERT INTO items (source, title, price, url, image, keyword, category)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            item.get("source"),
            item.get("title"),
            item.get("price"),
            item.get("url"),
            item.get("image"),
            item.get("keyword"),
            category,
        ))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        conn.close()
        return False


def add_items(items: List[Dict]) -> int:
    """Insert multiple items. Returns count of new items."""
    count = 0
    for item in items:
        if add_item(item):
            count += 1
    return count


def get_items(limit: int = 100, offset: int = 0, archived: bool = False) -> List[Dict]:
    """Fetch items from database."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("""
        SELECT * FROM items
        WHERE archived = ?
        ORDER BY found_date DESC
        LIMIT ? OFFSET ?
    """, (archived, limit, offset))
    rows = c.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_recent_items(hours: int = 24, limit: int = 50) -> List[Dict]:
    """Get items found in the last N hours."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("""
        SELECT * FROM items
        WHERE archived = 0
        AND datetime(found_date) > datetime('now', ?)
        ORDER BY found_date DESC
        LIMIT ?
    """, (f'-{hours} hours', limit))
    rows = c.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def search_items(keyword: str, limit: int = 50) -> List[Dict]:
    """Search items by title or keyword."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    search_term = f"%{keyword}%"
    c.execute("""
        SELECT * FROM items
        WHERE archived = 0 AND (title LIKE ? OR keyword LIKE ?)
        ORDER BY found_date DESC
        LIMIT ?
    """, (search_term, search_term, limit))
    rows = c.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def archive_item(item_id: int):
    """Archive an item."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE items SET archived = 1 WHERE id = ?", (item_id,))
    conn.commit()
    conn.close()


def get_stats() -> Dict:
    """Get database statistics."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) as total, COUNT(DISTINCT source) as sources FROM items WHERE archived = 0")
    row = c.fetchone()
    conn.close()
    return {
        "total_items": row[0],
        "sources": row[1],
    }


def get_categories() -> List[str]:
    """Get all categories in use."""
    return list(CATEGORIES.keys()) + ["Other"]


def get_items_by_category(category: str, limit: int = 100, offset: int = 0, archived: bool = False) -> List[Dict]:
    """Fetch items by category."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("""
        SELECT * FROM items
        WHERE category = ? AND archived = ?
        ORDER BY found_date DESC
        LIMIT ? OFFSET ?
    """, (category, archived, limit, offset))
    rows = c.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_category_stats() -> Dict:
    """Get item count by category."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        SELECT category, COUNT(*) as count
        FROM items
        WHERE archived = 0
        GROUP BY category
        ORDER BY count DESC
    """)
    rows = c.fetchall()
    conn.close()
    return {row[0]: row[1] for row in rows}
