import requests
import re
from difflib import SequenceMatcher
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import socket
from urllib3.util import connection

# Force IPv4 to prevent slow IPv6 DNS resolution/handshake timeouts to Russian networks
def allowed_gai_family():
    return socket.AF_INET

connection.allowed_gai_family = allowed_gai_family

# =====================================================
# CHANGE THIS
# =====================================================
MOVIE_NAME = "cuore di mamma"
MIN_DURATION = 50 * 60  # 50 minutes
# =====================================================

URL = "https://my.mail.ru/video/search"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/137.0.0.0 Safari/537.36"
    )
}

def similarity(a, b):
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def parse_views(text):
    text = text.replace("\xa0", " ").replace("•", " ")

    m = re.search(r"([\d.,]+)\s*([KM]?)", text, re.I)

    if not m:
        return 0

    try:
        num = float(m.group(1).replace(",", "."))
    except ValueError:
        return 0

    unit = m.group(2).upper()

    if unit == "K":
        num *= 1000

    elif unit == "M":
        num *= 1000000

    return int(num)


def highest_quality(hd):
    return 720 if hd else 480


def score_result(title, duration, views, hd, query):

    score = 0

    title_low = title.lower()
    query_low = query.lower()

    # --------------------
    # Title similarity
    # --------------------

    score += similarity(query, title) * 120

    # --------------------
    # Year
    # --------------------

    years = re.findall(r"(?:19|20)\d{2}", query)

    for year in years:
        if year in title:
            score += 40

    # --------------------
    # Runtime
    # --------------------

    if 80 * 60 <= duration <= 180 * 60:
        score += 20

    elif duration >= 50 * 60:
        score += 10

    # --------------------
    # Quality
    # --------------------

    if hd:
        score += 20

    # --------------------
    # Views
    # --------------------

    if views > 1_000_000:
        score += 20
    elif views > 100_000:
        score += 15
    elif views > 10_000:
        score += 10
    elif views > 1_000:
        score += 5

    # --------------------
    # Penalize junk
    # --------------------

    bad = [
        "trailer",
        "clip",
        "scene",
        "review",
        "reaction",
        "teaser",
        "dog",
        "cane",
        "aprimi"
    ]

    for word in bad:
        if word in title_low and word not in query_low:
            score -= 80

    return round(score, 2)

def duration_to_seconds(text):
    """
    Converts
    1:25:44
    52:10
    """
    text = text.strip()

    if not text:
        return 0

    parts = [int(x) for x in text.split(":")]

    if len(parts) == 3:
        h, m, s = parts
        return h * 3600 + m * 60 + s

    if len(parts) == 2:
        m, s = parts
        return m * 60 + s

    return 0


def search(query):

    r = requests.get(
        URL,
        params={"q": query},
        headers=HEADERS,
        timeout=30,
    )

    r.raise_for_status()

    soup = BeautifulSoup(r.text, "html.parser")

    # ONLY search results
    cards = soup.select(
        ".sp-video__search-result .sp-video__video-list__item"
    )

    print(f"\nFound {len(cards)} search results.\n")

    printed = set()

    for card in cards:

        # -----------------------------------
        # title
        # -----------------------------------
        title_tag = card.select_one(".sp-video__video-list__name")

        title = (
            title_tag.get_text(" ", strip=True)
            if title_tag
            else "Unknown"
        )

        # -----------------------------------
        # url
        # -----------------------------------
        preview = card.select_one(".sp-video__video-list__preview")

        if not preview:
            continue

        href = preview.get("href")

        if not href:
            continue

        url = urljoin("https://my.mail.ru", href)

        if url in printed:
            continue

        printed.add(url)

        # -----------------------------------
        # duration
        # -----------------------------------
        duration_tag = card.select_one(
            ".sp-video__video-list__duration"
        )

        duration_text = (
            duration_tag.get_text(strip=True)
            if duration_tag
            else ""
        )

        duration = duration_to_seconds(duration_text)

        if duration < MIN_DURATION:
            continue

        # -----------------------------------
        # HD
        # -----------------------------------
        hd = bool(
            card.select_one(".sp-video__video-list__hd")
        )

        # -----------------------------------
        # uploader
        # -----------------------------------
        uploader_tag = card.select_one(
            ".sp-video__video-list__user"
        )

        uploader = (
            uploader_tag.get_text(strip=True)
            if uploader_tag
            else "Unknown"
        )

        # -----------------------------------
        # views
        # -----------------------------------
        info = card.select_one(
            ".sp-video__video-list__info"
        )

        views = (
            info.get_text(" ", strip=True)
            if info
            else ""
        )

        print("=" * 80)
        print(title)
        print("Duration :", duration_text)
        print("HD       :", "Yes" if hd else "No")
        print("Uploader :", uploader)
        print("Views    :", views)
        print(url)

    print("\nDone.")


def find_rare_movie_links2(query_name):
    try:
        r = requests.get(
            URL,
            params={"q": query_name},
            headers=HEADERS,
            timeout=10,
        )
        r.raise_for_status()
        
        soup = BeautifulSoup(r.text, "html.parser")
        cards = soup.select(".sp-video__search-result .sp-video__video-list__item")[:15]
        
        printed = set()
        results = []
        
        for card in cards:
            title_tag = card.select_one(".sp-video__video-list__name")
            title = title_tag.get_text(" ", strip=True) if title_tag else "Unknown"
            
            preview = card.select_one(".sp-video__video-list__preview")
            if not preview:
                continue
            href = preview.get("href")
            if not href:
                continue
            url = urljoin("https://my.mail.ru", href)
            
            if url in printed:
                continue
            printed.add(url)
            
            duration_tag = card.select_one(".sp-video__video-list__duration")
            duration_text = duration_tag.get_text(strip=True) if duration_tag else ""
            duration = duration_to_seconds(duration_text)
            
            if duration < MIN_DURATION:
                continue
                
            hd = bool(card.select_one(".sp-video__video-list__hd"))
            
            # Views
            info = card.select_one(".sp-video__video-list__info")
            views_text = info.get_text(" ", strip=True) if info else ""
            views = parse_views(views_text)
            
            score = score_result(title, duration, views, hd, query_name)
            if score < 40:
                continue
                
            quality = highest_quality(hd)
            results.append({
                'site': 'Mail.ru',
                'title': f"{title} ({quality}p, {duration_text})",
                'url': url,
                'status': 'FOUND',
                'score': score
            })
            
        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:3]
    except Exception as e:
        print(f"RareMoviesFinder2 error: {e}")
        return []


if __name__ == "__main__":
    search(MOVIE_NAME)