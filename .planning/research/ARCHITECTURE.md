# Architecture: Full-Text Fetch + Structured AI Summarization

**Project:** daily-info-digest  
**Milestone:** Full-text article fetching + structured per-article AI breakdown  
**Researched:** 2026-05-10  
**Confidence:** HIGH — based on direct codebase analysis; no speculative claims

---

## Current Pipeline (Baseline)

```
feeds.yaml
    │
    ▼
main.py
    ├── fetch_rss()          → [{title, url, summary, source}]  ← RSS only
    ├── fetch_github_trending()
    └── fetch_reddit_posts()
    │
    ▼
sections = [{title, items, type}, ...]
    │
    ├── get_top_highlights()          1 Claude call (RSS items)
    └── _summarize_one() × N          ThreadPoolExecutor
          ├── summarize_section()     1 Claude call per section
          └── summarize_items()       1 Claude call per section → ai_summary: str
    │
    ▼
render_digest()        → output/YYYY-MM-DD.md
render_html_digest()   → output/YYYY-MM-DD.html
```

---

## Target Pipeline (After Milestone)

```
feeds.yaml
    │
    ▼
main.py
    ├── fetch_rss()          → [{title, url, summary, source}]
    ├── fetch_github_trending()
    └── fetch_reddit_posts()
    │
    ▼ (RSS items only)
fetch_article_text()         ← NEW: src/scrapers/article.py
  ThreadPoolExecutor(max_workers=10)
  per item: GET url → BeautifulSoup → join <p> text
  fallback chain: full_text → item["summary"] → ""
    │
    ▼
item["full_text"] populated on all RSS items
    │
    ├── get_top_highlights()          unchanged
    └── _summarize_one() × N          ThreadPoolExecutor (unchanged structure)
          ├── summarize_section()     unchanged
          └── summarize_items_structured()   ← REPLACES summarize_items() for RSS
                1 Claude call per section
                prompt: return JSON array of {core_idea, key_points}
                item["core_idea"] = str
                item["key_points"] = list[str]  (5 elements)
    │
    ▼
_render_rss_items()    ← renders core_idea + key_points dropdown
_render_accordion()    ← unchanged (GitHub/Reddit keep ai_summary: str path)
```

---

## Question 1: Where to Insert the Article Fetch Step

**Recommendation: New pass in `main.py` immediately after RSS items are collected and deduplicated, before `_summarize_one` is called.**

