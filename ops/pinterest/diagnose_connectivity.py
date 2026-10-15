"""Read-only connectivity diagnosis for Survival40 public resources.

Do not retry blocked responses, change headers to impersonate browsers,
or bypass site access policy. Print only status code and content type.
"""
from urllib import request, error

targets = {
    "wordpress_rss": "https://www.survival40.com/feed/",
    "wordpress_home": "https://www.survival40.com/",
    "wordpress_rest": "https://www.survival40.com/wp-json/wp/v2/posts?per_page=1&_fields=id",
    "shiori_image": "https://www.survival40.com/wp-content/plugins/survival40-auto/assets/navigator/explain.webp",
}
for name,url in targets.items():
    req = request.Request(url, headers={"User-Agent":"Survival40-Pinterest-Auto/1.0"})
    try:
        with request.urlopen(req,timeout=12) as res:
            res.read(128)
            print(name,res.status,res.headers.get("Content-Type","unknown"))
    except error.HTTPError as exc:
        print(name, "HTTP",exc.code)
    except (error.URLError,TimeoutError) as exc:
        print(name,"UNREACHABLE",type(exc).__name__)
