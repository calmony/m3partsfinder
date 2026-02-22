"""Flask web application for browsing found parts."""

from flask import Flask, render_template, request, jsonify
from urllib.parse import quote, unquote
from src.db import (
    init_db, get_items, get_recent_items, search_items, 
    archive_item, get_stats, get_items_by_category, get_categories, 
    get_category_stats
)
import logging
import os

logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True

# Header images (can be configured via environment or set here)
HEADER_IMAGE_URL = os.getenv('HEADER_IMAGE_URL', '/static/header-bg.jpg')  # Local M3 image
HEADER_LOGO_URL = os.getenv('HEADER_LOGO_URL', None)   # Set to a URL or path


def get_template_context(**kwargs):
    """Add header images to all template contexts."""
    context = {
        'header_image_url': HEADER_IMAGE_URL,
        'header_logo_url': HEADER_LOGO_URL,
    }
    context.update(kwargs)
    return context

app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True


@app.before_request
def before_first_request():
    """Initialize database."""
    try:
        init_db()
    except:
        pass


@app.route('/')
def index():
    """Home page with latest items."""
    page = request.args.get('page', 1, type=int)
    limit = 20
    offset = (page - 1) * limit
    
    items = get_items(limit=limit, offset=offset)
    stats = get_stats()
    categories = get_categories()
    cat_stats = get_category_stats()
    
    return render_template('index.html', **get_template_context(items=items, stats=stats, page=page, limit=limit, categories=categories, cat_stats=cat_stats))


@app.route('/recent')
def recent():
    """Show items found in last 24 hours."""
    hours = request.args.get('hours', 24, type=int)
    items = get_recent_items(hours=hours, limit=100)
    stats = get_stats()
    
    return render_template('recent.html', **get_template_context(items=items, stats=stats, hours=hours))


@app.route('/category/<path:category>')
def category(category):
    """Browse items by category."""
    # URL-decode the category name
    category = unquote(category)
    
    page = request.args.get('page', 1, type=int)
    limit = 20
    offset = (page - 1) * limit
    
    items = get_items_by_category(category, limit=limit, offset=offset)
    stats = get_stats()
    categories = get_categories()
    cat_stats = get_category_stats()
    
    return render_template('category.html', **get_template_context(items=items, stats=stats, page=page, limit=limit, 
                          category=category, categories=categories, cat_stats=cat_stats))


@app.route('/search')
def search():
    """Search items by keyword."""
    q = request.args.get('q', '', type=str)
    items = []
    
    if q:
        items = search_items(q, limit=50)
    
    return render_template('search.html', **get_template_context(items=items, query=q))


@app.route('/api/items')
def api_items():
    """JSON API for items."""
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 20, type=int)
    offset = (page - 1) * limit
    
    items = get_items(limit=limit, offset=offset)
    stats = get_stats()
    
    return jsonify({
        'items': items,
        'stats': stats,
        'page': page,
        'limit': limit,
    })


@app.route('/api/archive/<int:item_id>', methods=['POST'])
def api_archive(item_id):
    """Archive an item via API."""
    try:
        archive_item(item_id)
        return jsonify({'status': 'ok'})
    except Exception as e:
        logger.error(f"Archive error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 400


@app.route('/stats')
def stats():
    """Display statistics."""
    data = get_stats()
    return render_template('stats.html', **get_template_context(stats=data))


@app.errorhandler(404)
def not_found(error):
    return render_template('404.html', **get_template_context()), 404


@app.errorhandler(500)
def server_error(error):
    logger.error(f"Server error: {error}")
    return render_template('500.html', **get_template_context()), 500


if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)
