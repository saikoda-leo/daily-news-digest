# Phase 1: Backend - Research

**Researched:** 2026-05-10
**Domain:** Python article fetching (trafilatura + requests) + structured Claude JSON summarization
**Confidence:** HIGH

---

## Summary

Phase 1 adds two capabilities to an existing working Python pipeline: (1) concurrent full-text
article fetching for all RSS items using `requests` + `trafilatura`, and (2) replacing the
current `summarize_items()` (returns `ai_summary: str`) with `summarize_items_structured()`
(returns `core_idea: str` + `key_points: list[str]`). The HTML renderer phase (Phase 2) will
consume the new fields; this phase is backend-only.

The codebase already has `ThreadPoolExecutor` usage in `main.py`, a working `requests` stack,
and a robust JSON-parsing pattern in `summarizer.py` (including the markdown-strip regex).
All new code follows these established patterns. The only new dependency is `trafilatura==2.0.0`
(latest as of 2026-05-10; was 1.12.x when earlier planning research was written).

**Primary recommendation:** Build `src/scrapers/article.py` as a new isolated module, wire it
into `main.py` after dedup and before `_summarize_one`, then replace `summarize_items()` with
`summarize_items_structured()` for the RSS section type only. All other sections keep the
existing `ai_summary: str` path unchanged.

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| FETCH-01 | Fetch full HTML of each RSS article URL using `requests`, 10-second timeout | `requests` already in stack; timeout tuple `(3.05, 8)` pattern documented in PITFALLS.md |
| FETCH-02 | Extract clean article body text using `trafilatura` | `trafilatura.extract(html_str, include_comments=False, include_tables=False)` — confirmed API from official docs |
| FETCH-03 | Fall back to RSS feed summary text if fetch fails, times out, or text < 200 chars | Fallback chain: `full_text if len(full_text) >= 200 else item["summary"]` — pattern confirmed in existing ARCHITECTURE.md |
| FETCH-04 | Truncate extracted text to 6000 characters before sending to Claude | `text[:6000]` at summarizer boundary — no new library needed |
| FETCH-05 | All RSS article fetches run concurrently via `ThreadPoolExecutor` before summarization | `ThreadPoolExecutor(max_workers=10)` + `executor.map(fetch_one, items)` — pattern already used in `main.py` |
| SUMM-01 | Claude produces structured JSON per article: `{"core_idea": "...", "key_points": [...5...]}` | Batched JSON array prompt; existing markdown-strip regex re-used |
| SUMM-02 | Claude calls batched per section (one call per RSS section) | New `summarize_items_structured()` follows existing `summarize_items()` batch pattern |
| SUMM-03 | Malformed JSON or wrong `key_points` length falls back to empty structured summary | `try/except` around `json.loads`; `_safe_structured()` normalizer; length mismatch salvages partial results |
| SUMM-04 | Replace `ai_summary: str` on RSS items with `core_idea: str` + `key_points: list[str]` | Data model change isolated to RSS path; GitHub/Reddit keep `ai_summary: str` unchanged |
</phase_requirements>

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Article URL fetching | Backend (Python, `article.py`) | — | Network I/O; isolated from Claude logic |
| HTML-to-text extraction | Backend (Python, `article.py`) | — | CPU-bound parsing; trafilatura runs in same thread as fetch |
| Concurrent fetch orchestration | Orchestrator (`main.py`) | — | Sequencing decision: after dedup, before summarization |
| Structured Claude summarization | Backend (Python, `summarizer.py`) | — | Claude API calls; same tier as existing summarizer |
| RSS item data model | Backend (Python, in-memory dict) | — | `core_idea`/`key_points` fields set on item dicts before rendering |
| HTML rendering of new fields | Frontend (Phase 2) | — | `_render_rss_items()` change is out of scope for this phase |

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `trafilatura` | `2.0.0` | Article body extraction from pre-fetched HTML | Purpose-built for news article extraction; outperforms newspaper3k, readability-lxml, goose3 on recall; returns `None` on failure (clean fallback) |
| `requests` | `2.32.5` | HTTP fetch of article URLs | Already present; synchronous, works with `ThreadPoolExecutor` |
| `anthropic` | `0.100.0` | Claude API for structured summarization | Already present; existing pattern re-used |

