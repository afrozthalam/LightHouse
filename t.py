import requests
import json

url = "https://www.new1.hdhub4u.auction/api/search?query=harry%20potter&page=1"

r = requests.get(url)

print("Status:", r.status_code)

data = r.json()

print(json.dumps(data, indent=2)[:5000])