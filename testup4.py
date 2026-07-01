import sys
import re
import requests
import concurrent.futures
import threading

try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

from bs4 import BeautifulSoup
from urllib.parse import quote_plus, quote

# Pure-Python Token Set Ratio replacement to avoid external binary dependencies
def calculate_token_set_ratio(s1, s2):
    w1 = set(re.findall(r'\w+', s1.lower()))
    w2 = set(re.findall(r'\w+', s2.lower()))
    if not w1 or not w2:
        return 0
    
    intersection = w1.intersection(w2)
    diff1to2 = w1.difference(w2)
    diff2to1 = w2.difference(w1)
    
    # Sorted tokens list
    t0 = sorted(list(intersection))
    t1 = sorted(list(intersection) + list(diff1to2))
    t2 = sorted(list(intersection) + list(diff2to1))
    
    # Joins
    str0 = " ".join(t0).strip()
    str1 = " ".join(t1).strip()
    str2 = " ".join(t2).strip()
    
    # Simple Levenshtein ratio function
    def lev_ratio(a, b):
        if a == b:
            return 100.0
        if not a or not b:
            return 0.0
        
        # Standard DP Levenshtein distance
        rows = len(a) + 1
        cols = len(b) + 1
        dp = [[0]*cols for _ in range(rows)]
        for i in range(rows):
            dp[i][0] = i
        for j in range(cols):
            dp[0][j] = j
            
        for i in range(1, rows):
            for j in range(1, cols):
                if a[i-1] == b[j-1]:
                    dp[i][j] = dp[i-1][j-1]
                else:
                    dp[i][j] = min(
                        dp[i-1][j] + 1,    # deletion
                        dp[i][j-1] + 1,    # insertion
                        dp[i-1][j-1] + 1   # substitution
                    )
        
        distance = dp[rows-1][cols-1]
        max_len = max(len(a), len(b))
        return (1.0 - (distance / max_len)) * 100.0

    # Calculate Token Set Ratio
    r0 = lev_ratio(str0, str1)
    r1 = lev_ratio(str0, str2)
    r2 = lev_ratio(str1, str2)
    return max(r0, r1, r2)

TARGET_MOVIE = "harry potter and the chamber of secrets (2002)"

