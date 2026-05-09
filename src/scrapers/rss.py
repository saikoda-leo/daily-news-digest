import feedparser


def fetch_rss(url: str, max_items: int = 5) -> list[dict]:
    feed = feedparser.parse(url)
    items = []
    for entry in feed.entries[:max_items]:
        items.append({
            "title": entry.get("title", "No title"),
            "url": entry.get("link", ""),
            "summary": entry.get("summary", "") or entry.get("description", ""),
        })
    return items
