import requests
import re
import socket
from urllib3.util import connection
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from difflib import SequenceMatcher

# Force IPv4 to prevent slow IPv6 DNS resolution/handshake timeouts to Russian networks
def allowed_gai_family():
    return socket.AF_INET

connection.allowed_gai_family = allowed_gai_family

MIN_DURATION = 50 * 60  # 50 minutes

def duration_to_seconds(d_str):
    if not d_str:
        return 0
    parts = d_str.split(":")
    try:
        if len(parts) == 2:
            return int(parts[0]) * 60 + int(parts[1])
        elif len(parts) == 3:
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
    except:
        pass
    return 0

def score_result(title, duration, query):
    score = 0
    title_lower = title.lower()
    query_lower = query.lower()
    
    # 1. Title match score
    match_ratio = SequenceMatcher(None, query_lower, title_lower).ratio()
    score += int(match_ratio * 50)
    
    # Keyword bonus
    query_words = query_lower.split()
    matched_words = sum(1 for w in query_words if w in title_lower)
    if len(query_words) > 0:
        score += int((matched_words / len(query_words)) * 25)
        
    # 2. Duration score (prefer full movies over short clips)
    if duration > 3000:
        score += 25
    elif duration > 1200:
        score += 10
    else:
        score -= 20
        
    return min(max(score, 0), 100)

def find_rare_movie_links3(query_name):
    import time
    try:
        # Safe URL quote encoding for query string to support spaces (as '+'), non-ASCII, and special characters
        quoted_query = requests.utils.quote(query_name).replace('%20', '+')
        url = f"https://ok.ru/video/search/{quoted_query}"
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache"
        }
        
        r = None
        for attempt in range(3):
            try:
                print(f"[OK.ru Scraper] Fetching (Attempt {attempt+1}): {url}")
                r = requests.get(url, headers=headers, timeout=10)
                r.raise_for_status()
                # Sanity check: verify response contains video search markup or is not a redirect block
                if "video" in r.text or "ok.ru" in r.url:
                    break
            except Exception as e:
                print(f"[OK.ru Scraper] Attempt {attempt+1} connection error: {e}")
                if attempt == 2:
                    raise e
                time.sleep(1)
        
        if not r:
            return []
            
        print(f"[OK.ru Scraper] Response URL: {r.url} | Status: {r.status_code}")
        
        soup = BeautifulSoup(r.text, "html.parser")
        cards = soup.select(".video_search_result_video-card")
        
        printed = set()
        results = []
        
        # Primary Grid Parser
        for card in cards:
            title_tag = card.select_one("a.video_search_result_video-link")
            if not title_tag:
                continue
            
            href = title_tag.get("href")
            if not href:
                continue
            video_url = urljoin("https://ok.ru", href)
            
            if video_url in printed:
                continue
            printed.add(video_url)
            
            title = title_tag.get_text(" ", strip=True)
            
            duration_tag = card.select_one(".video-card_duration")
            duration_text = duration_tag.get_text(strip=True) if duration_tag else ""
            duration = duration_to_seconds(duration_text)
            
            if duration < MIN_DURATION:
                continue
                
            score = score_result(title, duration, query_name)
            if score < 40:
                continue
                
            # Quality estimation (default to 720p or 1080p if mentioned in title)
            quality = "720"
            if "1080" in title:
                quality = "1080"
            elif "2160" in title or "4k" in title:
                quality = "2160"
                
            results.append({
                'site': 'OK.ru',
                'title': f"{title} ({quality}p, {duration_text})",
                'url': video_url,
                'status': 'FOUND',
                'score': score
            })
            
        # Resilient Fallback: If no cards parsed via class selector, scan all matching direct links
        if not results:
            print("[OK.ru Scraper] Grid selector returned empty. Attempting resilient DOM scanner fallback...")
            for tag in soup.find_all("a", href=True):
                href = tag.get("href")
                if re.search(r'/video/\d+', href) and not "search" in href:
                    video_url = urljoin("https://ok.ru", href)
                    if video_url in printed:
                        continue
                    printed.add(video_url)
                    
                    # Walk parent levels to resolve card boundary
                    parent = tag.parent
                    container = None
                    for _ in range(4):
                        if parent and parent.name in ['div', 'li'] and any(c for c in parent.get('class', []) if 'card' in c or 'item' in c or 'result' in c):
                            container = parent
                            break
                        if parent:
                            parent = parent.parent
                            
                    if container:
                        title = tag.get_text(" ", strip=True)
                        if not title:
                            continue
                            
                        # Resolve duration
                        duration_tag = container.select_one("[class*='duration']")
                        duration_text = duration_tag.get_text(strip=True) if duration_tag else ""
                        if not duration_text:
                            # Search text subtree for digits matching duration
                            match = re.search(r'\b\d{1,2}:\d{2}(?::\d{2})?\b', container.get_text(" "))
                            if match:
                                duration_text = match.group(0)
                                
                        duration = duration_to_seconds(duration_text)
                        if duration < MIN_DURATION:
                            continue
                            
                        score = score_result(title, duration, query_name)
                        if score < 40:
                            continue
                            
                        quality = "720"
                        if "1080" in title:
                            quality = "1080"
                        elif "2160" in title or "4k" in title:
                            quality = "2160"
                            
                        results.append({
                            'site': 'OK.ru',
                            'title': f"{title} ({quality}p, {duration_text})",
                            'url': video_url,
                            'status': 'FOUND',
                            'score': score
                        })
            
        results.sort(key=lambda x: x['score'], reverse=True)
        print(f"[OK.ru Scraper] Found {len(results)} valid movies.")
        return results[:3]
    except Exception as e:
        print(f"okrutest error: {e}")
        return []

if __name__ == "__main__":
    import sys
    q = sys.argv[1] if len(sys.argv) > 1 else "cuore di mamma 1969"
    print(find_rare_movie_links3(q))