SITES = [
    {
        "name": "VegaMovies",
        "purpose": ["download"],
        "language": ["hindi", "english"],
        "methods": [
            {
                "type": "json",
                "search": "https://vegamoviece.com/wp-json/wp/v2/posts?search={query}",
                "encoder": "percent"
            },
            {
                "type": "html",
                "search": "https://vegamoviece.com/?s={query}",
                "encoder": "plus"
            }
        ]
    },
    {
        "name": "Movies4U (Finance)",
        "purpose": ["download"],
        "language": ["hindi", "english"],
        "methods": [
            {
                "type": "json",
                "search": "https://new3.movies4u.finance/wp-json/wp/v2/posts?search={query}",
                "encoder": "percent"
            },
            {
                "type": "html",
                "search": "https://new3.movies4u.finance/?s={query}",
                "encoder": "plus"
            }
        ]
    },
    {
        "name": "Movies4U",
        "purpose": ["download"],
        "language": ["hindi", "english"],
        "methods": [
            {
                "type": "json",
                "search": "https://movies4u.pn/wp-json/wp/v2/posts?search={query}",
                "encoder": "percent"
            },
            {
                "type": "html",
                "search": "https://movies4u.pn/?s={query}",
                "encoder": "plus"
            }
        ]
    },
    {
        "name": "MovieHunt",
        "purpose": ["download", "watch"],
        "language": ["hindi", "english"],
        "methods": [
            {
                "type": "json",
                "search": "https://movieshunt.team/wp-json/wp/v2/posts?search={query}",
                "encoder": "percent"
            },
            {
                "type": "html",
                "search": "https://movieshunt.team/?s={query}",
                "encoder": "plus"
            }
        ]
    },
    {
        "name": "UhdMovies",
        "purpose": ["download"],
        "language": ["hindi", "english"],
        "methods": [
            {
                "type": "html",
                "search": "https://uhdmovies.food/search/{query}",
                "encoder": "plus"
            }
        ]
    },
    {
        "name": "MoviezMad",
        "purpose": ["download"],
        "language": ["hindi", "english"],
        "methods": [
            {
                "type": "html",
                "search": "https://www.moviezmad.live/search?type=categories&q={query}",
                "encoder": "plus"
            }
        ]
    },
    {
        "name": "HDHub4u",
        "purpose": ["download", "watch"],
        "language": ["hindi", "english"],
        "methods": [
            {
                "type": "html",
                "search": "https://new2.hdhub4u.cl/search.html?q={query}",
                "encoder": "percent"
            }
        ]
    },
    {
        "name": "YoMovies",
        "purpose": ["download", "watch"],
        "language": ["hindi", "english"],
        "methods": [
            {
                "type": "json",
                "search": "https://yomovies.foundation/wp-json/wp/v2/posts?search={query}",
                "encoder": "percent"
            },
            {
                "type": "html",
                "search": "https://yomovies.foundation/?s={query}",
                "encoder": "plus"
            }
        ]
    },
    {
        "name": "TheMoviesFlix",
        "purpose": ["download"],
        "language": ["hindi", "english"],
        "methods": [
            {
                "type": "json",
                "search": "https://themoviesflix.xyz/wp-json/wp/v2/posts?search={query}",
                "encoder": "percent"
            },
            {
                "type": "html",
                "search": "https://themoviesflix.xyz/?s={query}",
                "encoder": "plus"
            }
        ]
    },
    {
        "name": "ExtraMovies",
        "purpose": ["download"],
        "language": ["hindi", "english"],
        "methods": [
            {
                "type": "json",
                "search": "https://extramovies.miami/wp-json/wp/v2/posts?search={query}",
                "encoder": "percent"
            },
            {
                "type": "html",
                "search": "https://extramovies.miami/?s={query}",
                "encoder": "plus"
            }
        ]
    },
    {
        "name": "MoviesDrives",
        "purpose": ["download"],
        "language": ["hindi", "english"],
        "methods": [
            {
                "type": "json",
                "search": "https://new4.moviesdrives.my/wp-json/wp/v2/posts?search={query}",
                "encoder": "percent"
            },
            {
                "type": "html",
                "search": "https://new4.moviesdrives.my/search.html?q={query}",
                "encoder": "percent"
            }
        ]
    },
    {
        "name": "CineVood",
        "purpose": ["download"],
        "language": ["hindi", "english"],
        "methods": [
            {
                "type": "json",
                "search": "https://cinevood.blog/wp-json/wp/v2/posts?search={query}",
                "encoder": "percent"
            },
            {
                "type": "html",
                "search": "https://cinevood.blog/?s={query}",
                "encoder": "plus"
            }
        ]
    },
    {
        "name": "HindMovie",
        "purpose": ["download"],
        "language": ["hindi", "english"],
        "methods": [
            {
                "type": "json",
                "search": "https://hindmovie.icu/wp-json/wp/v2/posts?search={query}",
                "encoder": "percent"
            },
            {
                "type": "html",
                "search": "https://hindmovie.icu/?s={query}",
                "encoder": "plus"
            }
        ]
    },
    {
        "name": "HDMovie2",
        "purpose": ["download"],
        "language": ["hindi", "english"],
        "methods": [
            {
                "type": "html",
                "search": "https://hdmovie2a.org/?s={query}",
                "encoder": "plus"
            }
        ]
    },
    {
        "name": "MoviesMod",
        "purpose": ["download"],
        "language": ["hindi", "english"],
        "methods": [
            {
                "type": "html",
                "search": "https://moviesmod.army/search/{query}",
                "encoder": "plus"
            }
        ]
    },
    {
        "name": "JaniHD",
        "purpose": ["download"],
        "language": ["hindi", "english"],
        "methods": [
            {
                "type": "html",
                "search": "https://janihd.blogspot.com/search?q={query}",
                "encoder": "plus"
            }
        ]
    },
    {
        "name": "HindiMovies",
        "purpose": ["watch"],
        "language": ["hindi", "english"],
        "methods": [
            {
                "type": "html",
                "search": "https://ww1.hindimovies.to/full-search/{query}/",
                "encoder": "plus"
            }
        ]
    },
    {
        "name": "CineGo",
        "purpose": ["watch"],
        "language": ["english"],
        "methods": [
            {
                "type": "html",
                "search": "https://cinego.watch/search?keyword={query}",
                "encoder": "plus"
            }
        ]
    },
    {
        "name": "HiMovies",
        "purpose": ["watch"],
        "language": ["english"],
        "methods": [
            {
                "type": "html",
                "search": "https://himovies.bz/search/{query}",
                "encoder": "hyphen"
            }
        ]
    },
    {
        "name": "FMoviess",
        "purpose": ["watch"],
        "language": ["english"],
        "methods": [
            {
                "type": "html",
                "search": "https://fmoviess.org/search/?q={query}",
                "encoder": "plus"
            }
        ]
    },
    {
        "name": "4KHDHub",
        "purpose": ["watch"],
        "language": ["english"],
        "methods": [
            {
                "type": "html",
                "search": "https://4khdhub.one/?s={query}",
                "encoder": "plus"
            }
        ]
    },
    {
        "name": "TinyZone",
        "purpose": ["watch"],
        "language": ["english"],
        "methods": [
            {
                "type": "html",
                "search": "https://ww5.tinyzone.org/search/?q={query}",
                "encoder": "plus"
            }
        ]
    },
    {
        "name": "YoYoMovies",
        "purpose": ["watch"],
        "language": ["english"],
        "methods": [
            {
                "type": "html",
                "search": "https://yoyomovies.net/?s={query}",
                "encoder": "plus"
            }
        ]
    },
    {
        "name": "YesHD",
        "purpose": ["watch"],
        "language": ["english"],
        "methods": [
            {
                "type": "html",
                "search": "https://yeshd.net/?s={query}",
                "encoder": "plus"
            }
        ]
    },
    {
        "name": "Flixer",
        "purpose": ["watch"],
        "language": ["english"],
        "methods": [
            {
                "type": "html",
                "search": "https://flixer.su/search?q={query}",
                "encoder": "plus"
            }
        ]
    },
    {
        "name": "1HD",
        "purpose": ["watch"],
        "language": ["english"],
        "methods": [
            {
                "type": "html",
                "search": "https://1hd.art/search?keyword={query}",
                "encoder": "plus"
            }
        ]
    },
    {
        "name": "Cineb",
        "purpose": ["watch"],
        "language": ["english"],
        "methods": [
            {
                "type": "html",
                "search": "https://cineb.sh/search?keyword={query}",
                "encoder": "plus"
            }
        ]
    },
    {
        "name": "Tvids",
        "purpose": ["watch"],
        "language": ["english"],
        "methods": [
            {
                "type": "html",
                "search": "https://www.tvids.tv/search?q={query}",
                "encoder": "plus"
            }
        ]
    },
    {
        "name": "IonMedia",
        "purpose": ["watch"],
        "language": ["english"],
        "methods": [
            {
                "type": "html",
                "search": "https://www1.ionmedia.net/search?keyword={query}",
                "encoder": "plus"
            }
        ]
    },
    {
        "name": "Zoovie",
        "purpose": ["watch"],
        "language": ["english"],
        "methods": [
            {
                "type": "html",
                "search": "https://zoovie.cc/search?q={query}",
                "encoder": "plus"
            }
        ]
    },
    {
        "name": "123Movies",
        "purpose": ["watch"],
        "language": ["hindi", "english"],
        "methods": [
            {
                "type": "html",
                "search": "https://earn.123movies.ltd/search?q={query}",
                "encoder": "percent"
            }
        ]
    },
    {
        "name": "OnlyFlix",
        "purpose": ["watch"],
        "language": ["english"],
        "methods": [
            {
                "type": "html",
                "search": "https://onlyflix.to/?s={query}&mcs_search_type=all",
                "encoder": "plus"
            }
        ]
    },
    {
        "name": "WatchSeries8",
        "purpose": ["watch"],
        "language": ["english"],
        "methods": [
            {
                "type": "html",
                "search": "https://watchseries8.art/search?keyword={query}",
                "encoder": "plus"
            }
        ]
    },
    {
        "name": "GoWatchSeries",
        "purpose": ["watch"],
        "language": ["english"],
        "methods": [
            {
                "type": "html",
                "search": "https://gowatchseries.lol/search/{query}",
                "encoder": "percent"
            }
        ]
    },
    {
        "name": "DopeBox",
        "purpose": ["watch"],
        "language": ["english"],
        "methods": [
            {
                "type": "html",
                "search": "https://dopebox.stream/search?keyword={query}",
                "encoder": "plus"
            }
        ]
    },
    {
        "name": "Movish",
        "purpose": ["watch"],
        "language": ["english"],
        "methods": [
            {
                "type": "html",
                "search": "https://movish.net/search/{query}",
                "encoder": "percent"
            }
        ]
    },
    {
        "name": "EuroPixHD",
        "purpose": ["watch"],
        "language": ["english"],
        "methods": [
            {
                "type": "html",
                "search": "https://europixhd.org/search.php?search={query}",
                "encoder": "plus"
            }
        ]
    },
    {
        "name": "WatchTV",
        "purpose": ["watch"],
        "language": ["english"],
        "methods": [
            {
                "type": "html",
                "search": "https://www.watchtv.click/?s={query}",
                "encoder": "plus"
            }
        ]
    },
    {
        "name": "MovieBoxOnline",
        "purpose": ["watch"],
        "language": ["english"],
        "methods": [
            {
                "type": "html",
                "search": "https://movieboxonline.net/search-result?keyword={query}",
                "encoder": "plus"
            }
        ]
    },
    {
        "name": "SeriesOnline",
        "purpose": ["watch"],
        "language": ["english"],
        "methods": [
            {
                "type": "html",
                "search": "https://seriesonline.stream/search?keyword={query}",
                "encoder": "plus"
            }
        ]
    },
    {
        "name": "Cataz",
        "purpose": ["watch"],
        "language": ["english"],
        "methods": [
            {
                "type": "html",
                "search": "http://cataz.stream/search?keyword={query}",
                "encoder": "plus"
            }
        ]
    },
    {
        "name": "StreamM4u",
        "purpose": ["watch"],
        "language": ["english"],
        "methods": [
            {
                "type": "html",
                "search": "https://streamm4u.vip/search/{query}",
                "encoder": "hyphen"
            }
        ]
    },
    {
        "name": "WatchLuna",
        "purpose": ["watch"],
        "language": ["english"],
        "methods": [
            {
                "type": "html",
                "search": "https://watchluna.com/search?query={query}",
                "encoder": "plus"
            }
        ]
    },
    {
        "name": "Movies2Watch",
        "purpose": ["watch"],
        "language": ["english"],
        "methods": [
            {
                "type": "html",
                "search": "https://movies2watch.fun/?s={query}",
                "encoder": "plus"
            }
        ]
    },
    {
        "name": "AttackerTV",
        "purpose": ["watch"],
        "language": ["english"],
        "methods": [
            {
                "type": "html",
                "search": "https://attackertv.watch/search?keyword={query}",
                "encoder": "plus"
            }
        ]
    },
    {
        "name": "123mkv",
        "purpose": ["download"],
        "language": ["hindi", "english"],
        "methods": [
            {
                "type": "html",
                "search": "https://123mkv.garden/?s={query}",
                "encoder": "plus"
            }
        ]
    },
    {
        "name": "HDMovie2 (Alternate)",
        "purpose": ["download"],
        "language": ["hindi", "english"],
        "methods": [
            {
                "type": "html",
                "search": "https://newhdmovie2.top/?s={query}&post_type=movie",
                "encoder": "plus"
            }
        ]
    },
    {
        "name": "Mp4Moviez",
        "purpose": ["download"],
        "language": ["hindi", "english"],
        "methods": [
            {
                "type": "html",
                "search": "https://www.mp4moviez.fast/search/{query}.html",
                "encoder": "percent"
            }
        ]
    },
    {
        "name": "KatMovieHD",
        "purpose": ["download"],
        "language": ["hindi", "english"],
        "methods": [
            {
                "type": "html",
                "search": "https://new.katmoviehd.top/?s={query}",
                "encoder": "plus"
            }
        ]
    },
    {
        "name": "CineFreak",
        "purpose": ["download"],
        "language": ["hindi", "english"],
        "methods": [
            {
                "type": "html",
                "search": "https://cinefreak.net/fast-search/?q={query}",
                "encoder": "plus"
            }
        ]
    },
    {
        "name": "EntertainmentForU",
        "purpose": ["download"],
        "language": ["hindi", "english"],
        "methods": [
            {
                "type": "html",
                "search": "https://entertaimentforu.blogspot.com/search?q={query}",
                "encoder": "plus"
            }
        ]
    },
    {
        "name": "SkyMoviesHD",
        "purpose": ["download", "watch"],
        "language": ["hindi", "english"],
        "methods": [
            {
                "type": "html",
                "search": "https://skymovieshd.ceo/search.php?search={query}&cat=All",
                "encoder": "plus"
            }
        ]
    },
    {
        "name": "KMMovies",
        "purpose": ["download"],
        "language": ["hindi", "english"],
        "methods": [
            {
                "type": "html",
                "search": "https://kmmovies.shop/?s={query}",
                "encoder": "plus"
            }
        ]
    },
    {
        "name": "DesireMovies",
        "purpose": ["download"],
        "language": ["hindi", "english"],
        "methods": [
            {
                "type": "html",
                "search": "https://1desiremovies.dad/?s={query}",
                "encoder": "plus"
            }
        ]
    },
    {
        "name": "7HitMovies",
        "purpose": ["download"],
        "language": ["hindi", "english"],
        "methods": [
            {
                "type": "html",
                "search": "https://7hitmovies.repair/?s={query}",
                "encoder": "plus"
            }
        ]
    },
    {
        "name": "FreeDriveMovie",
        "purpose": ["download"],
        "language": ["hindi", "english"],
        "methods": [
            {
                "type": "html",
                "search": "https://freedrivemovie.cyou/?s={query}",
                "encoder": "plus"
            }
        ]
    },
    {
        "name": "SFlix",
        "purpose": ["watch"],
        "language": ["hindi", "english"],
        "methods": [
            {
                "type": "html",
                "search": "https://sflix.film/search-result?keyword={query}",
                "encoder": "plus"
            }
        ]
    },
    {
        "name": "HDMovie2 (Watch)",
        "purpose": ["watch"],
        "language": ["hindi", "english"],
        "methods": [
            {
                "type": "html",
                "search": "https://newhdmovie2.top/?s={query}",
                "encoder": "plus"
            }
        ]
    },
    {
        "name": "HDMovieIzle",
        "purpose": ["watch"],
        "language": ["hindi", "english"],
        "methods": [
            {
                "type": "html",
                "search": "https://hdmovieizle.com/index.php?do=search&subaction=search&story={query}",
                "encoder": "plus"
            }
        ]
    },
    {
        "name": "VegamN",
        "purpose": ["watch"],
        "language": ["hindi", "english"],
        "methods": [
            {
                "type": "html",
                "search": "https://vegamn.com/index.php?do=search&subaction=search&story={query}",
                "encoder": "plus"
            }
        ]
    },
    {
        "name": "HDMovieGo",
        "purpose": ["watch"],
        "language": ["hindi", "english"],
        "methods": [
            {
                "type": "html",
                "search": "https://hdmoviego.com/index.php?do=search&subaction=search&story={query}",
                "encoder": "plus"
            }
        ]
    },
    {
        "name": "Shasha",
        "purpose": ["watch"],
        "language": ["hindi", "english"],
        "methods": [
            {
                "type": "html",
                "search": "https://www.shasha.co/search/{query}",
                "encoder": "percent"
            }
        ]
    },
    {
        "name": "MovieFuze",
        "purpose": ["watch"],
        "language": ["hindi", "english"],
        "methods": [
            {
                "type": "html",
                "search": "https://www.moviefuze.com/search?q={query}",
                "encoder": "plus"
            }
        ]
    },
    {
        "name": "HindiLinks4U",
        "purpose": ["watch"],
        "language": ["hindi", "english"],
        "methods": [
            {
                "type": "html",
                "search": "https://www.hindilinks4u.asia/?s={query}",
                "encoder": "plus"
            }
        ]
    },
    {
        "name": "HindiCinemaHub",
        "purpose": ["watch"],
        "language": ["hindi", "english"],
        "methods": [
            {
                "type": "html",
                "search": "https://www.hindicinemahub.com/search?q={query}",
                "encoder": "percent"
            }
        ]
    },
    {
        "name": "RareAnimes",
        "purpose": ["download", "watch"],
        "language": ["hindi"],
        "methods": [
            {
                "type": "html",
                "search": "https://www.rareanimes.mov/?s={query}",
                "encoder": "plus"
            }
        ]
    },
    {
        "name": "RareToonIndia",
        "purpose": ["download", "watch"],
        "language": ["hindi"],
        "methods": [
            {
                "type": "html",
                "search": "https://raretoonindia.in/?s={query}",
                "encoder": "plus"
            }
        ]
    },
    {
        "name": "ToonHub4u",
        "purpose": ["download", "watch"],
        "language": ["hindi"],
        "methods": [
            {
                "type": "html",
                "search": "https://toonhub4u.co/?s={query}",
                "encoder": "plus"
            }
        ]
    },
    {
        "name": "ToonStream",
        "purpose": ["download", "watch"],
        "language": ["hindi"],
        "methods": [
            {
                "type": "html",
                "search": "https://toonstream.vip/?s={query}",
                "encoder": "plus"
            }
        ]
    }
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/137.0.0.0 Safari/537.36"
    )
}

