---
phase: 01-backend
verified: 2026-05-11T13:23:31Z
status: human_needed
score: 9/9 must-haves verified
overrides_applied: 0
human_verification:
  - test: "Run `python main.py` end-to-end with ANTHROPIC_API_KEY set and inspect output"
    expected: "Digest completes; console shows 'Fetching full text for N articles …'; RSS items in output/YYYY-MM-DD.md have non-empty core_idea and exactly 5 key_points; GitHub/Reddit sections show ai_summary text; no tracebacks"
    why_human: "Live run requires real API key and network; verifiable only at runtime against actual RSS feeds"
  - test: "Observe fetch concurrency by timing a run with 20-30 RSS items"
    expected: "Total fetch phase visibly completes faster than sequential would (SC3 — parallelism observable in elapsed time)"
    why_human: "ThreadPoolExecutor concurrency is code-verified but wall-clock parallelism benefit can only be confirmed via a live run"
---

# Phase 1: Backend Verification Report

**Phase Goal:** Build the article-fetching and structured-summarization backend — every RSS item ends up with core_idea + key_points[5] instead of ai_summary; GitHub and Reddit sections keep existing ai_summary behavior.
**Verified:** 2026-05-11T13:23:31Z
**Status:** human_needed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|---------|
| 1 | fetch_article_texts(items) sets item['full_text'] on every item (str, may be empty) | VERIFIED | `src/scrapers/article.py` lines 39-42: mutates all items via ThreadPoolExecutor.map(_fetch_one); test_fetch_article_texts_mutates_all_items confirms return None + all full_text set |
| 2 | Article fetch failure or extracted text < 200 chars yields item['full_text'] = '' (never raises) | VERIFIED | `_fetch_one` lines 34-36: broad `except Exception` sets full_text=""; test_timeout_falls_back_to_empty, test_short_extracted_text_is_empty, test_trafilatura_returns_none_is_empty all pass |
| 3 | URLs ending in .pdf, youtube.com/watch, youtu.be/, or github.com/ are skipped without HTTP call | VERIFIED | `_fetch_one` lines 15-18: `any(p in url for p in SKIP_URL_PATTERNS)` guard; 4 skip tests pass |
| 4 | RSS items returned by fetch_rss have plain-text summary (HTML tags and entities stripped) | VERIFIED | `src/scrapers/rss.py` line 38: `_strip_html(entry.get("summary","") or entry.get("description",""))`; 4 HTML-stripping tests pass |
| 5 | All article fetches in fetch_article_texts run concurrently via ThreadPoolExecutor(max_workers=10) | VERIFIED | `src/scrapers/article.py` line 41: `with ThreadPoolExecutor(max_workers=10) as executor:`; test_fetch_article_texts_uses_thread_pool_with_10_workers passes |
| 6 | summarize_items_structured issues exactly one Claude call per section | VERIFIED | `src/summarizer.py` lines 177-186: single `_get_client().messages.create(...)` call; test_summarize_items_structured_one_call_per_section passes |
| 7 | Returned list has exactly len(items) entries; each entry has core_idea + key_points always exactly 5 strings; malformed JSON returns empty fallback | VERIFIED | `_safe_structured` enforces 5-item key_points; length-mismatch salvage at lines 202-207; 14 structured summarizer tests all pass |
| 8 | Existing summarize_items() and get_top_highlights() behavior is unchanged | VERIFIED | Functions at lines 85-119 and 46-82 of summarizer.py untouched; original 7 summarizer tests still pass |
| 9 | _summarize_one branches on section type: rss gets core_idea+key_points, github/reddit gets ai_summary | VERIFIED | `main.py` lines 55-63: `if section.get("type") == "rss"` branch; all 6 test_main.py tests pass including cross-branch non-leakage assertions |

