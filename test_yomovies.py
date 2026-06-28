import requests
import cloudscraper
from bs4 import BeautifulSoup
from rapidfuzz import fuzz

url = "https://yomovies1.lol/?s=harry+potter"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36"
}

print("Testing Yomovies Search...")
print(f"URL: {url}")

html = None
try:
    print("Trying standard requests...")
    r = requests.get(url, headers=headers, timeout=15)
    r.raise_for_status()
    html = r.text
    print("Requests success!")
except Exception as e:
    print("Requests failed:", e)

if not html:
    try:
        print("Trying cloudscraper...")
        scraper = cloudscraper.create_scraper()
        r = scraper.get(url, timeout=20)
        html = r.text
        print(f"Cloudscraper success (Status: {r.status_code})!")
    except Exception as e:
        print("Cloudscraper failed:", e)

if html:
    soup = BeautifulSoup(html, "html.parser")
    candidates = []
    for a in soup.find_all("a", href=True):
        title = a.get_text(" ", strip=True)
        if len(title) < 5:
            continue
        candidates.append({
            "title": title,
            "url": a["href"]
        })
        
    # De-duplicate
    seen = set()
    unique = []
    for item in candidates:
        key = (item["title"], item["url"])
        if key not in seen:
            seen.add(key)
            unique.append(item)
            
    print(f"\nFound {len(unique)} unique links. Top matches for 'harry potter':")
    
    matches = []
    for item in unique:
        score = fuzz.token_set_ratio("harry potter", item["title"].lower())
        if score >= 70:
            matches.append((score, item))
            
    matches.sort(key=lambda x: x[0], reverse=True)
    for score, item in matches[:10]:
        print(f"- [{round(score, 2)}] {item['title']}")
        print(f"  URL: {item['url']}")
else:
    print("Failed to fetch yomovies search page.")