[VERIFIED: pip index versions trafilatura] — Latest stable version is `2.0.0` (was `1.12.2` when prior research was written; upgrade to latest).

### Supporting (already installed, no new installs)

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `beautifulsoup4` | `4.14.3` | Fallback HTML stripping (for RSS `summary` HTML cleanup) | Used only for `strip_html()` on RSS `summary` field; NOT used for article body extraction (trafilatura handles that) |
| `html.parser` | stdlib | HTML entity unescaping in strip_html | No install needed |

### Not Added (and Why)

| Instead of | Could Use | Why Not |
|------------|-----------|---------|
| `trafilatura` | `newspaper3k` | Last release 2018; Python 3.10+ broken |
| `trafilatura` | `readability-lxml` | Lower recall; no active development |
| `trafilatura` | `goose3` | Adds Pillow dep; worse than trafilatura |
| `requests` | `httpx` | requests already present; no benefit for sync ThreadPoolExecutor use |
| char-based truncation | `tiktoken` | Overkill; 4 chars ≈ 1 token is sufficient estimate |

**Installation (one new package):**
```bash
pip install trafilatura==2.0.0
# Then update requirements.txt: add trafilatura==2.0.0
```

---

## Architecture Patterns

### System Architecture Diagram

```
feeds.yaml
    |
    v
fetch_rss() x N feeds ─────────────────────────────── [{title, url, summary, source}]
    |
    v (dedup + keyword filter — unchanged, in main.py)
all_rss_items: [{title, url, summary, source}]
    |
    v  [NEW — FETCH-05]
fetch_article_texts(all_rss_items)          ThreadPoolExecutor(max_workers=10)
  per item: requests.get(url, timeout=(3.05,8))
    ├─ success + len >= 200 chars → item["full_text"] = trafilatura.extract(resp.text, ...)
    └─ failure / short / non-article → item["full_text"] = ""
    |
    v
item["full_text"] set on all RSS items (empty string on failure)
    |
    v
sections assembled (unchanged structure)
    |
    ├── get_top_highlights() ────────────────── unchanged
    |
    └── _summarize_one() per section          ThreadPoolExecutor (existing)
          ├── summarize_section() ──────────── unchanged
          └── if section["type"] == "rss":
                summarize_items_structured()  [NEW — SUMM-01, SUMM-02]
                  input: full_text[:6000] OR summary fallback
                  1 Claude call per section, returns JSON array
                  per item: {"core_idea": str, "key_points": [5 x str]}
                  sets item["core_idea"], item["key_points"]
              else:
                summarize_items() ─────────── unchanged
                sets item["ai_summary"]
    |
    v
render_digest()       unchanged (markdown renderer ignores new fields)
render_html_digest()  reads item.get("ai_summary","") — unchanged in Phase 1
                      (Phase 2 will update to read core_idea + key_points)
```

### Recommended Project Structure (changes only)

```
src/
├── scrapers/
│   ├── rss.py           # MODIFIED: strip_html() applied to summary at item-build time
│   ├── article.py       # NEW: fetch_article_texts(items) + fetch_one(item)
│   ├── github.py        # unchanged
│   └── reddit.py        # unchanged
├── summarizer.py        # MODIFIED: add summarize_items_structured(); _summarize_one() branching
├── html_renderer.py     # unchanged in Phase 1
└── renderer.py          # unchanged
main.py                  # MODIFIED: call fetch_article_texts() after dedup, update import
requirements.txt         # MODIFIED: add trafilatura==2.0.0
tests/
├── test_article.py      # NEW: covers fetch_article_texts, fallback chain, skip patterns
└── test_summarizer.py   # MODIFIED: add tests for summarize_items_structured()
```