Rationale:
- The deduplication and keyword filter already run in `main.py` before sections are assembled. Article fetching must happen after dedup (no point fetching a URL we'll discard) and before summarization (the full text is the input to Claude).
- Inserting inside `rss.py` would conflate fetching the feed (fast, rarely fails) with fetching article pages (slow, frequently fails). These are different failure modes and should be isolated.
- Inserting inside `summarizer.py` would make the summarizer responsible for network I/O — a violation of its single responsibility (Claude API calls). The summarizer only consumes data; it must not produce it.
- A separate pass in `main.py` keeps the orchestration visible at the top level, matches the existing pattern, and makes it easy to skip (e.g., if a future config flag disables full-text fetching).

**Implementation location:** `src/scrapers/article.py` — new module with a single public function `fetch_article_texts(items: list[dict]) -> None` that mutates items in place by setting `item["full_text"]`.

The function is called once in `main.py` after `all_rss_items` is finalized:

```python
# After dedup + keyword filter, before sections assembly
if all_rss_items:
    fetch_article_texts(all_rss_items)  # sets item["full_text"] in place
    sections.append({"title": "Top Stories", "items": all_rss_items, "type": "rss"})
```

Mutation-in-place matches the existing pattern: `_summarize_one` mutates `section["summary"]`, `item["ai_summary"]` in place. No new return-value wiring needed.

---

## Question 2: Concurrency Model for Article Fetching

**Recommendation: `ThreadPoolExecutor(max_workers=10)`, per-request timeout of 8 seconds, no rate limiter.**

### Thread pool size

With 20–30 RSS articles and pure network I/O (no CPU work), 10 workers is the right ceiling:
- Fewer workers (e.g., 3–5) means sequential batches and unnecessary wall-clock time.
- More workers (e.g., 30) risks overwhelming a news site's connection limit per IP and triggering 429 or TCP resets. 10 is a conventional respectful ceiling.
- The existing `ThreadPoolExecutor()` in `main.py` uses the default (min(32, os.cpu_count()+4)), which for a 4-core CI runner is 8. Matching that ballpark is consistent.

### Timeout

8 seconds per article, applied to both connect and read:
```python
requests.get(url, timeout=8, headers={"User-Agent": "Mozilla/5.0 ..."})
```
- Paywall redirects and bot-detection pages typically respond immediately (3xx or 200 with thin content) — the timeout is a backstop for hung connections.
- GitHub Actions has a 6-hour job limit. With 30 articles and 10 workers, worst case is 3 batches × 8 s = 24 s of fetch time. Acceptable.
- `requests` `timeout` applies per connection attempt and per read chunk, not end-to-end. An 8-second value is safe for typical article sizes.

### Rate limiting

No per-domain rate limiter needed for this use case:
- The digest fetches each article URL once per day.
- URLs come from different domains (each RSS feed points to a different publisher).
- A single fetch per domain per day does not trigger rate limits on any mainstream news site.
- Adding a rate limiter would be speculative complexity.

---

## Question 3: How to Batch Structured Claude Calls

**Recommendation: One Claude call per section (same batching as `summarize_items`), returning a JSON array of `{core_idea, key_points}` objects.**

### Option A: One call per article (individual)

- Pros: Simple prompt, simple response parsing.
- Cons: With 20–30 RSS articles this means 20–30 Claude API calls where today there is 1. At claude-haiku pricing (~$0.00025 per 1K input tokens), this is not a cost disaster, but it is a latency disaster — 20–30 serial calls even with parallelism introduces significant overhead and token overhead (system prompt repeated 30 times without caching benefit per call).
- Reject: Violates the "keep calls batched where possible" constraint in PROJECT.md.

### Option B: One call per section (batch JSON array)

- Pros: Matches existing `summarize_items` pattern exactly. System prompt is cached once per section call. Claude sees all articles in context, which improves coherence. Only 1 extra Claude call per RSS section (replacing the existing `summarize_items` call — not in addition to it).
- Cons: JSON array response parsing is slightly more complex; must handle length mismatches.
- Accept: This is the right approach.

The prompt becomes:

```
For each article below, return a JSON array with exactly one object per article:
[{"core_idea": "One sentence.", "key_points": ["point 1", ..., "point 5"]}, ...]

Article text takes precedence over the snippet. If article text is absent, use the snippet.
```

Max tokens bumps from 1024 to ~2048 to accommodate the expanded structured output (5 points × ~15 words × 30 articles ≈ 2250 words ≈ ~2800 tokens).

### Function name

Replace `summarize_items()` with `summarize_items_structured()` for RSS sections. Keep the original `summarize_items()` for GitHub/Reddit (those sections still return `ai_summary: str` — the structured format does not apply to them per PROJECT.md out-of-scope rules).

---

## Question 4: Data Model — Field Shape

**Recommendation: Replace `ai_summary: str` with `core_idea: str` and `key_points: list[str]` directly on RSS items. Keep `ai_summary: str` on GitHub/Reddit items.**

### Why not a nested dict (`ai_summary: dict`)?

A single `ai_summary` field that sometimes holds a string and sometimes holds a dict creates a type union that every consumer must branch on. The html_renderer.py already branches on `if ai_summary:` in two places. Adding `isinstance(ai_summary, dict)` checks doubles the branching complexity.

### Why not a single new field alongside `ai_summary`?

Keeping `ai_summary` populated with a string for RSS items "just in case" means carrying dead data. The renderer would need to decide which field wins.

### Recommended shape for RSS items after this milestone:

```python
{
    "title":      str,
    "url":        str,
    "summary":    str,   # raw RSS excerpt — unchanged
    "source":     str,   # feed name — unchanged
    "full_text":  str,   # fetched article body (may be "" on failure)
    "core_idea":  str,   # Claude structured summary — replaces ai_summary
    "key_points": list[str],  # 5 elements; Claude structured summary
}
```

GitHub/Reddit items retain:
```python
{
    "title":      str,
    "url":        str,
    "summary":    str,
    "ai_summary": str,   # 1-2 sentence string — unchanged
    # + "stars" or "score" as before
}
```

### Renderer impact

`_render_rss_items()` in `html_renderer.py` currently reads `item.get("ai_summary", "")`. After the migration, it reads `item.get("core_idea", "")` and `item.get("key_points", [])`. The branch that checks `if ai_summary:` becomes `if core_idea:`.

`_render_accordion()` for GitHub/Reddit keeps `item.get("ai_summary", "")` unchanged — no modification needed.

This is a clean boundary: RSS rendering path changes, accordion rendering path does not.

---

## Question 5: Error Handling

### Article fetch errors

Every article fetch error must be silent from the user's perspective (the digest continues) but the fallback must be deterministic. Use this precedence in `fetch_article_texts`:

```python
try:
    resp = requests.get(url, timeout=8, headers={...})
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    paragraphs = [p.get_text(strip=True) for p in soup.find_all("p")]
    text = " ".join(paragraphs)
    item["full_text"] = text if len(text) > 200 else ""
except Exception as e:
    print(f"[warn] article fetch {url}: {e}", file=sys.stderr)
    item["full_text"] = ""
```

The 200-character minimum guards against bot-detection pages that return a thin 200 OK with "Please enable JavaScript" body text. These pages have valid status codes and valid HTML — the length check is the only reliable signal.

### Fallback chain in the Claude prompt

Rather than implementing fallback logic in Python (checking `full_text` vs `summary` before building the prompt), pass both to Claude and instruct it to prefer full text:

```
For each article, you are given a title, a full_text (may be empty), and a snippet.
Use full_text if non-empty; otherwise use snippet.
```

This keeps the Python orchestration simple. Claude handles the conditional gracefully.

### Malformed Claude JSON responses

The existing `summarize_items()` already handles this: `json.loads()` inside a try/except, returning `[""] * len(items)` on failure. The new `summarize_items_structured()` must extend this:

```python
try:
    result = json.loads(raw)
    if isinstance(result, list) and len(result) == len(items):
        return result  # list of {"core_idea": str, "key_points": list}
except Exception:
    pass
# fallback: empty structured objects
return [{"core_idea": "", "key_points": []} for _ in items]
```

Length mismatch is the most common failure mode (Claude truncates when max_tokens is hit). Log it:

```python
if len(result) != len(items):
    print(f"[warn] structured summary length mismatch: got {len(result)}, expected {len(items)}", file=sys.stderr)
```

Partial results should be salvaged: zip the result list with items up to the shorter length, fill the rest with empty structured objects.

### Individual key_points validation

After JSON parsing, each item in the result should be validated:

```python
def _safe_structured(obj: dict) -> dict:
    return {
        "core_idea":  str(obj.get("core_idea", "")),
        "key_points": [str(p) for p in obj.get("key_points", [])[:5]],
    }
```

This guards against Claude returning a `key_points` that is a string instead of a list, or returning 7 points instead of 5.

---

## Question 6: Fallback Chain

The fallback chain has three levels, resolved at two different points:

**Level 1 — Article fetch (in `article.py`):**

```
full_text = fetched body text (if len > 200)
         OR "" (on any network/parse/length failure)
```

`item["full_text"]` is always set (never absent); it is either a non-empty string or `""`.

**Level 2 — Claude prompt construction (in `summarizer.py`):**

```
input_text = item["full_text"]   if len(item["full_text"]) > 200
           ELSE item["summary"]  if item["summary"]
           ELSE "(no content)"
```

The summarizer constructs the numbered prompt with `input_text`. This is a 3-line conditional, not a framework. Claude still makes the call — it simply receives better or worse input.

**Level 3 — Claude response failure (in `summarizer.py`):**

```
structured result = parsed JSON   if well-formed and correct length
                  = empty objects  if JSON parse fails or length mismatch
```

The renderer handles empty `core_idea` and empty `key_points` the same way it handles absent `ai_summary` today: no dropdown is rendered, the article title links directly to the URL.

---

## Component Boundaries

| Component | File | Responsibility | Inputs | Outputs |
|-----------|------|---------------|--------|---------|
| RSS scraper | `src/scrapers/rss.py` | Fetch and parse feed entries | feed URL, max_items | `[{title, url, summary}]` |
| Article fetcher | `src/scrapers/article.py` | Fetch full body text for each article | `list[dict]` (mutates in place) | sets `item["full_text"]` |
| Structured summarizer | `src/summarizer.py` | Claude call per section; returns structured breakdown | section items with `full_text` | sets `item["core_idea"]`, `item["key_points"]` |
| RSS renderer | `src/html_renderer.py` `_render_rss_items()` | Render structured breakdown dropdown | items with `core_idea`/`key_points` | HTML string |
| Accordion renderer | `src/html_renderer.py` `_render_accordion()` | Render GitHub/Reddit accordion | items with `ai_summary` | HTML string — no change |
| Orchestrator | `main.py` | Sequence all steps; fault isolation | `feeds.yaml` | calls article fetcher, then summarizer |

**Boundary rule:** `article.py` never touches Claude. `summarizer.py` never makes HTTP requests. `main.py` owns the sequencing. Neither renderer is aware of where data came from.

---

## Data Flow Direction

```
feeds.yaml
    │
    ▼
fetch_rss() ──────────────────────────────── [{title, url, summary, source}]
    │
    ▼ (dedup + keyword filter in main.py)
fetch_article_texts() ────────────────────── mutates: adds item["full_text"]
    │
    ▼
sections assembled [{title, items, type}]
    │
    ├── get_top_highlights() ──────────────── mutates: section["highlights"]
    │
    └── _summarize_one() per section (ThreadPoolExecutor)
          ├── summarize_section() ─────────── mutates: section["summary"]
          └── for RSS: summarize_items_structured()
                       mutates: item["core_idea"], item["key_points"]
              for GitHub/Reddit: summarize_items()
                       mutates: item["ai_summary"]
    │
    ▼
render_digest()       (reads core_idea/key_points for MD — optional enhancement)
render_html_digest()
    ├── _render_rss_items()    reads core_idea + key_points
    └── _render_accordion()   reads ai_summary (unchanged)
```

All mutations are additive. No existing field is removed during the migration. `ai_summary` simply becomes unpopulated for RSS items (it is never set on them by `summarize_items_structured`); the renderer checks `core_idea` first for RSS items.

---

## Suggested Build Order

**Step 1 — Article fetcher (`src/scrapers/article.py`)**

Build and test in isolation. Write a standalone script that calls `fetch_article_texts` on a hardcoded list of URLs and prints the `full_text` length for each. Verify:
- Successful fetch returns > 200 chars of clean text
- 404/timeout sets `full_text = ""`
- Paywall / JS-required page sets `full_text = ""` (length guard fires)
- Concurrency: 10 workers, 8-second timeout, ~30 URLs complete in < 30 seconds

This step has zero Claude API cost and zero risk to existing output.

**Step 2 — Wiring article fetcher into `main.py`**

Add the `fetch_article_texts(all_rss_items)` call after the keyword filter and before sections assembly. Run the full pipeline. Verify `item["full_text"]` is populated before Claude is called. No Claude prompt changes yet — output is identical to today.

**Step 3 — Structured summarizer (`summarize_items_structured` in `summarizer.py`)**

Add the new function alongside the existing `summarize_items`. Use the existing `summarize_items` as the template — same Claude client, same system prompt caching pattern, same JSON-strip regex. Only the prompt and response parsing change. The fallback (`[{"core_idea": "", "key_points": []}]`) mirrors the existing `[""] * len(items)` fallback.

Wire it in `_summarize_one` behind a type check:

```python
if section.get("type") == "rss":
    per_item = summarize_items_structured(title, section["items"])
    for item, structured in zip(section["items"], per_item):
        item["core_idea"] = structured["core_idea"]
        item["key_points"] = structured["key_points"]
else:
    per_item = summarize_items(title, section["items"])
    for item, ai_sum in zip(section["items"], per_item):
        item["ai_summary"] = ai_sum
```

**Step 4 — HTML renderer update (`_render_rss_items` in `html_renderer.py`)**

Replace the `ai_summary` rendering block with `core_idea` + `key_points`. The structure is:

```html
<details class="article-details">
  <summary>...</summary>
  <div class="article-ai-summary">
    <strong>Core idea:</strong> {core_idea}
    <ol>
      <li>{key_points[0]}</li>
      ...
    </ol>
    <a href="{url}">Read full article</a>
  </div>
</details>
```

The fallback (no dropdown) when `core_idea` is empty stays unchanged.

**Step 5 — End-to-end validation**

Run `python main.py` with the full config. Verify:
- All RSS articles have `core_idea` and `key_points` populated (or gracefully empty)
- HTML dropdown renders correctly for articles with full text
- HTML dropdown renders correctly for articles where full text fell back to RSS summary
- GitHub/Reddit sections are identical to before
- Total wall-clock time is within acceptable bounds (target: < 2 minutes)

---

## Key Risks and Mitigations

| Risk | Severity | Mitigation |
|------|----------|-----------|
| Claude response exceeds max_tokens mid-array | HIGH | Bump max_tokens to 2048; log length mismatches; salvage partial results |
| Paywall page passes length check (200+ chars of cookie consent text) | MEDIUM | Length threshold of 200 chars is a heuristic; acceptable false-positive rate for a personal digest |
| A slow article URL blocks a worker thread for 8 seconds | LOW | With 10 workers and 30 articles, worst-case latency is ceil(30/10) × 8 = 24 s — acceptable |
| GitHub/Reddit rendering broken by data model change | LOW | Those sections never call `summarize_items_structured`; `ai_summary` is still set on them; `_render_accordion` is not modified |
| Claude returns `key_points` as a string instead of list | LOW | `_safe_structured` validator normalizes the field before it is stored on the item |

---

*Architecture analysis: 2026-05-10 — based on direct source code inspection of main.py, src/summarizer.py, src/scrapers/rss.py, src/html_renderer.py, src/renderer.py, and .planning/codebase/*