# ----------------------------------------------------
# Thread-safe Print wrapper with Subscriber Support
# ----------------------------------------------------
print_lock = threading.Lock()
subscribers = []
subscribers_lock = threading.Lock()

def register_subscriber(callback):
    with subscribers_lock:
        subscribers.append(callback)

def unregister_subscriber(callback):
    with subscribers_lock:
        if callback in subscribers:
            subscribers.remove(callback)

def safe_print(*args, **kwargs):
    with print_lock:
        print(*args, **kwargs)
    
    # Format message as string
    msg = " ".join(map(str, args))
    with subscribers_lock:
        for cb in subscribers:
            try:
                cb(msg)
            except:
                pass

# ----------------------------------------------------
# Fetch page (Unified engine for HTML and JSON)
# ----------------------------------------------------
def fetch_url(url, is_json=False):
    try:
        safe_print(f"   ↳ trying requests for: {url}")
        r = requests.get(
            url,
            headers=HEADERS,
            timeout=1.5
        )
        r.raise_for_status()
        safe_print("   ↳ requests success")
        return r.json() if is_json else r.text
    except Exception as e:
        safe_print(f"   ↳ requests failed: {e}")
        # If requests failed with a connection error or timeout, do NOT try cloudscraper!
        # It's a network issue and cloudscraper will also time out. Raise it immediately.
        if isinstance(e, (requests.exceptions.ConnectionError, requests.exceptions.Timeout)):
            raise e

        # Fallback to standard requests if it is blocked
        safe_print("   ↳ trying requests backup")
        r_backup = requests.get(
            url,
            headers=HEADERS,
            timeout=1.5
        )
        r_backup.raise_for_status()
        return r_backup.json() if is_json else r_backup.text
    except Exception as e:
        safe_print(f"   ↳ requests backup failed: {e}")
        raise Exception(
            f"Both requests attempts failed: {e}"
        )

