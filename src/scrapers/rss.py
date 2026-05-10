import html as _html
import re
from html.parser import HTMLParser

import feedparser


class _Stripper(HTMLParser):
    def __init__(self):
        super().__init__()
        self._parts: list[str] = []

    def handle_data(self, d: str) -> None:
        self._parts.append(d)

    def get_text(self) -> str:
        return re.sub(r"\s+", " ", _html.unescape(" ".join(self._parts))).strip()


def _strip_html(text: str) -> str:
    s = _Stripper()
    try:
        s.feed(_html.unescape(text))
        return s.get_text()
    except Exception:
        return text


def fetch_rss(url: str, max_items: int = 5) -> list[dict]:
    feed = feedparser.parse(url)
    if feed.bozo and not feed.entries:
        raise RuntimeError(f"failed to fetch feed: {feed.bozo_exception}")
    items = []
    for entry in feed.entries[:max_items]:
        items.append({
            "title": entry.get("title", "No title"),
            "url": entry.get("link", ""),
            "summary": _strip_html(entry.get("summary", "") or entry.get("description", "")),
        })
    return items
