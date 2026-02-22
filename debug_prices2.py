import requests
from bs4 import BeautifulSoup
import re

headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'}

# Test the exhaust thread that we know has $800
url = 'https://www.m3post.com/forums/showthread.php?t=2229446'

resp = requests.get(url, headers=headers, timeout=10)
soup = BeautifulSoup(resp.text, 'lxml')

# Get all text and find prices
all_text = soup.get_text()
prices = re.findall(r'\$[\d,]+(?:\.\d{2})?', all_text)
print(f"All prices found: {prices[:10]}")

# Find the first price and look for context
if prices:
    first_price = prices[0]
    idx = all_text.find(first_price)
    context = all_text[max(0, idx-150):idx+150]
    print(f"\nContext around first price ({first_price}):")
    print(context)

# Look at table structure
print("\n=== Looking for table cells ===")
tds = soup.find_all('td', limit=20)
for i, td in enumerate(tds[:10]):
    text = td.get_text(strip=True)[:80]
    if text and len(text) > 10:
        print(f"{i}: {text}")
