---
phase: 01-backend
reviewed: 2026-05-10T00:00:00Z
depth: standard
files_reviewed: 8
files_reviewed_list:
  - src/scrapers/article.py
  - src/scrapers/rss.py
  - src/summarizer.py
  - main.py
  - tests/test_article.py
  - tests/test_main.py
  - tests/test_rss.py
  - tests/test_summarizer.py
findings:
  critical: 0
  warning: 4
  info: 4
  total: 8
status: issues_found
---

# Phase 01: Code Review Report

**Reviewed:** 2026-05-10T00:00:00Z
**Depth:** standard
**Files Reviewed:** 8
**Status:** issues_found

## Summary

Eight files reviewed across the article scraper, RSS scraper, summarizer, main orchestrator, and their test suites. No critical (data-loss or security) issues were found. Four warnings were identified: a broken markdown-fence stripping path in the structured summarizer, a case-sensitive Content-Type comparison that silently skips valid HTML pages, a convention violation where `summarize_section` propagates exceptions rather than catching them internally, and a potential `TypeError` in the keyword filter when item fields are `None`. Four informational items cover dead code, a rare HTML fallback, a redundant double-unescape, and test coverage gaps.

## Warnings

### WR-01: Dead-code leading fence regex in `summarize_items_structured` — silent fallback on markdown-wrapped responses

