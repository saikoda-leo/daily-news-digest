import sys
from concurrent.futures import ThreadPoolExecutor

import requests
import trafilatura

_HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

SKIP_URL_PATTERNS = (".pdf", "youtube.com/watch", "youtu.be/", "github.com/")
MIN_CONTENT_CHARS = 200


def _fetch_one(item: dict) -> None:
    """Mutates item in place: sets item['full_text'] (str, may be empty). Never raises."""
    url = item.get("url", "")
    if not url or any(p in url for p in SKIP_URL_PATTERNS):
        item["full_text"] = ""
        return
    try:
        resp = requests.get(url, timeout=(3.05, 8), headers=_HEADERS)
        resp.raise_for_status()
        if resp.encoding and resp.encoding.lower() in ("iso-8859-1", "latin-1"):
            resp.encoding = resp.apparent_encoding or "utf-8"
        if "text/html" not in resp.headers.get("Content-Type", ""):
            item["full_text"] = ""
            return
        text = trafilatura.extract(
            resp.text,
            include_comments=False,
            include_tables=False,
            favor_recall=True,
        )
        item["full_text"] = text if (text and len(text) >= MIN_CONTENT_CHARS) else ""
    except Exception as e:
        print(f"[warn] article fetch {url}: {e}", file=sys.stderr)
        item["full_text"] = ""


def fetch_article_texts(items: list[dict]) -> None:
    """Mutates all items in place concurrently via ThreadPoolExecutor(max_workers=10). Never raises."""
    with ThreadPoolExecutor(max_workers=10) as executor:
        list(executor.map(_fetch_one, items))
