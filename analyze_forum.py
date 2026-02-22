import requests
from bs4 import BeautifulSoup

headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'}
url = 'https://www.m3post.com/forums/forumdisplay.php?f=182'

try:
    resp = requests.get(url, headers=headers, timeout=15)
    soup = BeautifulSoup(resp.text, 'lxml')
    
    thread_links = soup.find_all('a', href=lambda x: x and 'showthread.php' in x)
    titles = [link.get_text(strip=True) for link in thread_links if link.get_text(strip=True)]
    
    print("Sample forum thread titles (first 20):\n")
    for i, title in enumerate(titles[:20], 1):
        if title and len(title) > 2:
            print(f"{i}. {title}")
    
    print(f"\n\nTotal threads visible: {len(titles)}")
    print("\nKeyword analysis:")
    
    # Analyze common keywords
    keywords_to_check = ['E90', 'E92', 'E93', 'M3', 'FS', 'WTS', 'WTB', 'GMG', 'CSL', 'BBS', 'ZCP']
    for kw in keywords_to_check:
        count = sum(1 for t in titles if kw.lower() in t.lower())
        if count > 0:
            print(f"  {kw}: {count} threads")

except Exception as e:
    print(f"Error: {e}")