def encode_query(query, encoder="plus"):
    if encoder == "percent":
        return quote(query)
    elif encoder == "hyphen" or encoder == "dash":
        return quote(query.replace(" ", "-"))
    return quote_plus(query)

# ----------------------------------------------------
# JSON Results Auto-Extraction Parser helpers
# ----------------------------------------------------
def resolve_value(val):
    if isinstance(val, dict):
        for k in ["rendered", "title", "name", "text", "url", "link", "href"]:
            if k in val:
                return resolve_value(val[k])
        # Fallback to first string value found
        for v in val.values():
            if isinstance(v, str):
                return v
        # Fallback to string of first item
        if val:
            return str(next(iter(val.values())))
    return str(val) if val is not None else None

def extract_candidates_from_json(data, site_config):
    items = []
    if isinstance(data, list):
        items = data
    elif isinstance(data, dict):
        res_key = site_config.get("results_key")
        if res_key and res_key in data and isinstance(data[res_key], list):
            items = data[res_key]
        else:
            # Auto-detect: find the largest list in the dictionary values
            lists = [v for v in data.values() if isinstance(v, list)]
            if lists:
                lists.sort(key=len, reverse=True)
                items = lists[0]
            else:
                items = [data]
                
    candidates = []
    title_keys = site_config.get("title_keys", ["title", "name", "post_title", "title_name", "text", "heading"])
    url_keys = site_config.get("url_keys", ["url", "link", "permalink", "href", "post_url", "slug"])
    
    for item in items:
        if not isinstance(item, dict):
            continue
            
        title = None
        explicit_title_key = site_config.get("title_key")
        if explicit_title_key and explicit_title_key in item:
            title = resolve_value(item[explicit_title_key])
        else:
            for tk in title_keys:
                for k in item.keys():
                    if tk in k.lower():
                        title = resolve_value(item[k])
                        break
                if title:
                    break
                    
        url = None
        explicit_url_key = site_config.get("url_key")
        if explicit_url_key and explicit_url_key in item:
            url = resolve_value(item[explicit_url_key])
        else:
            for uk in url_keys:
                for k in item.keys():
                    if uk in k.lower():
                        url = resolve_value(item[k])
                        break
                if url:
                    break
                    
        # Fallbacks
        if not title:
            for k, v in item.items():
                if isinstance(v, str) and not v.startswith(("http://", "https://", "/")):
                    title = v
                    break
        if not url:
            for k, v in item.items():
                if isinstance(v, str) and (v.startswith(("http://", "https://", "/")) or "url" in k.lower() or "link" in k.lower()):
                    url = v
                    break
                    
        if title and url:
            title = title.strip()
            url = url.strip()
            if not url.startswith(("http://", "https://")):
                if url.startswith("//"):
                    from urllib.parse import urlparse
                    parsed_search = urlparse(site_config["search"])
                    url = f"{parsed_search.scheme}:{url}"
                else:
                    from urllib.parse import urljoin
                    url = urljoin(site_config["search"], url)
            candidates.append({"title": title, "url": url})
            
    return candidates