**Score:** 9/9 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `requirements.txt` | trafilatura==2.0.0 pin | VERIFIED | Line 6: `trafilatura==2.0.0` |
| `src/scrapers/article.py` | fetch_article_texts + _fetch_one, min 40 lines | VERIFIED | 43 lines; exports both functions; ThreadPoolExecutor(max_workers=10); timeout=(3.05,8); trafilatura.extract with favor_recall=True |
| `src/scrapers/rss.py` | _strip_html applied to summary | VERIFIED | 2 occurrences of `_strip_html`; class _Stripper(HTMLParser) present |
| `tests/test_article.py` | 14 tests covering all behaviors | VERIFIED | 14 test functions present; all pass |
| `src/summarizer.py` | summarize_items_structured + _safe_structured | VERIFIED | Both functions present at lines 122-209; import sys added at line 3 |
| `tests/test_summarizer.py` | Tests for structured summarizer | VERIFIED | 14 new tests appended (lines 72-252); 21 total tests pass |
| `main.py` | fetch_article_texts wired + _summarize_one branched | VERIFIED | fetch_article_texts imported and called (line 14, 100); summarize_items_structured imported and branched (line 15, 56) |
| `tests/test_main.py` | 6 tests for branching logic | VERIFIED | 6 tests present; all pass |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| src/scrapers/article.py::_fetch_one | trafilatura.extract | module import + call | VERIFIED | Line 5: `import trafilatura`; line 27: `trafilatura.extract(resp.text, ...)` |
| src/scrapers/article.py::fetch_article_texts | ThreadPoolExecutor | concurrent.futures import | VERIFIED | Line 2: `from concurrent.futures import ThreadPoolExecutor`; line 41: `ThreadPoolExecutor(max_workers=10)` |
| src/scrapers/rss.py::fetch_rss | _strip_html | wraps summary at item-construction | VERIFIED | Line 38: `_strip_html(entry.get("summary","") or entry.get("description",""))` |
| src/summarizer.py::summarize_items_structured | _get_client().messages.create | single call with assistant prefill "[" | VERIFIED | Lines 182-185: messages list ends with `{"role": "assistant", "content": "["}` |
| src/summarizer.py::summarize_items_structured | _safe_structured | normalizer per parsed object | VERIFIED | Line 204: `out.append(_safe_structured(result[i]))` |
| src/summarizer.py::summarize_items_structured | json.loads | wrapped in try/except | VERIFIED | Line 194: `result = json.loads(raw)` inside try block |
| main.py | src.scrapers.article.fetch_article_texts | import + call after keyword filter | VERIFIED | Line 14: `from src.scrapers.article import fetch_article_texts`; line 100: `fetch_article_texts(all_rss_items)` |
| main.py | src.summarizer.summarize_items_structured | import + branching call in _summarize_one | VERIFIED | Line 15: in summarizer import; line 56: `per_item = summarize_items_structured(title, section["items"])` |
| main.py::_summarize_one | section type check | if section.get("type") == "rss" | VERIFIED | Line 55: `if section.get("type") == "rss":` |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|--------------|--------|-------------------|--------|
| src/scrapers/article.py | full_text per item | trafilatura.extract(resp.text) from requests.get | Yes — live HTTP fetch or empty string fallback | FLOWING |
| src/summarizer.py::summarize_items_structured | core_idea, key_points | Claude API response parsed via json.loads | Yes — real Claude call or safe empty fallback | FLOWING |
| main.py::_summarize_one (rss branch) | item["core_idea"], item["key_points"] | structured from summarize_items_structured result | Yes — wired from summarizer output | FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| fetch_article_texts sets full_text="" on empty URL | `python -c "from src.scrapers.article import fetch_article_texts; items=[{'url':'','summary':'s'}]; fetch_article_texts(items); assert items[0]['full_text']==''"`  | exit 0 | PASS |
| _strip_html removes tags and decodes entities | `python -c "from src.scrapers.rss import _strip_html; print(_strip_html('&lt;p&gt;hi&lt;/p&gt;'))"` | `hi` | PASS |
| _safe_structured pads key_points to 5 | `python -c "from src.summarizer import _safe_structured; r=_safe_structured({'core_idea':'x','key_points':['a']}); assert len(r['key_points'])==5"` | exit 0 | PASS |
| main imports resolve | `python -c "import main; assert callable(main.fetch_article_texts) and callable(main.summarize_items_structured)"` | exit 0 | PASS |
| Full test suite | `python -m pytest tests/ -q` | 64 passed in 1.05s | PASS |
| trafilatura version | `python -c "import trafilatura; print(trafilatura.__version__)"` | 2.0.0 | PASS |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|---------|
| FETCH-01 | 01-01 | Fetch full HTML via requests with timeout | SATISFIED (deviation noted) | requests.get with timeout=(3.05,8); REQUIREMENTS.md says "10-second timeout" but PLAN spec prescribes (3.05,8) tuple — functional equivalent; PATTERNS.md line 137 confirms intentional choice |
| FETCH-02 | 01-01 | Extract clean text via trafilatura | SATISFIED | trafilatura.extract called with favor_recall=True; min 200-char threshold |
| FETCH-03 | 01-01 | Fallback to RSS summary on failure/short text | SATISFIED | _fetch_one returns full_text="" on failure; summarize_items_structured uses summary[:1000] when full_text is empty or < 200 chars |
| FETCH-04 | 01-02 | Truncate extracted text to 6000 chars before Claude | SATISFIED | `ft[:6000]` at summarizer.py line 154; test_summarize_items_structured_truncates_to_6000 passes |
| FETCH-05 | 01-01/01-03 | All RSS fetches concurrent before summarization | SATISFIED | ThreadPoolExecutor(max_workers=10) in article.py; fetch called before sections.append in main.py |
| SUMM-01 | 01-02 | Claude returns {"core_idea": str, "key_points": [5 strings]} per article | SATISFIED | summarize_items_structured + _safe_structured enforce this shape |
| SUMM-02 | 01-02 | One Claude call per section (not per article) | SATISFIED | Single messages.create call; test_one_call_per_section confirms |
| SUMM-03 | 01-02 | Malformed JSON / wrong key_points length handled gracefully | SATISFIED | try/except around json.loads; _safe_structured clamps/pads; 4 failure-mode tests pass |
| SUMM-04 | 01-03 | RSS ai_summary replaced by core_idea + key_points | SATISFIED | _summarize_one rss branch assigns core_idea/key_points never ai_summary; test_summarize_one_rss asserts ai_summary not in items |

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|---------|--------|
| None found | — | — | — | — |