**File:** `src/summarizer.py:185-189`
**Issue:** `summarize_items_structured` prepends `"["` to the raw response text before applying the leading-fence strip regex (`r'^```\w*\s*'`). Because the string now starts with `"["` instead of `` ` ``, the regex can never match. If Claude wraps its JSON output in a markdown code fence (e.g., `` ```json\n[...]\n``` ``), the resulting string is `"[```json\n..."`, the leading fence is not stripped, `json.loads` raises, and the function silently returns a list of empty structured dicts for the entire section — with no warning emitted. The trailing-fence strip (line 189) still works, but the leading one is dead code that provides false safety.

**Fix:**
```python
# After prepending "[", strip the fence from inside the bracket:
raw = "[" + response.content[0].text.strip()
# Remove a possible leading fence that Claude wrapped around the continuation:
raw = re.sub(r'^\[```\w*\s*', '[', raw)
raw = re.sub(r'\s*```$', '', raw).strip()
```
Alternatively, strip fences from `response.content[0].text` before prepending:
```python
text = response.content[0].text.strip()
text = re.sub(r'^```\w*\s*', '', text)
text = re.sub(r'\s*```$', '', text).strip()
raw = "[" + text
```

---

### WR-02: Case-sensitive Content-Type comparison silently skips valid HTML pages

**File:** `src/scrapers/article.py:24`
**Issue:** `"text/html" not in resp.headers.get("Content-Type", "")` is a case-sensitive substring check. Servers that return `"TEXT/HTML"` or `"Text/Html"` (non-standard but permitted by RFC 7231) cause `_fetch_one` to set `item["full_text"] = ""` and return early without fetching article content. The article is then summarized only from its RSS snippet. No warning is printed, so the failure is invisible.

**Fix:**
```python
if "text/html" not in resp.headers.get("Content-Type", "").lower():
    item["full_text"] = ""
    return
```

---

### WR-03: `summarize_section` does not catch exceptions — violates documented convention

**File:** `src/summarizer.py:28-43`
**Issue:** `CLAUDE.md` states: *"Summarizer functions catch `Exception` internally and return a safe fallback. They never propagate exceptions to the orchestrator."* `summarize_section` has no `try/except` block and will propagate network errors, `IndexError` (empty `response.content`), and API errors to its caller. The caller (`main._summarize_one`) does catch it, so the immediate impact is contained, but any future call site that does not wrap the call will be silently unprotected — contrary to the stated contract.

**Fix:**
```python
def summarize_section(section_title: str, items: list) -> str:
    if not items:
        return ""
    items_text = "\n".join(
        f"- {item['title']}: {item.get('summary', '')[:300]}"
        for item in items
    )
    try:
        response = _get_client().messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=256,
            system=[{"type": "text", "text": _SYSTEM_PROMPT, "cache_control": {"type": "ephemeral"}}],
            messages=[{"role": "user", "content": f"Section: {section_title}\n\nItems:\n{items_text}\n\nSummarize what is notable."}],
        )
        return response.content[0].text
    except Exception:
        return ""
```

---

### WR-04: `_keyword_match` raises `TypeError` when `title` or `summary` is `None`

**File:** `main.py:43`
**Issue:** `item.get("title", "")` returns `None` (not `""`) when the key exists in the dict with value `None`. `feedparser` can set `entry["title"] = None` for malformed feeds. When that happens, `None + " " + ...` raises `TypeError`, which propagates out of the list-comprehension filter at line 96, crashing the entire run (not just the affected item). This only triggers when `rss_filter.keywords` is configured.

**Fix:**
```python
def _keyword_match(item: dict, keywords: list) -> bool:
    if not keywords:
        return True
    text = ((item.get("title") or "") + " " + (item.get("summary") or "")).lower()
    return any(k.lower() in text for k in keywords)
```

---

## Info

### IN-01: `_EMPTY_STRUCTURED` constant is defined but never used

**File:** `src/summarizer.py:122`
**Issue:** `_EMPTY_STRUCTURED = {"core_idea": "", "key_points": ["", "", "", "", ""]}` is defined as a module-level constant but is never referenced. The code at lines 196, 206, and 209 (and in the `except` block) each construct the same dict inline. This also means a future schema change requires updating four separate locations instead of one.

**Fix:** Either delete `_EMPTY_STRUCTURED` and leave the inline dicts as-is, or replace all inline occurrences with `_EMPTY_STRUCTURED.copy()` (use `.copy()` to avoid sharing mutable state between returned items).

---

### IN-02: `_strip_html` fallback returns raw HTML on parse error

**File:** `src/scrapers/rss.py:25-26`
**Issue:** When `HTMLParser.feed()` raises an exception, `_strip_html` returns the original `text` argument — which may contain HTML markup. This can leak tags like `<b>`, `<p>` etc. into item summaries and ultimately into the digest output. `HTMLParser` is very tolerant and this path is rarely triggered in practice, but when it is, the caller cannot distinguish clean text from tag-laden fallback.

**Fix:**
```python
    except Exception:
        return re.sub(r"<[^>]+>", " ", text).strip()  # bare tag strip as fallback
```

---

### IN-03: Double `_html.unescape` call in `_strip_html` is redundant

**File:** `src/scrapers/rss.py:22-23, 17`
**Issue:** `_strip_html` calls `_html.unescape(text)` before feeding to `HTMLParser` (line 23), and then `get_text()` calls `_html.unescape` again on the assembled parts (line 17). `HTMLParser` already decodes HTML entities when calling `handle_data`, so the first `unescape` call in `_strip_html` is redundant. For normal input the output is identical, but the redundant decode is misleading to readers and wastes a pass over the string.

**Fix:** Remove the pre-unescape in `_strip_html`:
```python
def _strip_html(text: str) -> str:
    s = _Stripper()
    try:
        s.feed(text)          # HTMLParser decodes entities internally
        return s.get_text()   # get_text applies unescape as a safety net
    except Exception:
        return text
```

---

### IN-04: Test coverage gaps

**Files:** `tests/test_main.py`, `tests/test_summarizer.py`, `tests/test_rss.py`
**Issue:** Several important paths lack test coverage:
- No test for `_keyword_match` (including the `None`-value crash described in WR-04).
- No test for `load_config` (missing file, invalid YAML).
- No test verifying that `summarize_section` exception propagation is handled at the call site.
- No test for `summarize_items_structured` when Claude returns markdown-fenced output (the dead-code fence strip described in WR-01 would be caught by such a test).
- No test for the Content-Type case-sensitivity issue (WR-02).

**Fix:** Add targeted unit tests for each path above using `unittest.mock.patch`.

---

_Reviewed: 2026-05-10T00:00:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