# ----------------------------------------------------
# Thread function to search a single site
# ----------------------------------------------------
def search_site(site, search_queries, target_movie):
    site_name = site["name"]
    methods = site.get("methods", [])
    
    last_error = None
    
    for i, method in enumerate(methods):
        method_type = method.get("type", "html").upper()
        
        safe_print("\n" + "=" * 70)
        safe_print(f"STARTING SEARCH: {site_name} (Method {i+1}/{len(methods)}: {method_type})")
        safe_print("=" * 70)

        best_score = 0
        best_match = None
        method_error = None

        try:
            for query in search_queries:
                safe_print(f"\n[{site_name} - {method_type}] Trying Query: {query}")
                
                encoded_query = encode_query(query, method.get("encoder", "plus"))
                search_url = method["search"].format(query=encoded_query)
                
                safe_print(f"[{site_name} - {method_type}] URL: {search_url}")

                try:
                    is_json = (method.get("type") == "json")
                    response_data = fetch_url(search_url, is_json=is_json)
                except Exception as e:
                    method_error = str(e)
                    safe_print(f"[{site_name} - {method_type}] ↳ query fetch error: {e}")
                    break

                candidates = []
                if method.get("type") == "json":
                    candidates = extract_candidates_from_json(response_data, method)
                else:
                    soup = BeautifulSoup(response_data, "html.parser")
                    for a in soup.find_all("a", href=True):
                        title = a.get_text(" ", strip=True)
                        if len(title) < 5:
                            continue
                        
                        raw_url = a["href"].strip()
                        if not raw_url.startswith(("http://", "https://")):
                            if raw_url.startswith("//"):
                                from urllib.parse import urlparse
                                parsed_search = urlparse(search_url)
                                resolved_url = f"{parsed_search.scheme}:{raw_url}"
                            else:
                                from urllib.parse import urljoin
                                resolved_url = urljoin(search_url, raw_url)
                        else:
                            resolved_url = raw_url

                        candidates.append({
                            "title": title,
                            "url": resolved_url
                        })

                # remove duplicates
                seen = set()
                unique = []
                for item in candidates:
                    key = (item["title"], item["url"])
                    if key not in seen:
                        seen.add(key)
                        unique.append(item)

                query_best_score = 0
                query_best_match = None

                for item in unique:
                    score = calculate_token_set_ratio(
                        target_movie.lower(),
                        item["title"].lower()
                    )
                    if score > query_best_score:
                        query_best_score = score
                        query_best_match = item

                safe_print(
                    f"[{site_name} - {method_type}] ↳ Best score this query: {round(query_best_score, 2)}"
                )

                if query_best_score > best_score:
                    best_score = query_best_score
                    best_match = query_best_match

                # good match found -> stop trying more queries
                threshold = 70 if site_name.lower() == "rareanimes" else 85
                if query_best_score >= threshold:
                    safe_print(f"[{site_name} - {method_type}] ↳ Good match found, stopping")
                    break

            # Evaluate search results for this method
            if method_error:
                safe_print(f"\n⚠️ [{site_name} - {method_type}] Error: {method_error}")
                last_error = method_error
                
                # Check if it is a connection/network issue to abort dead sites early
                err_lower = method_error.lower()
                is_network = any(ind in err_lower for ind in [
                    "connection", "timeout", "timed out", "dns", "resolv", 
                    "unreachable", "refused", "disconnected", "max retries", 
                    "host", "handshake", "ssl"
                ])
                if is_network:
                    safe_print(f"[{site_name}] Network unreachable or offline. Aborting site search immediately.")
                    safe_print(f"[SITE_COMPLETE] {site_name} | ERROR")
                    return {
                        "site": site_name,
                        "status": "ERROR",
                        "error": f"Site offline/unreachable: {method_error}"
                    }
                
                safe_print(f"[{site_name}] {method_type} method failed. Checking fallbacks...")
                continue
                
            threshold = 70 if site_name.lower() == "rareanimes" else 85
            if best_match and best_score >= threshold:
                safe_print(f"\n✅ [{site_name}] FOUND using {method_type}")
                safe_print(f"[{site_name}] Score : {round(best_score, 2)}")
                safe_print(f"[{site_name}] Title : {best_match['title']}")
                safe_print(f"[{site_name}] URL   : {best_match['url']}")
                safe_print(f"[SITE_COMPLETE] {site_name} | FOUND")
                return {
                    "site": site_name,
                    "status": "FOUND",
                    "score": round(best_score, 2),
                    "title": best_match["title"],
                    "url": best_match["url"]
                }
            else:
                safe_print(f"\n❌ [{site_name} - {method_type}] MOVIE NOT FOUND")
                safe_print(f"[{site_name}] Checking next search fallback method...")

        except Exception as e:
            safe_print(f"\n⚠️ [{site_name} - {method_type}] Error: {e}")
            last_error = str(e)
            safe_print(f"[{site_name}] Method error occurred. Checking fallbacks...")
            continue
            
    # If all methods completed and failed
    if last_error:
        safe_print(f"[SITE_COMPLETE] {site_name} | ERROR")
        return {
            "site": site_name,
            "status": "ERROR",
            "error": last_error
        }
    else:
        safe_print(f"[SITE_COMPLETE] {site_name} | NOT_FOUND")
        return {
            "site": site_name,
            "status": "NOT_FOUND"
        }

