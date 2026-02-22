import requests
from bs4 import BeautifulSoup

headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'}
url = 'https://www.m3post.com/forums/forumdisplay.php?f=182'

try:
    print("Fetching m3post forum...")
    resp = requests.get(url, headers=headers, timeout=15)
    soup = BeautifulSoup(resp.text, 'lxml')
    
    # Try to find thread links
    links = soup.find_all('a', href=lambda x: x and 'showthread' in x)
    print(f'✓ Found {len(links)} thread links via showthread search')
    
    if links:
        print("\nFirst 5 threads:")
        for link in links[:5]:
            title = link.get_text(strip=True)
            href = link.get('href')
            print(f"  - {title[:60]}")
            print(f"    URL: {href[:80]}")
    else:
        print("\nNo showthread links found, trying alternative selectors...")
        
        # Try to find all rows
        trs = soup.find_all('tr', limit=10)
        print(f'Found {len(trs)} table rows')
        
        # Try divs with class containing thread
        divs = soup.find_all('div', class_=lambda x: x and 'thread' in x.lower(), limit=5)
        print(f'Found {len(divs)} divs with thread in class')
    
    # Check if page loaded properly
    print(f"\nPage response status: {resp.status_code}")
    print(f"Page length: {len(resp.text)} bytes")
    
except Exception as e:
    print(f'❌ Error: {e}')
    import traceback
    traceback.print_exc()
