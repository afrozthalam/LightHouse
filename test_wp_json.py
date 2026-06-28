import requests
import json

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36"
}

endpoints = {
    "Posts Endpoint": "https://themoviesflix.xyz/wp-json/wp/v2/posts?search=harry+potter",
    "General Search Endpoint": "https://themoviesflix.xyz/wp-json/wp/v2/search?search=harry+potter"
}

for name, url in endpoints.items():
    print(f"\n==========================================")
    print(f"Testing: {name}")
    print(f"URL: {url}")
    print(f"==========================================")
    try:
        r = requests.get(url, headers=headers, timeout=10)
        print("Status Code:", r.status_code)
        if r.status_code == 200:
            data = r.json()
            print("Response Type:", type(data))
            if isinstance(data, list):
                print(f"Found {len(data)} items.")
                if len(data) > 0:
                    print("Sample Item Keys:", list(data[0].keys()))
                    # Try to extract sample title and url
                    sample = data[0]
                    # In posts endpoint, title is usually inside a dict: {'rendered': '...'}
                    # link is usually standard
                    title = sample.get("title", {}).get("rendered") if isinstance(sample.get("title"), dict) else sample.get("title")
                    if not title:
                        title = sample.get("title")
                    link = sample.get("link")
                    print(f"Sample Match -> Title: {title} | Link: {link}")
            elif isinstance(data, dict):
                print("Keys in response dictionary:", list(data.keys()))
        else:
            print("Failed. Response Snippet:", r.text[:200])
    except Exception as e:
        print("Error during request:", e)
