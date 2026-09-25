import urllib.request
try:
    req = urllib.request.Request(
        "https://magenta-wolf-691543.hostingersite.com/",
        headers={'User-Agent': 'Mozilla/5.0'}
    )
    html = urllib.request.urlopen(req).read().decode('utf-8')
    print("Length:", len(html))
    print("Head:", html[:500])
except Exception as e:
    print("Error:", e)
