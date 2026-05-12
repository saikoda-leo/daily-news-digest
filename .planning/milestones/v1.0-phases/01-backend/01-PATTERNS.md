# Phase 1: Backend - Pattern Map

**Mapped:** 2026-05-10
**Files analyzed:** 6 (2 new, 4 modified)
**Analogs found:** 6 / 6

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `requirements.txt` | config | — | `requirements.txt` (self) | exact |
| `src/scrapers/rss.py` | scraper/utility | request-response | `src/scrapers/github.py` | role-match |
| `src/scrapers/article.py` | scraper/service | request-response + batch | `src/scrapers/github.py` | role-match |
| `src/summarizer.py` | service | request-response + batch | `src/summarizer.py` (self, existing functions) | exact |
| `main.py` | orchestrator | batch | `main.py` (self, existing `_summarize_one`) | exact |
| `tests/test_article.py` | test | — | `tests/test_rss.py` | role-match |

---

## Pattern Assignments

### `requirements.txt` (config)

**Analog:** `requirements.txt` (self)

**Existing content** (lines 1-5):
```
anthropic==0.100.0
feedparser==6.0.12
requests==2.32.5
beautifulsoup4==4.14.3
PyYAML==6.0.3
```

**Change:** Append one line. Preserve pinned `==` version style — every existing dependency is pinned to an exact version, not a range.
```
trafilatura==2.0.0
```

---

### `src/scrapers/rss.py` (scraper, request-response) — MODIFIED

**Analog:** `src/scrapers/github.py`

**Imports pattern** — github.py lines 1-4 show the stdlib-first style used in scrapers:
```python
import sys
import requests
from bs4 import BeautifulSoup
```
For rss.py the new imports are stdlib only — no new third-party imports needed:
```python
import html as _html
from html.parser import HTMLParser
```

**Core pattern to add — `_strip_html()` helper.**
The scraper already returns `entry.get("summary", "") or entry.get("description", "")` at line 13. Add the helper before `fetch_rss()` and apply it at item-construction time:

```python
import html as _html
from html.parser import HTMLParser


class _Stripper(HTMLParser):
    def __init__(self):
        super().__init__()
        self._parts: list[str] = []

    def handle_data(self, d: str) -> None:
        self._parts.append(d)

    def get_text(self) -> str:
        return _html.unescape(" ".join(self._parts)).strip()


def _strip_html(text: str) -> str:
    s = _Stripper()
    try:
        s.feed(text)
        return s.get_text()
    except Exception:
        return text  # return original if parse fails
```

**Item construction change** — rss.py lines 10-14 (current):
```python
items.append({
    "title": entry.get("title", "No title"),
    "url": entry.get("link", ""),
    "summary": entry.get("summary", "") or entry.get("description", ""),
})
```
After modification (only the `"summary"` value changes):
```python
items.append({
    "title": entry.get("title", "No title"),
    "url": entry.get("link", ""),
    "summary": _strip_html(entry.get("summary", "") or entry.get("description", "")),
})
```

**Error handling pattern** — mirror github.py's stderr warn + continue style (github.py lines 37-43). The existing `fetch_rss` raises on hard failure (bozo + no entries) and silently returns partial results otherwise — keep that contract unchanged.

---

### `src/scrapers/article.py` (scraper/service, request-response + batch) — NEW

**Analog:** `src/scrapers/github.py` (same role: scraper, same HTTP stack: `requests`)

**Imports pattern** — model after github.py lines 1-4, then add trafilatura and stdlib:
```python
import sys
import requests
import trafilatura
from concurrent.futures import ThreadPoolExecutor
```

**Headers pattern** — github.py line 5 defines a module-level `_HEADERS` constant; do the same with the browser User-Agent required for news sites:
```python
_HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

SKIP_URL_PATTERNS = (".pdf", "youtube.com/watch", "youtu.be/", "github.com/")
MIN_CONTENT_CHARS = 200
```

**Core fetch pattern — `_fetch_one(item)`:**
Mutates `item` in place; never raises. This mirrors the isolation contract in `_scrape()` in main.py (main.py lines 31-36) where any exception is caught and returns `None`.
```python
def _fetch_one(item: dict) -> None:
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
```

**Concurrent orchestration pattern — `fetch_article_texts(items)`:**
Mirrors the `ThreadPoolExecutor` usage in main.py lines 123-124. Cap at 10 workers; use `list()` to force eager evaluation so all futures complete before the function returns.
```python
def fetch_article_texts(items: list[dict]) -> None:
    """Mutates all items in place concurrently. Never raises."""
    with ThreadPoolExecutor(max_workers=10) as executor:
        list(executor.map(_fetch_one, items))
```

**Error handling pattern** — github.py lines 37-41 show the warn-to-stderr + degrade style. All exceptions in `_fetch_one` must be caught and result in `item["full_text"] = ""`. `fetch_article_texts` itself never raises.