def deep_scrape_rareanimes(movie_url, purpose="watch"):
    import requests
    from bs4 import BeautifulSoup
    import re
    
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/137.0 Safari/537.36"
        )
    }
    
    extra_results = []
    try:
        r = requests.get(movie_url, headers=headers, timeout=15)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, "html.parser")
            post_content = soup.find(class_=re.compile("entry-content|herald-entry-content|post-content"))
            if not post_content:
                post_content = soup
                
            current_section = "General"
            for child in post_content.find_all(["p", "h1", "h2", "h3", "h4"]):
                text = child.get_text(strip=True)
                if not text:
                    continue
                
                text_low = text.lower()
                is_header = False
                for lang in ["hindi", "tamil", "telugu", "english", "multi"]:
                    if lang in text_low and len(text) < 50:
                        if not child.find("a"):
                            is_header = True
                            break
                            
                if is_header:
                    current_section = text
                
                # Check if Hindi section
                if "hindi" in current_section.lower() and "tamil" not in current_section.lower() and "telugu" not in current_section.lower():
                    links = child.find_all("a", href=True)
                    for a in links:
                        a_txt = a.get_text(strip=True)
                        href = a["href"]
                        
                        if a_txt == "WatchMultiQuality":
                            extra_results.append({
                                "site": "RareAnimes - Watch (MultiQuality)",
                                "status": "FOUND",
                                "title": f"Direct Watch Stream ({a_txt})",
                                "url": href,
                                "score": 100.0
                            })
                        elif a_txt == "StreamBeta":
                            extra_results.append({
                                "site": "RareAnimes - Stream (Beta)",
                                "status": "FOUND",
                                "title": f"Direct Watch Stream ({a_txt})",
                                "url": href,
                                "score": 100.0
                            })
                        elif a_txt == "DLBeta" and purpose == "download":
                            extra_results.append({
                                "site": "RareAnimes - Download (Fast)",
                                "status": "FOUND",
                                "title": f"Direct Fast Download ({a_txt})",
                                "url": href,
                                "score": 100.0
                            })
                        elif a_txt == "Mega" and purpose == "download":
                            extra_results.append({
                                "site": "RareAnimes - Download (Mega)",
                                "status": "FOUND",
                                "title": f"Direct Mega Download ({a_txt})",
                                "url": href,
                                "score": 100.0
                            })
    except Exception as e:
        safe_print(f"RareAnimes deep scraping exception: {e}")
        
    return extra_results