No TODO/FIXME/placeholder comments, no return null/empty stubs in production code paths, no hardcoded empty arrays for rendering. The empty-fallback dicts in summarizer are intentional safety nets (not stubs), all guarded by `except Exception` blocks with real code paths above them.

### Human Verification Required

#### 1. End-to-End Live Run

**Test:** With ANTHROPIC_API_KEY set, run `python main.py` from the project root.
**Expected:**
- Console prints "Fetching full text for N articles …"
- Digest completes without tracebacks
- Output file `output/YYYY-MM-DD.html` is generated
- Each RSS article in the output has a non-empty core_idea line and exactly 5 key_points
- GitHub/Reddit sections retain their existing ai_summary prose format
- `[warn]` lines for individual article fetch failures are acceptable (they prove fallback works)

**Why human:** Requires a live ANTHROPIC_API_KEY and real network access to RSS feeds. The concurrency and Claude API response cannot be exercised by unit tests with mocks.

#### 2. Parallel Fetch Timing (SC3)

**Test:** Time a run with 20-30 RSS articles: `time python main.py` and compare against a sequential baseline (or simply observe that the fetch phase completes in a few seconds, not 20-30 sequential timeouts).
**Expected:** Total fetch time for 20-30 articles is under 20 seconds (parallel wall-clock), not 60-90+ seconds (sequential worst-case).
**Why human:** Wall-clock parallelism benefit requires a live run; cannot be verified by mocking ThreadPoolExecutor.

### Gaps Summary

No blocking gaps identified. All 9 must-have truths are VERIFIED in the codebase. All 9 requirements (FETCH-01 through FETCH-05, SUMM-01 through SUMM-04) are satisfied in code. All 64 tests pass. The FETCH-01 timeout deviation (3.05, 8 vs "10-second") is an intentional refinement prescribed by the PLAN spec — not a gap.

Two human verification items remain per the ROADMAP success criteria (SC1 and SC3 require live execution to confirm end-to-end behavior).

---

_Verified: 2026-05-11T13:23:31Z_
_Verifier: Claude (gsd-verifier)_
