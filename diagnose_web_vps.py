import requests

ip = "86.48.17.194"

endpoints = [
    "/version",
    "/areadocliente/",
    "/areadocliente/index.html",
    "/static/index.html"
]

for ep in endpoints:
    url = f"http://{ip}{ep}"
    try:
        r = requests.get(url, timeout=5)
        print(f"{url} -> {r.status_code}")
        if r.status_code == 200:
            print(f"   Response starts with: {r.text[:50]}...")
    except Exception as e:
        print(f"{url} -> FAILED: {e}")