---

### `src/summarizer.py` (service, request-response + batch) — MODIFIED

**Analog:** `src/summarizer.py` — existing `summarize_items()` and `get_top_highlights()` functions are the direct analogs.

**Imports pattern** (summarizer.py lines 1-4 — unchanged, all required imports already present):
```python
import json
import re
from typing import Optional
import anthropic
```

**Claude client pattern** (summarizer.py lines 6-7, 20-24 — reuse exactly):
```python
_client: Optional[anthropic.Anthropic] = None

def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic()
    return _client
```

**Batched JSON call pattern** — `summarize_items()` lines 84-118 is the closest analog: one Claude call, numbered items, JSON array response, try/except fallback. The new `summarize_items_structured()` follows the same structure with three differences: (1) uses `full_text[:6000]` instead of `summary[:400]`, (2) expects JSON objects not strings, (3) uses assistant prefill `[`.

**JSON strip pattern** (summarizer.py lines 74-75 — copy exactly, do not rewrite):
```python
raw = re.sub(r'^```\w*\s*', '', raw)
raw = re.sub(r'\s*```$', '', raw).strip()
```

**Assistant prefill pattern** — `get_top_highlights()` does not use prefill; `summarize_items_structured()` must prepend `"["` to the assistant turn and to the response:
```python
messages=[
    {"role": "user", "content": prompt},
    {"role": "assistant", "content": "["},  # JSON prefill
],
# ...
raw = "[" + response.content[0].text.strip()
```

**Error handling pattern** (summarizer.py lines 103-118 — `summarize_items` try/except):
```python
try:
    response = _get_client().messages.create(...)
    raw = response.content[0].text.strip()
    raw = re.sub(r'^```\w*\s*', '', raw)
    raw = re.sub(r'\s*```$', '', raw).strip()
    result = json.loads(raw)
    if isinstance(result, list) and len(result) == len(items):
        return [str(s) for s in result]
except Exception:
    pass
return [""] * len(items)
```
For `summarize_items_structured`, the fallback is `[_EMPTY.copy() for _ in items]` instead of `[""] * len(items)`. Length mismatch is salvaged (partial results kept) rather than discarded entirely.

**`_safe_structured()` normalizer** — new private helper, place after `_summarize_one`-equivalent imports. No analog exists; implement as specified in RESEARCH.md Pattern 4:
```python
def _safe_structured(obj: dict) -> dict:
    kp_raw = obj.get("key_points", [])
    if isinstance(kp_raw, str):
        kp_raw = [kp_raw]
    kp = [str(p) for p in kp_raw[:5]]
    kp = (kp + [""] * 5)[:5]
    return {
        "core_idea": str(obj.get("core_idea", "")),
        "key_points": kp,
    }
```

**`max_tokens` formula** — derived from existing `summarize_items()` which uses `max_tokens=1024`. For structured output use the dynamic formula to avoid truncation:
```python
max_tokens = min(4096, len(items) * 120 + 200)
```

---

### `main.py` (orchestrator, batch) — MODIFIED

**Analog:** `main.py` (self) — the existing `_summarize_one()` function at lines 46-58 and the `ThreadPoolExecutor` at lines 123-124.

**Import addition** — add to the existing import block (main.py lines 11-16). Follow the existing grouping: scrapers together, then summarizer:
```python
from src.scrapers.article import fetch_article_texts
from src.summarizer import summarize_section, get_top_highlights, summarize_items, summarize_items_structured
```

**Fetch wiring** — insert after keyword filter (main.py line 89), before `sections.append` (main.py line 92). Follow the existing `if all_rss_items:` guard pattern (main.py line 91):
```python
# After line 89:
if all_rss_items:
    fetch_article_texts(all_rss_items)  # sets item["full_text"] in place
```

**`_summarize_one()` branching** — replace the `per_item` block (main.py lines 53-58). Keep the outer `try/except` and `[warn]` pattern unchanged:
```python
# BEFORE (lines 53-58):
try:
    per_item = summarize_items(title, section["items"])
    for item, ai_sum in zip(section["items"], per_item):
        item["ai_summary"] = ai_sum
except Exception as e:
    print(f"[warn] item summary failed for {title}: {e}", file=sys.stderr)

# AFTER:
try:
    if section.get("type") == "rss":
        per_item = summarize_items_structured(title, section["items"])
        for item, structured in zip(section["items"], per_item):
            item["core_idea"] = structured["core_idea"]
            item["key_points"] = structured["key_points"]
    else:
        per_item = summarize_items(title, section["items"])
        for item, ai_sum in zip(section["items"], per_item):
            item["ai_summary"] = ai_sum
except Exception as e:
    print(f"[warn] item summary failed for {title}: {e}", file=sys.stderr)
