import requests
import re
from difflib import SequenceMatcher
import socket
from urllib3.util import connection

# Force IPv4 to prevent slow IPv6 DNS resolution/handshake timeouts to Russian networks
def allowed_gai_family():
    return socket.AF_INET

connection.allowed_gai_family = allowed_gai_family

# =====================================================
# CHANGE THIS
# =====================================================
MOVIE_NAME = "cuore di mamma 1969"
MIN_DURATION = 50 * 60  # 50 minutes
# =====================================================

CLIENT_ID = "52649896"
CLIENT_SECRET = "WStp4ihWG4l3nmXZgIbC"
VERSION = "5.282"


def get_token():
    r = requests.post(
        "https://login.vk.com/?act=get_anonym_token",
        data={
            "client_secret": CLIENT_SECRET,
            "client_id": CLIENT_ID,
            "scopes": "audio_anonymous,video_anonymous,photos_anonymous,profile_anonymous",
            "isApiOauthAnonymEnabled": "false",
            "version": VERSION,
            "app_id": CLIENT_ID,
        },
        timeout=30,
    )

    r.raise_for_status()
    return r.json()["data"]["access_token"]


def find_video_objects(obj):
    """
    Recursively find objects containing both duration and direct_url.
    """
    results = []

    if isinstance(obj, dict):
        if (
            "duration" in obj
            and "direct_url" in obj
        ):
            results.append(obj)

        for v in obj.values():
            results.extend(find_video_objects(v))

    elif isinstance(obj, list):
        for item in obj:
            results.extend(find_video_objects(item))

    return results


def get_next_from(obj):
    if isinstance(obj, dict):
        if "next_from" in obj:
            return obj["next_from"]

        for v in obj.values():
            nxt = get_next_from(v)
            if nxt:
                return nxt

    elif isinstance(obj, list):
        for item in obj:
            nxt = get_next_from(item)
            if nxt:
                return nxt

    return None


def search(token, query):

    r = requests.post(
        "https://api.vkvideo.ru/method/catalog.getVideoSearch",
        params={
            "v": VERSION,
            "client_id": CLIENT_ID,
        },
        data={
            "screen_ref": "search_video_service",
            "need_blocks": "1",
            "q": query,
            "input_method": "preset_from_link",
            "access_token": token,
        },
        timeout=60,
    )

    r.raise_for_status()

    js = r.json()

    videos = find_video_objects(js)

    printed = set()

    results = []

    for video in videos:

        duration = video.get("duration", 0)

        if duration < MIN_DURATION:
            continue

        url = video.get("direct_url")

        if not url:
            continue

        if url in printed:
            continue

        printed.add(url)

        results.append({
            "score": score_video(video, query),
            "title": video.get("title", ""),
            "duration": duration,
            "quality": highest_quality(video),
            "views": video.get("views", 0),
            "url": url,
        })

    results.sort(key=lambda x: x["score"], reverse=True)

    for r in results:

        h = r["duration"] // 3600
        m = (r["duration"] % 3600) // 60
        s = r["duration"] % 60

        print(
            f"[{r['score']:6.1f}] "
            f"{h:02}:{m:02}:{s:02} "
            f"{r['quality']}p "
            f"{r['views']:>8} views\n"
            f"{r['title']}\n"
            f"{r['url']}\n"
        )

    print("\nFinished.")
    print("Total:", len(printed))

def similarity(a, b):
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def highest_quality(video):

    files = video.get("files", {})

    if "mp4_2160" in files:
        return 2160

    if "mp4_1440" in files:
        return 1440

    if "mp4_1080" in files:
        return 1080

    if "mp4_720" in files:
        return 720

    if "mp4_480" in files:
        return 480

    if "mp4_360" in files:
        return 360

    return 240


def score_video(video, query):

    score = 0

    title = video.get("title", "")
    description = video.get("description", "")
    duration = video.get("duration", 0)
    views = video.get("views", 0)

    # -------------------------------------------------
    # TITLE SIMILARITY
    # -------------------------------------------------

    score += similarity(query, title) * 100

    # -------------------------------------------------
    # YEAR
    # -------------------------------------------------

    years = re.findall(r"(19|20)\d\d", query)

    if years:

        year = years[0]

        if year in title:
            score += 40

        if year in description:
            score += 20

    # -------------------------------------------------
    # DURATION
    # -------------------------------------------------

    if 80 * 60 <= duration <= 180 * 60:
        score += 30

    elif duration >= 50 * 60:
        score += 15

    # -------------------------------------------------
    # QUALITY
    # -------------------------------------------------

    quality = highest_quality(video)

    if quality >= 1080:
        score += 20

    elif quality >= 720:
        score += 15

    elif quality >= 480:
        score += 8

    # -------------------------------------------------
    # VIEWS
    # -------------------------------------------------

    if views > 2_000_000:
        score += 15

    elif views > 500_000:
        score += 10

    elif views > 100_000:
        score += 5

    # -------------------------------------------------
    # VERIFIED
    # -------------------------------------------------

    if video.get("verified"):
        score += 10

    # -------------------------------------------------
    # BAD WORDS
    # -------------------------------------------------

    bad = [
        "trailer",
        "clip",
        "reaction",
        "review",
        "teaser",
        "shorts",
        "scene",
        "edit",
        "recap",
        "explained"
    ]

    txt = (title + " " + description).lower()

    if any(word in txt for word in bad):
        score -= 100

    return round(score, 2)


def find_rare_movie_links(query_name):
    try:
        token = get_token()
        r = requests.post(
            "https://api.vkvideo.ru/method/catalog.getVideoSearch",
            params={
                "v": VERSION,
                "client_id": CLIENT_ID,
            },
            data={
                "screen_ref": "search_video_service",
                "need_blocks": "1",
                "q": query_name,
                "input_method": "preset_from_link",
                "access_token": token,
            },
            timeout=15,
        )
        r.raise_for_status()
        js = r.json()
        videos = find_video_objects(js)
        
        printed = set()
        results = []
        for video in videos:
            duration = video.get("duration", 0)
            if duration < MIN_DURATION:
                continue
            url = video.get("direct_url")
            if not url:
                continue
            if url in printed:
                continue
            printed.add(url)
            
            score = score_video(video, query_name)
            if score < 40: # filter out bad matches
                continue
                
            quality = highest_quality(video)
            results.append({
                'site': 'VK Video',
                'title': f"{video.get('title', '')} ({quality}p, {duration // 60} min)",
                'url': url,
                'status': 'FOUND',
                'score': score
            })
            
        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:3]
    except Exception as e:
        print(f"RareMoviesFinder error: {e}")
        return []

if __name__ == "__main__":
    token = get_token()
    search(token, MOVIE_NAME)