def scrape_rareanimes_anime(target_movie, excluded):
    import requests
    from bs4 import BeautifulSoup
    from urllib.parse import quote_plus, urljoin
    import re
    
    query_clean = re.sub(r"\s*\(\d{4}\)\s*", "", target_movie).strip()
    search_url = f"https://www.rareanimes.mov/?s={quote_plus(query_clean)}"
    
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/137.0 Safari/537.36"
        )
    }
    
    fallback_result = {
        "site": "RareAnimes",
        "status": "FOUND",
        "title": f"Search '{query_clean}' on RareAnimes",
        "url": search_url,
        "score": 100.0
    }
    
    if "rareanimes" in excluded:
        return []
        
    try:
        r = requests.get(search_url, headers=headers, timeout=12)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, "html.parser")
            
            links = []
            for a in soup.find_all("a", href=True):
                href = urljoin("https://www.rareanimes.mov", a["href"])
                if href.startswith("https://www.rareanimes.mov/") and not any(x in href for x in ["/category/", "/tag/", "/author/", "/page/", "/feed/", "/wp-", "#", "?reply", "?p="]):
                    txt = a.get_text(strip=True)
                    if txt and len(txt) > 3:
                        links.append((txt, href))
                        
            best_match = None
            best_score = 0
            for txt, href in links:
                score = calculate_token_set_ratio(query_clean, txt)
                if score > best_score:
                    best_score = score
                    best_match = (txt, href)
                    
            if best_match and best_score >= 80:
                post_title, post_url = best_match
                main_link = {
                    "site": "RareAnimes",
                    "status": "FOUND",
                    "title": post_title,
                    "url": post_url,
                    "score": round(best_score, 2)
                }
                extra = deep_scrape_rareanimes(post_url, "watch")
                return [main_link] + extra
    except Exception as e:
        safe_print(f"RareAnimes anime search scraper exception: {e}")
        
    return [fallback_result]