### Pattern 1: Article Fetch — Single Item

```python
# Source: ARCHITECTURE.md + PITFALLS.md (project research) + official trafilatura docs
import requests
import trafilatura

SKIP_URL_PATTERNS = (".pdf", "youtube.com/watch", "youtu.be/", "github.com/")
MIN_CONTENT_CHARS = 200

def _fetch_one(item: dict) -> None:
    """Mutates item in place: sets item["full_text"] (str, may be empty)."""
    url = item.get("url", "")
    fallback = item.get("summary", "")

    # URL pre-check: skip non-article URL types
    if not url or any(p in url for p in SKIP_URL_PATTERNS):
        item["full_text"] = ""
        return

    try:
        resp = requests.get(
            url,
            timeout=(3.05, 8),
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"},
        )
        resp.raise_for_status()

        # Fix encoding misdetection on Vietnamese news sites (PITFALLS.md Pitfall 5)
        if resp.encoding and resp.encoding.lower() in ("iso-8859-1", "latin-1"):
            resp.encoding = resp.apparent_encoding or "utf-8"

        # Content-Type check: skip non-HTML
        content_type = resp.headers.get("Content-Type", "")
        if "text/html" not in content_type:
            item["full_text"] = ""
            return

        # trafilatura extraction (returns None on failure)
        # Source: trafilatura.readthedocs.io — extract() function signature
        text = trafilatura.extract(
            resp.text,
            include_comments=False,
            include_tables=False,
            favor_recall=True,
        )

        if text and len(text) >= MIN_CONTENT_CHARS:
            item["full_text"] = text
        else:
            item["full_text"] = ""

    except Exception as e:
        print(f"[warn] article fetch {url}: {e}", file=sys.stderr)
        item["full_text"] = ""
```

### Pattern 2: Concurrent Article Fetching (in `article.py`)

```python
# Source: ARCHITECTURE.md; Python stdlib ThreadPoolExecutor docs
from concurrent.futures import ThreadPoolExecutor

def fetch_article_texts(items: list[dict]) -> None:
    """Mutates all items in place concurrently. Never raises."""
    with ThreadPoolExecutor(max_workers=10) as executor:
        list(executor.map(_fetch_one, items))
```

### Pattern 3: Wire Into `main.py`

```python
# In main.py — insert AFTER keyword filter, BEFORE sections assembly
from src.scrapers.article import fetch_article_texts

# Existing code:
all_rss_items = [item for item in all_rss_items if _keyword_match(item, keywords)]

# NEW LINE:
if all_rss_items:
    fetch_article_texts(all_rss_items)  # sets item["full_text"] in place

# Existing code continues:
if all_rss_items:
    sections.append({"title": "Top Stories", "items": all_rss_items, "type": "rss"})
```

### Pattern 4: Structured Summarizer

