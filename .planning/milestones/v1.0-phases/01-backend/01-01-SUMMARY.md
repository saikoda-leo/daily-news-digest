---
phase: 01-backend
plan: "01"
subsystem: scrapers
tags: [article-fetching, rss, trafilatura, tdd, concurrent]
dependency_graph:
  requires: []
  provides: [src.scrapers.article, rss._strip_html, trafilatura-dep]
  affects: [src.scrapers.rss, requirements.txt]
tech_stack:
  added: [trafilatura==2.0.0, lxml_html_clean (transitive)]
  patterns: [ThreadPoolExecutor, HTMLParser, TDD]
key_files:
  created:
    - src/scrapers/article.py
    - tests/test_article.py
  modified:
    - requirements.txt
    - src/scrapers/rss.py
    - tests/test_rss.py
decisions:
  - "Used double-unescape in _strip_html: unescape input before feeding to HTMLParser to handle entity-encoded HTML from mocked RSS entries"
  - "Added re.sub whitespace collapse in _Stripper.get_text() to handle spaces introduced by tag removal"
  - "lxml_html_clean installed as transitive dep for trafilatura 2.0.0 (not pinned in requirements.txt)"
metrics:
  duration: "3 minutes"
  completed: "2026-05-10"
  tasks_completed: 2
  tasks_total: 2
  tests_before: 26 (or 44 in full suite)
  tests_after: 58 (full suite)
---

# Phase 01 Plan 01: Article Fetcher and RSS HTML Stripping Summary

**One-liner:** Concurrent article text fetcher via trafilatura with URL skip patterns, plus HTML entity stripping for RSS summaries.

## What Was Built

This plan delivers the data layer for Phase 2's structured summarizer: every RSS item gains a `full_text` field populated by fetching the article URL and extracting clean body text via trafilatura.

### Task 1: trafilatura pin + HTML stripping in rss.py

- Added `trafilatura==2.0.0` to `requirements.txt`
- Added `_Stripper` (HTMLParser subclass) and `_strip_html()` to `src/scrapers/rss.py`
- `_strip_html()` pre-unescapes HTML entities, feeds to parser, collapses whitespace, then unescapes again via `_html.unescape`
- Modified `fetch_rss()` to wrap summary with `_strip_html()` at item construction
- Added 4 new tests to `tests/test_rss.py` (tags+entity decode, plain text, empty, description fallback)
- Installed `trafilatura==2.0.0` (and transitive dep `lxml_html_clean`) into `.venv`

### Task 2: src/scrapers/article.py + tests/test_article.py

- Created `src/scrapers/article.py` with `fetch_article_texts(items)` and `_fetch_one(item)`
- Skip patterns: `.pdf`, `youtube.com/watch`, `youtu.be/`, `github.com/` — no HTTP call for these
- Encoding fix: ISO-8859-1/latin-1 responses get `resp.encoding = resp.apparent_encoding`
- Content-Type guard: non-`text/html` responses return empty string without calling trafilatura
- `trafilatura.extract()` called with `favor_recall=True`, `include_comments=False`, `include_tables=False`
- Minimum 200 chars threshold (`MIN_CONTENT_CHARS`) — shorter extraction returns empty string
- `ThreadPoolExecutor(max_workers=10)` for concurrent fetching across all RSS items
- All exceptions caught internally — never raises to caller
- Created `tests/test_article.py` with 14 tests covering all behaviors

## Test Counts

| Phase | Test Count |
|-------|-----------|
| Before plan | 26 (just rss/github) or 44 (full suite including summarizer/html_renderer) |
| After plan | 58 total (44 pre-existing + 4 new rss + 14 new article = 58) |

All 58 tests pass.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Double-unescape needed in _strip_html**
- **Found during:** Task 1 GREEN phase
- **Issue:** The plan's `_Stripper.get_text()` only unescaped after joining parts. But when mock RSS entries have entity-encoded HTML (`&lt;p&gt;Hello &amp;amp; &lt;b&gt;world&lt;/b&gt;&lt;/p&gt;`), the HTMLParser sees `&lt;p&gt;` as text (not a tag), so tag stripping doesn't work.
- **Fix:** Pre-unescape the input text before calling `s.feed()` in `_strip_html()`. This converts `&lt;p&gt;` to `<p>` so the parser recognizes it as a tag and strips it.
- **Files modified:** `src/scrapers/rss.py`
- **Commit:** 32cdcb6

**2. [Rule 1 - Bug] Whitespace collapse needed in get_text()**
- **Found during:** Task 1 GREEN phase (after fix 1)
- **Issue:** After tag removal, joining `_parts` with `" "` leaves double spaces where tags were (e.g., `"Hello &  world"` instead of `"Hello & world"`).
- **Fix:** Added `re.sub(r"\s+", " ", ...)` in `get_text()` and moved `import re` to module level.
- **Files modified:** `src/scrapers/rss.py`
- **Commit:** 32cdcb6

**3. [Rule 3 - Blocking] lxml_html_clean missing dependency**
- **Found during:** Task 1 verification
- **Issue:** `trafilatura==2.0.0` requires `lxml_html_clean` but it was not installed in `.venv`. `import trafilatura` failed with `ImportError: lxml.html.clean module is now a separate project`.
- **Fix:** Ran `pip install lxml_html_clean` to install the missing transitive dependency. Not pinned in `requirements.txt` (it is a transitive dep that pip resolves automatically).
- **Commit:** 32cdcb6 (installed, not code-committed)

## Notes for Plan 03 (Orchestrator Wire-up)

The orchestrator (`main.py`) needs to:
1. Import `fetch_article_texts` from `src.scrapers.article`
2. Call `fetch_article_texts(rss_items)` after collecting all RSS items and before passing them to the summarizer
3. The `full_text` field will then be available on each item for Plan 02's structured summarizer

```python
from src.scrapers.article import fetch_article_texts
# After scraping RSS feeds:
fetch_article_texts(all_rss_items)  # mutates in place; never raises
```

## Self-Check: PASSED

### Files Created/Modified Verification

- FOUND: requirements.txt
- FOUND: src/scrapers/rss.py
- FOUND: src/scrapers/article.py
- FOUND: tests/test_rss.py
- FOUND: tests/test_article.py

### Commits Verified

- FOUND: 32cdcb6 (feat(01-01): pin trafilatura and add HTML stripping to rss.py)
- FOUND: b11eca1 (feat(01-01): create article fetcher with concurrent text extraction)
