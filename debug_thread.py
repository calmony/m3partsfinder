import requests
from bs4 import BeautifulSoup
import re

headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'}
thread_url = 'https://www.m3post.com/forums/showthread.php?t=2229446'  # E90 Full ACM Modded Exhaust

resp = requests.get(thread_url, headers=headers, timeout=10)
soup = BeautifulSoup(resp.text, 'lxml')

print("=== THREAD ANALYSIS ===\n")

# Find post content
post = soup.find('div', class_=lambda x: x and 'post' in x.lower() if x else False)
if post:
    text = post.get_text()[:500]
    print("Post content (first 500 chars):")
    print(text)
    print()

# Look for price patterns
all_text = soup.get_text()
prices = re.findall(r'\$[\d,]+(?:\.\d{2})?|\b\d+\s*usd\b|\b\d+\s*each\b', all_text, re.IGNORECASE)
if prices:
    print(f"Found prices: {prices[:5]}")
else:
    print("No prices found in common format")

# Look for images
imgs = soup.find_all('img', limit=10)
print(f"\nFound {len(imgs)} images:")
for img in imgs[:5]:
    src = img.get('src', '')
    alt = img.get('alt', '')
    if 'post' in src.lower() or 'attachment' in src.lower() or 'image' in src.lower():
        print(f"  ✓ {src[:80]}")
    elif src and len(src) > 20:
        print(f"  - {src[:80]}")