```python
# Source: ARCHITECTURE.md; extends existing summarize_items() pattern in summarizer.py
def summarize_items_structured(section_title: str, items: list) -> list[dict]:
    """One Claude call per section. Returns list of {"core_idea": str, "key_points": list[str]}."""
    if not items:
        return []

    _EMPTY = {"core_idea": "", "key_points": []}

    # Build numbered list; use full_text if available, else summary
    def _input_text(item: dict) -> str:
        ft = item.get("full_text", "")
        if ft and len(ft) >= 200:
            return ft[:6000]           # FETCH-04: truncate to 6000 chars
        return item.get("summary", "")[:1000]

    numbered = "\n\n".join(
        f"[{i}] TITLE: {item['title']}\nTEXT: {_input_text(item)}"
        for i, item in enumerate(items)
    )

    # max_tokens formula: per-item budget + overhead (PITFALLS.md Pitfall 8)
    max_tokens = min(4096, len(items) * 120 + 200)

    prompt = (
        f"Section: {section_title}\n\n"
        "For each article, return a JSON array with exactly one object per article.\n"
        "Each object must have:\n"
        '  "core_idea": one sentence capturing the main point\n'
        '  "key_points": exactly 5 short bullet points (strings)\n\n'
        "Example for 2 articles:\n"
        '[{"core_idea": "OpenAI released GPT-5.", "key_points": ["point 1", "point 2", "point 3", "point 4", "point 5"]}, '
        '{"core_idea": "Google cuts 20% of staff.", "key_points": ["p1", "p2", "p3", "p4", "p5"]}]\n\n'
        "Return ONLY the JSON array, no markdown fences.\n\n"
        f"{numbered}"
    )

    try:
        response = _get_client().messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=max_tokens,
            system=[{"type": "text", "text": _SYSTEM_PROMPT, "cache_control": {"type": "ephemeral"}}],
            messages=[
                {"role": "user", "content": prompt},
                {"role": "assistant", "content": "["},  # JSON prefill to prevent markdown wrapping
            ],
        )
        # Prepend the prefill character that Claude was forced to continue from
        raw = "[" + response.content[0].text.strip()

        # Strip any accidental markdown wrapping (defensive; prefill should prevent it)
        raw = re.sub(r'^```(?:json)?\s*', '', raw, flags=re.IGNORECASE)
        raw = re.sub(r'\s*```$', '', raw).strip()

        # Check stop_reason for truncation (PITFALLS.md Pitfall 8)
        if response.stop_reason == "max_tokens":
            print(f"[warn] structured summary truncated for section {section_title}", file=sys.stderr)

        result = json.loads(raw)

        if not isinstance(result, list):
            return [_EMPTY] * len(items)

        # Salvage partial results on length mismatch
        if len(result) != len(items):
            print(f"[warn] structured summary length mismatch: got {len(result)}, expected {len(items)}", file=sys.stderr)

        structured = []
        for i, item in enumerate(items):
            if i < len(result):
                structured.append(_safe_structured(result[i]))
            else:
                structured.append(_EMPTY.copy())
        return structured

    except Exception:
        return [_EMPTY.copy() for _ in items]


def _safe_structured(obj: dict) -> dict:
    """Normalize Claude output: ensure correct types and clamp key_points to 5."""
    kp_raw = obj.get("key_points", [])
    if isinstance(kp_raw, str):
        kp_raw = [kp_raw]  # Claude returned string instead of list
    kp = [str(p) for p in kp_raw[:5]]
    kp = (kp + [""] * 5)[:5]  # pad or truncate to exactly 5
    return {
        "core_idea": str(obj.get("core_idea", "")),
        "key_points": kp,
    }
```

### Pattern 5: `_summarize_one()` Branching in `main.py`

The existing `_summarize_one()` function in `main.py` (lines 46-58) calls `summarize_items()`
unconditionally. Replace that block:

```python
# BEFORE (lines 53-58 in main.py):
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

### Pattern 6: RSS HTML-in-Summary Fix (Pitfall 10)

Apply in `rss.py` at item-build time using stdlib only:

```python
# Add to rss.py (no new imports needed beyond stdlib html.parser)
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

# In fetch_rss(), change item construction:
items.append({
    "title": entry.get("title", "No title"),
    "url": entry.get("link", ""),
    "summary": _strip_html(entry.get("summary", "") or entry.get("description", "")),
})
```

### Anti-Patterns to Avoid