```

---

### `tests/test_article.py` (test) — NEW

**Analog:** `tests/test_rss.py` and `tests/test_summarizer.py`

**Test file structure pattern** (test_rss.py lines 1-4):
```python
import pytest
from unittest.mock import patch, MagicMock
from src.scrapers.article import fetch_article_texts, _fetch_one
```

**Mock helper pattern** (test_summarizer.py lines 6-9 — `_mock_response`; test_rss.py lines 6-12 — `_make_entry`/`_make_feed`):
For article tests, mock `requests.get` and `trafilatura.extract` at the module level using `patch`:
```python
def _make_resp(text="<html>article</html>", status=200, content_type="text/html", encoding="utf-8"):
    r = MagicMock()
    r.text = text
    r.status_code = status
    r.encoding = encoding
    r.apparent_encoding = "utf-8"
    r.headers = {"Content-Type": content_type}
    r.raise_for_status = MagicMock()
    return r
```

**Patch scope pattern** (test_rss.py lines 23-24 — `with patch("feedparser.parse", ...)`):
```python
with patch("src.scrapers.article.requests.get", return_value=_make_resp(...)):
    with patch("src.scrapers.article.trafilatura.extract", return_value="article text " * 20):
        ...
```

**Assertion style** (test_rss.py lines 25-27 — direct dict key access, no magic):
```python
assert items[0]["full_text"] == "article text " * 20
assert items[0]["full_text"] == ""  # fallback cases
```

---

## Shared Patterns

### Stderr Warning Pattern
**Source:** `main.py` lines 34-35; `src/scrapers/github.py` lines 37-43
**Apply to:** `src/scrapers/article.py` `_fetch_one()`, `src/summarizer.py` `summarize_items_structured()`
```python
print(f"[warn] <context>: {e}", file=sys.stderr)
```
All warnings use `[warn]` prefix, `file=sys.stderr`, and include enough context (URL, section name) to identify the failure source.

### Isolation / Never-Raise Contract
**Source:** `main.py` `_scrape()` lines 31-36
**Apply to:** `src/scrapers/article.py` `_fetch_one()` and `fetch_article_texts()`
```python
def _scrape(label: str, fn, *args, **kwargs) -> "list[dict] | None":
    try:
        return fn(*args, **kwargs)
    except Exception as e:
        print(f"[warn] {label}: {e}", file=sys.stderr)
        return None
```
Every scraper function catches all exceptions and returns a safe default. `_fetch_one` must set `item["full_text"] = ""` and return, never re-raise.

### JSON Parse + Markdown Strip Pattern
**Source:** `src/summarizer.py` lines 73-76 (`get_top_highlights`), lines 110-113 (`summarize_items`)
**Apply to:** `src/summarizer.py` `summarize_items_structured()` — reuse both regexes exactly:
```python
raw = response.content[0].text.strip()
raw = re.sub(r'^```\w*\s*', '', raw)
raw = re.sub(r'\s*```$', '', raw).strip()
result = json.loads(raw)
```

### Module-Level `_HEADERS` Constant
**Source:** `src/scrapers/github.py` line 5; `src/scrapers/reddit.py` line 3
**Apply to:** `src/scrapers/article.py`
```python
_HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
```
Both github.py and reddit.py define a module-level `_HEADERS` dict. article.py should follow the same pattern.

### Claude API Call Structure
**Source:** `src/summarizer.py` lines 36-42 (`summarize_section`), lines 104-110 (`summarize_items`)
**Apply to:** `src/summarizer.py` `summarize_items_structured()`
```python
response = _get_client().messages.create(
    model="claude-haiku-4-5-20251001",
    max_tokens=...,
    system=[{"type": "text", "text": _SYSTEM_PROMPT, "cache_control": {"type": "ephemeral"}}],
    messages=[{"role": "user", "content": prompt}],
)
```
Always use `_get_client()` (never instantiate directly), always pass system prompt with `cache_control`, always use `claude-haiku-4-5-20251001`.

### pytest Mock Pattern
**Source:** `tests/test_summarizer.py` lines 33-37
**Apply to:** `tests/test_article.py`, new tests in `tests/test_summarizer.py`
```python
mock_client = MagicMock()
mock_client.messages.create.return_value = _mock_response('["Summary A.", "Summary B."]')
with patch.object(summarizer, "_get_client", return_value=mock_client):
    result = summarizer.summarize_items("Section", items)
```

---

## No Analog Found

No files are without an analog. All new/modified files have role-matching or exact analogs in the codebase.

---

## Metadata

**Analog search scope:** `src/scrapers/`, `src/summarizer.py`, `main.py`, `tests/`
**Files scanned:** 9 (rss.py, github.py, reddit.py, summarizer.py, main.py, requirements.txt, test_rss.py, test_summarizer.py, test_html_renderer.py)
**Pattern extraction date:** 2026-05-10
