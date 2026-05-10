---
phase: 01-backend
plan: "03"
subsystem: orchestrator
tags: [main, wiring, rss, structured-summary, tdd]
dependency_graph:
  requires:
    - phase: 01-backend/01-01
      provides: fetch_article_texts from src.scrapers.article
    - phase: 01-backend/01-02
      provides: summarize_items_structured from src.summarizer
  provides:
    - main.py wired with fetch_article_texts call before summarization
    - _summarize_one branches on section type (rss vs github/reddit)
    - RSS items now get core_idea + key_points; GitHub/Reddit keep ai_summary
  affects: [phase-02-html-renderer]
tech-stack:
  added: []
  patterns: [type-based branching in orchestrator, pre-summarization fetch wiring, TDD red-green]

key-files:
  created:
    - tests/test_main.py
  modified:
    - main.py

key-decisions:
  - "Two separate `if all_rss_items:` blocks for fetch and append: keeps the fetch call surgical and out of the append guard scope"
  - "Branch inside _summarize_one on section.get('type') == 'rss': single dispatch point, no wrapper function needed"
  - "RSS items get core_idea + key_points (never ai_summary); GitHub/Reddit keep ai_summary (never core_idea/key_points) — clean split, no dual-shape items"

patterns-established:
  - "Section type determines summarization path: rss → structured; any other → per-item ai_summary"
  - "fetch_article_texts called after dedup+filter, before sections.append — all fetches complete before any summarization"

requirements-completed: [SUMM-04, FETCH-05]

duration: 5min
completed: 2026-05-10
---

# Phase 01 Plan 03: Orchestrator Wiring Summary

**Three surgical edits to main.py wire the article fetcher and structured summarizer so every RSS item gets core_idea + 5 key_points while GitHub/Reddit sections keep their existing ai_summary behavior.**

## Performance

- **Duration:** ~5 min
- **Started:** 2026-05-10T14:00:00Z
- **Completed:** 2026-05-10T14:05:00Z
- **Tasks:** 1 of 2 (Task 2 is a human-verify checkpoint, not yet approved)
- **Files modified:** 2

## Accomplishments

- Added `from src.scrapers.article import fetch_article_texts` to main.py imports
- Added `summarize_items_structured` to the summarizer import line
- Inserted `fetch_article_texts(all_rss_items)` call between keyword filter and sections.append, inside an `if all_rss_items:` guard, with a console log "Fetching full text for N articles …"
- Replaced the unconditional `summarize_items` call in `_summarize_one` with a branch: rss → `summarize_items_structured` + assigns `core_idea`/`key_points`; else → `summarize_items` + assigns `ai_summary`
- Created `tests/test_main.py` with 6 tests covering all branches and import resolution

## Task Commits

1. **Task 1 (RED): failing tests** - `fd0d908` (test(01-03): add failing tests for _summarize_one branching and fetch wiring)
2. **Task 1 (GREEN): main.py wiring** - `016242a` (feat(01-03): wire fetch_article_texts and branch _summarize_one for rss vs non-rss)

## Files Created/Modified

- `main.py` — three surgical changes: two new imports, one fetch call site, one branched block in `_summarize_one`
- `tests/test_main.py` — 6 new tests covering rss/github/reddit/no-type branches, isolation on summarize_section failure, and import smoke test

## Decisions Made

- Two separate `if all_rss_items:` guards: one for the fetch call, one for sections.append. Keeps the fetch wiring surgical without merging into the append block.
- Branching on `section.get("type") == "rss"` inside `_summarize_one`: single dispatch point. The else branch covers github, reddit, and any future section type that should get per-item ai_summary.
- RSS items do NOT receive `ai_summary`; GitHub/Reddit items do NOT receive `core_idea`/`key_points`. Clean split at the data model level.

## Test Counts

| Plan | Tests Added | Cumulative Total |
|------|-------------|-----------------|
| Pre-existing | 44 | 44 |
| Plan 01 (article + rss) | +14 | 58 |
| Plan 02 (structured summarizer) | +14 | 58 (pre-merged from plan 01 base) |
| Plan 03 (this plan) | +6 | 64 |

All 64 tests pass.

## main.py Diff Summary

**Change 1 — Imports (lines 11-14):**
Added `from src.scrapers.article import fetch_article_texts` after reddit import.
Added `summarize_items_structured` to the summarizer import line.

**Change 2 — fetch wiring (after keyword filter):**
```python
if all_rss_items:
    print(f"Fetching full text for {len(all_rss_items)} articles …", flush=True)
    fetch_article_texts(all_rss_items)
```
Inserted between the filter and the existing `if all_rss_items: sections.append(...)`.

**Change 3 — _summarize_one branching (lines 53-58):**
```python
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

## Deviations from Plan

None — plan executed exactly as written. The three changes to main.py and the 6 tests match the plan's action spec verbatim.

## Known Stubs

None. Both `fetch_article_texts` and `summarize_items_structured` are fully implemented in Plans 01 and 02. The branching wiring is complete. No placeholder values, no hardcoded empty data.

## Notes for Phase 2 (HTML Renderer)

The item dict shape is now split by section type:

- **RSS items:** expose `core_idea` (str) and `key_points` (list of exactly 5 strings). No `ai_summary`.
- **GitHub / Reddit items:** expose `ai_summary` (str). No `core_idea` or `key_points`.

The HTML renderer (`src/html_renderer.py`) must read both shapes. Specifically:
- `_render_rss_items()` should read `item.get("core_idea")` and `item.get("key_points", [])` to render the structured breakdown dropdown
- `_render_accordion()` (for github/reddit) should continue reading `item.get("ai_summary", "")` as before

## Threat Surface Scan

No new network endpoints, auth paths, file access patterns, or schema changes beyond those already tracked in Plans 01 and 02. T-01-10 (data shape regression) mitigated by `test_main.py` tests asserting cross-branch non-leakage. T-01-13 (existing-test regression) mitigated by all 64 tests staying green.

## Self-Check: PASSED

- FOUND: main.py (modified, 3 changes applied)
- FOUND: tests/test_main.py (created, 6 tests)
- FOUND commit fd0d908 (RED: test)
- FOUND commit 016242a (GREEN: feat)
- All 64 tests pass
- `grep -c 'from src.scrapers.article import fetch_article_texts' main.py` → 1
- `grep -c 'summarize_items_structured' main.py` → 2 (import + call)
- `grep -c 'fetch_article_texts(all_rss_items)' main.py` → 1
- `grep -c 'section.get("type") == "rss"' main.py` → 1
- `grep -c 'item\["core_idea"\]' main.py` → 1
- `grep -c 'item\["key_points"\]' main.py` → 1
- `grep -c 'item\["ai_summary"\]' main.py` → 1 (else branch only)