- **Fetching inside `summarizer.py`:** The summarizer must not make HTTP requests. Keep it Claude-only.
- **Raising from `_fetch_one`:** Any exception must be caught and converted to `item["full_text"] = ""`. The pipeline must never crash on a single article.
- **Setting `max_workers` to number-of-items:** Cap at 10. With 25 articles at 10 workers, worst-case is `ceil(25/10) × 8s = 24s`. Uncapped could trigger rate limits or connection exhaustion.
- **Using `timeout=10` (single int):** Use `timeout=(3.05, 8)` tuple — separate connect and read timeouts.
- **Not checking `stop_reason`:** Truncated JSON from Claude is the most common failure mode on large sections. Log and handle it.
- **Using assistant prefill without prepending the prefill character to the response:** When using `{"role": "assistant", "content": "["}`, Claude's response text does NOT include the `[` — you must prepend it manually before `json.loads()`.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Article body extraction | Custom `<p>` concatenation or BeautifulSoup heuristics | `trafilatura.extract()` | BS4 `<p>` extracts nav/footer garbage; trafilatura scores content density; returns `None` cleanly |
| Encoding detection | Manual charset sniffing | `resp.apparent_encoding` (requests/chardet already installed) | Handles Vietnamese UTF-8 misdetection correctly |
| JSON prefill | Prompt-only "return JSON" instruction | `{"role": "assistant", "content": "["}` in messages | Prefill eliminates markdown wrapping more reliably than instruction alone |

**Key insight:** The trafilatura vs BS4 choice is not cosmetic — BS4 `find_all('p')` on a modern news page extracts 40-60% boilerplate (navigation labels, cookie banners, sidebar teasers). Trafilatura uses content-density scoring to identify the main article block; its failure mode (returning `None`) is clean and easy to handle.

---

## Common Pitfalls

### Pitfall 1: Paywall/Bot-Detection Returns Poison Content (HTTP 200, short text)
**What goes wrong:** Sites like The Verge serve HTTP 200 with a cookie consent gate or Cloudflare challenge. `trafilatura` extracts "Please enable JavaScript" or "Subscribe to read more". The 200-char threshold triggers fallback correctly only if the extracted text is actually short — some consent pages are longer than 200 chars.
**Why it happens:** `requests` does not execute JS; Cloudflare challenge is HTML returned as 200.
**How to avoid:** `MIN_CONTENT_CHARS = 200` catches most cases. `trafilatura` usually returns `None` or very short text for JS-challenge pages. Accept that some consent-page poison text may slip through; the structured summary will be low-quality but the pipeline will not crash.
**Warning signs:** Multiple articles from the same domain produce identical `core_idea` text.

### Pitfall 2: `key_points` Count Mismatch from Claude Haiku
**What goes wrong:** Haiku returns 3-4 points (short article) or 6-7 (long article). The renderer may show blank bullet slots or extra points.
**How to avoid:** `_safe_structured()` clamps: `(kp + [""] * 5)[:5]`. Apply always, unconditionally.

### Pitfall 3: Markdown-Wrapped JSON Despite Instruction
**What goes wrong:** Haiku wraps the array in ` ```json ... ``` ` code fences despite "no markdown" instruction.
**How to avoid:** Use assistant prefill (`{"role": "assistant", "content": "["}`) — this forces Haiku to start its response mid-JSON. Then prepend `"["` before parsing. The existing regex strip is a secondary fallback.

### Pitfall 4: `max_tokens` Truncation Produces Invalid JSON
**What goes wrong:** With 25 articles and `max_tokens=1024`, Claude's response is cut mid-JSON array. `json.loads()` raises `JSONDecodeError`.
**How to avoid:** Use formula `min(4096, len(items) * 120 + 200)`. Check `response.stop_reason == "max_tokens"` and log warning. Wrap `json.loads()` in `try/except`.

### Pitfall 5: Vietnamese Site Encoding Garbling (VnExpress, Tuoi Tre, Tinhte)
**What goes wrong:** `requests` defaults to `ISO-8859-1` when no charset in Content-Type. `resp.text` contains mojibake. `trafilatura` receives garbled input.
**How to avoid:**
```python
if resp.encoding and resp.encoding.lower() in ("iso-8859-1", "latin-1"):
    resp.encoding = resp.apparent_encoding or "utf-8"
```
Apply before accessing `resp.text`.

