"""On-demand, read-only OG/Article-image triage for two verified published posts.

The daily Pinterest RSS audit samples only ten items. This optional diagnostic
covers posts 389 and 438 without changing that sample, a workflow, or WordPress.
No image fetch, social publishing, SEO mutation, or Google indexing assertion.
"""
from urllib.error import HTTPError, URLError

from scripts.social.check_og import (
    OG_PREFIX, canonical, fetch_public_head, inspect,
)

# Authenticated WordPress and rendered public <head> checked 2026-10-31.
# Never accept a URL or ID from CLI input or a remote feed in this diagnostic.
TARGETS = (
    (389, "https://www.survival40.com/40s-male-bad-breath-care/"),
    (438, "https://www.survival40.com/40s-male-all-in-one-skincare-guide/"),
)


def run(fetcher=fetch_public_head):
    rows = []
    for article_id, article_url in TARGETS:
        item = {
            "article_id": article_id,
            "article_url": canonical(article_url),
            "expected_social_image": OG_PREFIX + str(article_id) + ".png",
        }
        try:
            rows.append(inspect(item, fetcher(article_url)))
        except (OSError, UnicodeError, ValueError, HTTPError, URLError) as exc:
            # Do not expose response bodies, credentials or exception messages.
            rows.append({
                "article_id": article_id,
                "article_url": article_url,
                "status": "UNAVAILABLE_UNVERIFIED",
                "error_type": type(exc).__name__,
            })
    return {
        "read_only": True,
        "changed_site": False,
        "social_published": False,
        "google_discover_appearance_verified": False,
        "image_bytes_or_dimensions_verified": False,
        "scope": "two preverified published articles; not a sitewide audit",
        "items": rows,
    }


if __name__ == "__main__":
    for row in run()["items"]:
        hint = row.get("discover_metadata", {}).get(
            "article_schema_image_source_hint", "UNVERIFIED"
        )
        print(f'Article #{row["article_id"]}: {row["status"]}; schema={hint}')
    print("READ-ONLY: no WordPress, advertising, image or SNS changes")
