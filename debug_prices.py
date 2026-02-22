import requests
from bs4 import BeautifulSoup
import re

headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'}

# Test first thread
urls = [
    'https://www.m3post.com/forums/showthread.php?t=2226687',  # M3 e9x lci adaptive 
    'https://www.m3post.com/forums/showthread.php?t=2222892',  # FS awron gauge
    'https://www.m3post.com/forums/showthread.php?t=2229446',  # E90 Full ACM Exhaust
]

for url in urls:
    try:
        print(f"\n=== {url.split('t=')[1]} ===")
        resp = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(resp.text, 'lxml')
        
        # Try different post content selectors
        selectors = [
            'div[class*="post_message"]',
            'div[class*="message"]',
            'div[class*="post"]',
            'div.postcontent',
            'td[class*="alt"]',
        ]
        
        for selector in selectors:
            post = soup.select_one(selector)
            if post:
                text = post.get_text()[:300]
                print(f"Found with {selector}:")
                print(f"  Text: {text[:100]}...")
                
                # Look for prices
                prices = re.findall(r'\$[\d,]+(?:\.\d{2})?', post.get_text())
                if prices:
                    print(f"  Prices: {prices}")
                break
        
    except Exception as e:
        print(f"Error: {e}")