### Pitfall 6: Hacker News URLs Are Not Articles (PDF, GitHub repo, YouTube)
**What goes wrong:** HN RSS items link to PDFs, GitHub repos, YouTube — not text articles. `requests` downloads binary; `trafilatura` gets garbage input.
**How to avoid:**
```python
SKIP_URL_PATTERNS = (".pdf", "youtube.com/watch", "youtu.be/", "github.com/")
if any(p in url for p in SKIP_URL_PATTERNS):
    item["full_text"] = ""
    return
```
Also check `resp.headers.get("Content-Type", "")` — skip if not `text/html`.

### Pitfall 7: RSS `summary` Field Contains HTML Markup (SUMM-04 related)
**What goes wrong:** VnExpress and Tinhte.vn embed `<img>`, `<a>`, `<p>` in the RSS `summary` field. When this is passed as fallback text to Claude, key points contain raw HTML fragments.
**How to avoid:** Apply `_strip_html()` in `rss.py` at item construction time. Uses stdlib `html.parser` — no new dependency.

### Pitfall 8: GitHub Actions IP Blocks (403/429 from News Sites)
**What goes wrong:** AWS `us-east-1` IPs are in Cloudflare/Fastly blocklists. News publishers return 403 for these ranges.
**How to avoid:** Treat HTTP 403, 429, 451 as fallback triggers (not fatal errors). `resp.raise_for_status()` already converts these to exceptions, and the outer `except Exception` catches them and sets `item["full_text"] = ""`.

---

## Code Examples

### trafilatura.extract() Signature (from official docs)
```python
# Source: trafilatura.readthedocs.io (VERIFIED)
import trafilatura

# Pass pre-fetched HTML string; returns str or None
text = trafilatura.extract(
    filecontent=html_string,       # str, the HTML
    include_comments=False,        # skip comment sections
    include_tables=False,          # skip data tables
    favor_recall=True,             # prefer more text over precision
)
# Returns None if extraction fails — clean fallback signal
```

### ThreadPoolExecutor Pattern (from Python stdlib)
```python
# Source: ARCHITECTURE.md; Python docs
from concurrent.futures import ThreadPoolExecutor

def fetch_article_texts(items: list[dict]) -> None:
    with ThreadPoolExecutor(max_workers=10) as executor:
        list(executor.map(_fetch_one, items))
    # executor.map() raises the first exception from any worker —
    # MUST ensure _fetch_one() never raises (catches all exceptions internally)
```

### Existing JSON Strip Pattern (from summarizer.py — re-use exactly)
```python
# Source: src/summarizer.py lines 74-75 (VERIFIED from codebase)
raw = re.sub(r'^```\w*\s*', '', raw)
raw = re.sub(r'\s*```$', '', raw).strip()
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `newspaper3k` | `trafilatura` | 2021-2023 | newspaper3k abandoned; trafilatura now the ecosystem standard |
| Single-value timeout `timeout=10` | Tuple timeout `timeout=(connect, read)` | requests >=2.x | Separates connect hang from read stall; prevents 20s worst case |
| JSON-only instruction | Assistant prefill + JSON instruction | Anthropic API prompt caching era | Virtually eliminates markdown wrapping; cleaner than regex-only approach |

**trafilatura 2.0.0 note:** Latest version is 2.0.0 (released 2025). The `extract()` function API is backward-compatible with 1.x. The breaking change in 1.12.x was deprecation of CLI/function arguments related to `trafilatura.hashing` (renamed to `trafilatura.deduplication`) — not relevant to our usage of `extract()`. [VERIFIED: pip index versions trafilatura; Context7 /adbar/trafilatura HISTORY.md]

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | trafilatura 2.0.0 `extract()` API is backward-compatible with 1.12.x | Standard Stack | Low — only breaking change was `hashing` → `deduplication` rename, unrelated to `extract()` |
| A2 | `favor_recall=True` parameter exists in trafilatura 2.0.0 `extract()` | Code Examples | Low — confirmed as named parameter in official docs; if missing, omit and rely on default |
| A3 | Claude Haiku model ID `claude-haiku-4-5-20251001` remains valid | Pattern 4 | Low — use existing model ID from `summarizer.py`; do not change it |

