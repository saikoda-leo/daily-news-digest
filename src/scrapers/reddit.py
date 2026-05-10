import requests

_HEADERS = {"User-Agent": "daily-info-digest/1.0 (personal newspaper bot)"}


def fetch_reddit_posts(subreddit: str, max_posts: int = 5) -> list[dict]:
    url = f"https://www.reddit.com/r/{subreddit}/top.json"
    resp = requests.get(url, headers=_HEADERS, params={"limit": max_posts, "t": "day"}, timeout=10)
    resp.raise_for_status()

    children = resp.json().get("data", {}).get("children", [])
    posts = []
    for child in children[:max_posts]:
        d = child.get("data", {})
        if not d.get("title"):
            continue
        posts.append({
            "title": d["title"],
            "url": d.get("url", f"https://reddit.com{d.get('permalink', '')}"),
            "summary": d.get("selftext", "")[:500],
            "score": d.get("score", 0),
        })

    return posts
