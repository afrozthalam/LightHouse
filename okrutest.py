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
    try:
        url = f"https://ok.ru/video/search/{query_name.replace(' ', '+')}"
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/137.0.0.0 Safari/537.36"
            )
        }
        
        r = requests.get(url, headers=headers, timeout=15)
        r.raise_for_status()
        
        soup = BeautifulSoup(r.text, "html.parser")
        cards = soup.select(".video_search_result_video-card")
        
        printed = set()
        results = []
        
        for card in cards:
            title_tag = card.select_one("a.video_search_result_video-link")
            if not title_tag:
                continue
            
            href = title_tag.get("href")
            if not href:
                continue
            url = urljoin("https://ok.ru", href)
            
            if url in printed:
                continue
            printed.add(url)
            
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
                'url': url,
                'status': 'FOUND',
                'score': score
            })
            
        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:3]
    except Exception as e:
        print(f"okrutest error: {e}")
        return []

if __name__ == "__main__":
    import sys
    q = sys.argv[1] if len(sys.argv) > 1 else "cuore di mamma 1969"
    print(find_rare_movie_links3(q))