**A1 and A2 are low-risk:** The `extract()` function signature was confirmed from official readthedocs (VERIFIED). If `favor_recall=True` is not accepted, remove it — the default behavior is still correct.

---

## Open Questions (RESOLVED)

1. **trafilatura 2.0.0 vs 1.12.2**
   - What we know: PyPI latest is 2.0.0; prior research recommended >=1.12. The `extract()` API is stable across both.
   - What's unclear: Whether 2.0.0 introduces any new required parameter or default-behavior change that affects our use case.
   - Recommendation: Pin to `2.0.0` (latest stable). If a regression is found, drop to `1.12.2`.

2. **Assistant prefill behavior with Anthropic SDK**
   - What we know: Anthropic's messages API supports an optional assistant turn as the last message to prefill the response. The SDK passes it as `{"role": "assistant", "content": "["}`.
   - What's unclear: Whether the current `anthropic==0.100.0` SDK version requires any special flag to enable prefill.
   - Recommendation: The SDK has supported prefill since early versions. Test in the first task; if it fails, fall back to the existing regex-strip approach.

3. **Phase 2 renderer compatibility**
   - What we know: Phase 1 leaves `html_renderer.py` unchanged. It still reads `item.get("ai_summary", "")`.
   - What's unclear: Whether the Phase 2 plan will update `_render_rss_items()` to read `core_idea` + `key_points` instead.
   - Recommendation: SUMM-04 only requires replacing fields in the data model. The renderer update is explicitly in Phase 2 (REND-01 through REND-04). No action needed in Phase 1.

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.9 | Runtime | Yes | 3.9 (.venv) | — |
| `requests` | FETCH-01 | Yes | 2.32.5 | — |
| `beautifulsoup4` | RSS HTML strip | Yes | 4.14.3 | — |
| `anthropic` | SUMM-01–04 | Yes | 0.100.0 | — |
| `trafilatura` | FETCH-02 | No (not yet installed) | — | Must install: `pip install trafilatura==2.0.0` |
| ANTHROPIC_API_KEY env var | Claude calls | Unknown at plan time | — | Pipeline exits early with clear error (existing check in main.py) |

**Missing dependencies:**
- `trafilatura==2.0.0` — must be installed and added to `requirements.txt` as the first task of this phase. No viable fallback (BS4 `<p>` extraction is not a substitute; it is the anti-pattern).

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest (already in use) |
| Config file | none — standard pytest discovery |
| Quick run command | `python -m pytest tests/ -q` |
| Full suite command | `python -m pytest tests/ -v` |