# ----------------------------------------------------
# Main Search Execution Function (Exportable)
# ----------------------------------------------------
def run_movie_search(target_movie, filter_purpose=None, filter_language=None, exclude_sites=None, original_title=None, is_anime=False):
    import os
    
    def get_site_name_from_url(url):
        from urllib.parse import urlparse
        try:
            parsed = urlparse(url)
            domain = parsed.netloc
            name_parts = domain.replace('www.', '').split('.')
            if len(name_parts) > 1 and len(name_parts[0]) <= 3:
                name = "".join([p.capitalize() for p in name_parts[:2]])
            else:
                name = name_parts[0].capitalize()
            return name
        except:
            return "AnimeSite"
            
    def build_search_url(line, query):
        from urllib.parse import quote, quote_plus
        import re
        if 'attack+on' in line.lower() or 'attck+on' in line.lower():
            q_val = quote_plus(query)
        else:
            q_val = quote(query)
        new_url = re.sub(r'attack[+\s%20]*on[+\s%20]*titan', q_val, line, flags=re.IGNORECASE)
        new_url = re.sub(r'attck[+\s%20]*on[+\s%20]*titan', q_val, new_url, flags=re.IGNORECASE)
        return new_url.strip()

    # Parse excluded sites
    excluded = set()
    if exclude_sites:
        if isinstance(exclude_sites, str):
            excluded = {name.strip().lower() for name in exclude_sites.split(",") if name.strip()}
        else:
            excluded = {name.strip().lower() for name in exclude_sites}

    # Anime watch list shortcut (Option A)
    is_watch = filter_purpose and filter_purpose.lower() == 'watch'
    is_eng = filter_language and filter_language.lower() == 'english'
    is_hindi = filter_language and filter_language.lower() == 'hindi'
    
    if is_anime and is_watch and (is_eng or is_hindi):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        file_to_load = os.path.join(base_dir, "watch english anime.txt") if is_eng else os.path.join(base_dir, "hindi watch anime.txt")
        
        results = []
        if os.path.exists(file_to_load):
            with open(file_to_load, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
            query_clean = re.sub(r"\s*\(\d{4}\)\s*", "", target_movie).strip()
            
            for line in lines:
                line_str = line.strip()
                if not line_str or line_str.startswith('#'):
                    continue
                
                site_name = get_site_name_from_url(line_str)
                if site_name.lower() in excluded:
                    continue
                    
                if site_name.lower() == "rareanimes":
                    anime_results = scrape_rareanimes_anime(target_movie, excluded)
                    results.extend(anime_results)
                    safe_print(f"[SITE_COMPLETE] {site_name} | FOUND")
                else:
                    search_url = build_search_url(line_str, query_clean)
                    results.append({
                        "site": site_name,
                        "status": "FOUND",
                        "title": f"Search '{query_clean}' on {site_name}",
                        "url": search_url,
                        "score": 100.0
                    })
                    safe_print(f"[SITE_COMPLETE] {site_name} | FOUND")
        else:
            safe_print(f"Anime file not found: {file_to_load}")
            
        return results

    # Build search query list
    search_queries = [target_movie]
    year_match = re.search(r"\((\d{4})\)", target_movie)
    if year_match:
        year = year_match.group(1)
        title_only = re.sub(r"\s*\(\d{4}\)\s*", "", target_movie).strip()
        # 1. Clean "Title Year" first (most compatible, specific)
        # 2. "Title" (only if it is long enough, e.g. >= 5 chars, to avoid slow database scans on short common words like "FROM" or "Dark")
        # 3. Fallback "Title (Year)" (with parenthesis)
        search_queries = [f"{title_only} {year}"]
        if len(title_only) >= 5:
            search_queries.append(title_only)
        search_queries.append(target_movie)

    # Parse excluded sites
    excluded = set()
    if exclude_sites:
        if isinstance(exclude_sites, str):
            excluded = {name.strip().lower() for name in exclude_sites.split(",") if name.strip()}
        else:
            excluded = {name.strip().lower() for name in exclude_sites}

    # Filter sites based on purpose & language selection
    filtered_sites = []
    for site in SITES:
        # Check if site is disabled/removed
        if site["name"].lower() in excluded:
            continue
        # Check purpose matching
        site_purposes = site.get("purpose", [])
        if filter_purpose and filter_purpose.lower() not in [p.lower() for p in site_purposes]:
            continue
        # Check language matching
        site_languages = site.get("language", [])
        if filter_language and filter_language.lower() not in [l.lower() for l in site_languages]:
            continue
        filtered_sites.append(site)

    if not filtered_sites:
        safe_print("No sites matched the selected filters!")
        return []

    safe_print(f"Searching {len(filtered_sites)} matching sites concurrently...")
    
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, len(filtered_sites))) as executor:
        futures = {
            executor.submit(search_site, site, search_queries, target_movie): site 
            for site in filtered_sites
        }
        for future in concurrent.futures.as_completed(futures):
            site = futures[future]
            try:
                res = future.result()
                results.append(res)
            except Exception as e:
                results.append({
                    "site": site["name"],
                    "status": "ERROR",
                    "error": str(e)
                })
                
    # Deep scrape RareAnimes if found in search results
    rareanimes_found = next((res for res in results if res.get("site") == "RareAnimes" and res.get("status") == "FOUND"), None)
    if rareanimes_found:
        movie_url = rareanimes_found["url"]
        safe_print(f"\n[RareAnimes] Deep scraping links from: {movie_url}")
        extra_links = deep_scrape_rareanimes(movie_url, filter_purpose)
        if extra_links:
            safe_print(f"[RareAnimes] Extracted {len(extra_links)} direct download/stream links successfully.")
            results.extend(extra_links)
            
    # RareMoviesFinder Fallback Search
    found_any = any(res.get("status") == "FOUND" for res in results)
    if not found_any:
        safe_print("\nNo links found on regular indexing networks. Activating RareMoviesFinder fallback search...")
        try:
            # Extract year from target_movie (e.g. "Cuore di mamma (1969)" -> " (1969)")
            year_match = re.search(r"\((\d{4})\)", target_movie)
            year_suffix = f" ({year_match.group(1)})" if year_match else ""
            
            # Use original title if available, otherwise target_movie
            rare_query = f"{original_title.strip()}{year_suffix}" if (original_title and original_title.strip()) else target_movie
            safe_print(f"Fallback engines querying: '{rare_query}'")
            
            rare_results = []
            
            def run_vk():
                try:
                    import RareMoviesFinder
                    return RareMoviesFinder.find_rare_movie_links(rare_query)
                except Exception as e:
                    safe_print(f"VK Video fallback failed: {e}")
                    return []

            def run_mailru():
                try:
                    import RareMoviesFinder2
                    return RareMoviesFinder2.find_rare_movie_links2(rare_query)
                except Exception as e:
                    safe_print(f"Mail.ru fallback failed: {e}")
                    return []

            def run_okru():
                try:
                    import okrutest
                    return okrutest.find_rare_movie_links3(rare_query)
                except Exception as e:
                    safe_print(f"OK.ru fallback failed: {e}")
                    return []

            # Run VK Video, Mail.ru, and OK.ru crawls concurrently to keep response times fast!
            with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
                futures = [
                    executor.submit(run_vk),
                    executor.submit(run_mailru),
                    executor.submit(run_okru)
                ]
                for future in concurrent.futures.as_completed(futures):
                    rare_results.extend(future.result())
            
            if rare_results:
                safe_print(f"Fallback engines found {len(rare_results)} links!")
                results.extend(rare_results)
            else:
                safe_print("Fallback engines found no links.")
        except Exception as e:
            safe_print(f"Failed to run fallbacks: {e}")
                
    return results

if __name__ == "__main__":
    safe_print(f"Target Movie: {TARGET_MOVIE}")
    results = run_movie_search(TARGET_MOVIE)

    # ----------------------------------------------------
    # Final Summary
    # ----------------------------------------------------
    safe_print("\n")
    safe_print("=" * 70)
    safe_print("FINAL RESULTS")
    safe_print("=" * 70)

    for result in results:
        site_cfg = next((s for s in SITES if s["name"] == result["site"]), {})
        
        purposes = site_cfg.get("purpose", ["unknown"])
        if isinstance(purposes, str):
            purposes = [purposes]
        purpose_str = "/".join(purposes).upper()
        
        languages = site_cfg.get("language", ["unknown"])
        if isinstance(languages, str):
            languages = [languages]
        lang_str = "/".join(languages).upper()
        
        meta_str = f"({purpose_str} | {lang_str})"
        
        if result["status"] == "FOUND":
            safe_print(f"\n[FOUND] {result['site']} {meta_str}")
            safe_print(f"Title : {result['title']}")
            safe_print(f"Score : {result['score']}")
            safe_print(f"URL   : {result['url']}")
        elif result["status"] == "NOT_FOUND":
            safe_print(f"\n[NOT FOUND] {result['site']} {meta_str} - Movie not found")
        else:
            safe_print(f"\n[ERROR] {result['site']} {meta_str} - {result['error']}")