Current test status: 26 tests passing.

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| FETCH-01 | requests.get called with timeout=(3.05,8) | unit | `python -m pytest tests/test_article.py -x` | No — Wave 0 |
| FETCH-02 | trafilatura.extract called on resp.text | unit | `python -m pytest tests/test_article.py -x` | No — Wave 0 |
| FETCH-03 | full_text="" when fetch fails; summary used as input | unit | `python -m pytest tests/test_article.py -x` | No — Wave 0 |
| FETCH-03 | full_text="" when extracted text < 200 chars | unit | `python -m pytest tests/test_article.py -x` | No — Wave 0 |
| FETCH-04 | text truncated to 6000 chars before Claude prompt | unit | `python -m pytest tests/test_summarizer.py -x` | Partially — Wave 0 |
| FETCH-05 | ThreadPoolExecutor used; all items mutated before return | unit | `python -m pytest tests/test_article.py -x` | No — Wave 0 |
| SUMM-01 | Claude response parsed to core_idea + key_points | unit | `python -m pytest tests/test_summarizer.py::test_summarize_items_structured_returns_structured -x` | No — Wave 0 |
| SUMM-02 | One Claude call per section, not per article | unit | `python -m pytest tests/test_summarizer.py -x` | No — Wave 0 |
| SUMM-03 | Malformed JSON returns empty dicts; no crash | unit | `python -m pytest tests/test_summarizer.py::test_summarize_items_structured_bad_json_falls_back -x` | No — Wave 0 |
| SUMM-03 | key_points wrong length → clamped/padded to 5 | unit | `python -m pytest tests/test_summarizer.py -x` | No — Wave 0 |
| SUMM-04 | RSS items get core_idea + key_points; GitHub/Reddit keep ai_summary | integration | `python -m pytest tests/test_summarizer.py -x` | No — Wave 0 |

### Sampling Rate
- **Per task commit:** `python -m pytest tests/ -q`
- **Per wave merge:** `python -m pytest tests/ -v`
- **Phase gate:** Full suite green (`26 + N new tests`) before phase close

### Wave 0 Gaps
- `tests/test_article.py` — covers FETCH-01, FETCH-02, FETCH-03, FETCH-05 and all skip/fallback scenarios
- New test functions in `tests/test_summarizer.py` — covers SUMM-01, SUMM-02, SUMM-03, SUMM-04

*(Existing test_summarizer.py exists but has no tests for `summarize_items_structured`)*

---

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | No | No user auth in this pipeline |
| V3 Session Management | No | No sessions |
| V4 Access Control | No | Single-user local tool |
| V5 Input Validation | Yes (limited) | HTML from untrusted sites is parsed by trafilatura (not eval'd); Claude prompt injection via article text is accepted risk for personal digest |
| V6 Cryptography | No | No secrets stored in new code |

### Known Threat Patterns

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Prompt injection via article body | Tampering | Accept risk — personal tool, no privileged actions taken on Claude output; output is HTML displayed to owner only |
| SSRF via RSS item URL | Tampering | URLs come from trusted RSS feeds configured by owner in feeds.yaml; no user-supplied URLs |
| Large binary download via non-article URL | DoS | Content-Type check + URL skip patterns prevent PDF/binary download |

---

## Sources

### Primary (HIGH confidence)
- `src/main.py`, `src/summarizer.py`, `src/scrapers/rss.py`, `src/html_renderer.py` — direct codebase inspection
- `.planning/research/ARCHITECTURE.md` — project architecture research (2026-05-10)
- `.planning/research/PITFALLS.md` — domain pitfalls (2026-05-10)
- `.planning/research/STACK.md` — library selection rationale (2026-05-10)
- Context7 `/websites/trafilatura_readthedocs_io_en` — `extract()` function signature (VERIFIED)
- Context7 `/adbar/trafilatura` — usage patterns and HISTORY.md (VERIFIED)
- `pip index versions trafilatura` — confirmed latest version 2.0.0 (VERIFIED)
- `python -m pytest tests/ -q` — 26 existing tests passing (VERIFIED)

### Secondary (MEDIUM confidence)
- `.planning/REQUIREMENTS.md` — requirement IDs and descriptions
- `.planning/STATE.md` — current project state and locked decisions

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — trafilatura 2.0.0 confirmed on PyPI; all other libraries verified in requirements.txt and installed venv
- Architecture: HIGH — derived from direct codebase inspection; mutation-in-place pattern matches existing code
- Pitfalls: HIGH — grounded in existing codebase patterns and prior domain research
- Code examples: HIGH — function signatures verified against official trafilatura docs; patterns verified against existing summarizer.py

**Research date:** 2026-05-10
**Valid until:** 2026-06-10 (trafilatura is actively maintained; API is stable; check for 2.x point releases)
