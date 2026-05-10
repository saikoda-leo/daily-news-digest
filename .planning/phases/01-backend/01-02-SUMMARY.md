---
phase: 01-backend
plan: "02"
subsystem: summarizer
tags: [summarization, claude-api, tdd, json-safety]
dependency_graph:
  requires: []
  provides: [summarize_items_structured, _safe_structured]
  affects: [src/summarizer.py, tests/test_summarizer.py]
tech_stack:
  added: []
  patterns: [assistant-prefill, json-fallback-normalizer, tdd-red-green]
key_files:
  created: []
  modified:
    - src/summarizer.py
    - tests/test_summarizer.py
decisions:
  - "Used substring presence check (assert 'x'*6000 in prompt) instead of character count for truncation tests — prompt template contains 3 x's and 7 y's that would skew counts"
  - "Assistant prefill '[' forces Claude to return a JSON array, avoiding markdown-fenced or non-array responses"
  - "max_tokens = min(4096, len(items)*120+200) keeps token budget proportional to section size"
metrics:
  duration: "3 minutes"
  completed_date: "2026-05-10"
  tasks_completed: 1
  tasks_total: 1
---

# Phase 01 Plan 02: Structured Summarizer Summary

Added `summarize_items_structured()` and `_safe_structured()` to `src/summarizer.py` with bullet-proof JSON handling, assistant prefill, and 14 new tests covering all edge cases.

## What Was Built

### New functions in `src/summarizer.py`

**`_safe_structured(obj: dict) -> dict`**
Normalizes one Claude-returned object to the canonical shape:
- Clamps `key_points` to exactly 5 (truncates if too many, pads with `""` if too few)
- Wraps string `key_points` in a list (handles Claude misformatting)
- Returns `{"core_idea": "", "key_points": ["","","","",""]}` for any non-dict input

**`summarize_items_structured(section_title: str, items: list) -> list`**
One Claude call per section that returns `[{"core_idea": str, "key_points": [5 strings]}, ...]`:
- Per-item input: `full_text[:6000]` if `full_text` is non-empty and >= 200 chars, else `summary[:1000]`
- Assistant prefill `"["` forces JSON array output without markdown fences
- `max_tokens = min(4096, len(items) * 120 + 200)` — proportional, not hardcoded
- Malformed JSON → returns N empty structured dicts (no exception propagated)
- Length mismatch salvage: present items kept, missing items padded with empty dict
- Stderr warnings for truncated responses and length mismatches (section title only, no raw body)

**Unchanged existing functions:**
- `summarize_section()` — unchanged
- `get_top_highlights()` — unchanged
- `summarize_items()` — unchanged
- `_get_client()`, `_SYSTEM_PROMPT`, `_HIGHLIGHT_SYSTEM_PROMPT` — unchanged

### Tests in `tests/test_summarizer.py`

| Before | After |
|--------|-------|
| 7 tests | 21 tests |

14 new tests added covering:
1. Empty input returns empty list
2. Valid JSON response parsed and returned correctly
3. Assistant prefill `{"role": "assistant", "content": "["}` is the last message
4. Bad JSON falls back to N empty structured dicts
5. Too many key_points clamped to 5
6. Too few key_points padded to 5
7. Length mismatch salvaged (partial + empty padding)
8. `full_text` of 10,000 chars truncated to 6,000 (verified via `"x"*6000 in prompt`)
9. Empty `full_text` falls back to `summary[:1000]`
10. Short `full_text` (< 200 chars) falls back to `summary[:1000]`
11. `max_tokens` formula: 5 items → 800 (`5*120+200`)
12. `max_tokens` cap: 100 items → 4096 (not 12200)
13. One Claude call per section with 5 items
14. String `key_points` wrapped as `[string, "", "", "", ""]`

## TDD Gate Compliance

- RED commit: `a614a47` — `test(01-02): add failing tests for summarize_items_structured` (14 failing)
- GREEN commit: `043c65c` — `feat(01-02): add summarize_items_structured and _safe_structured to summarizer` (21 passing)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed character-counting test assertions**
- **Found during:** GREEN phase (3 tests failing after implementation)
- **Issue:** Tests counted occurrences of "x" and "y" across the entire prompt, but the prompt template itself contains 3 "x" characters (from "exactly" appearing twice, "GPT-5." contains no x — actually from "exactly" x2 and "example") and 7 "y" characters (from "key_points" x5, "exactly" x2 in template). The simple `.count("x") == 6000` assertion gave `6003`.
- **Fix:** Changed to substring presence check: `assert "x" * 6000 in sent_prompt` and `assert "x" * 6001 not in sent_prompt`. This is a more robust test anyway — it verifies the exact 6000-char block is present without caring about template characters.
- **Files modified:** `tests/test_summarizer.py` (lines for tests 8, 9, 10)
- **Commits:** `043c65c`

## Notes for Plan 03

Plan 03 will wire `summarize_items_structured` into `_summarize_one()` in `main.py` or `summarizer.py`:

```python
from src.summarizer import summarize_items_structured

# In the RSS summarization loop:
structured_results = summarize_items_structured(section_title, rss_items)
for item, structured in zip(rss_items, structured_results):
    item["core_idea"] = structured["core_idea"]
    item["key_points"] = structured["key_points"]
```

The import path is: `from src.summarizer import summarize_items_structured`

## Known Stubs

None. Both functions are fully implemented with no placeholder values.

## Threat Surface Scan

No new network endpoints, auth paths, file access patterns, or schema changes introduced. The `summarize_items_structured` function calls the existing Claude API client (same pattern as `summarize_items`). T-01-07 (DoS via oversized input) and T-01-09 (malformed JSON) mitigations from the threat model are both implemented: input capped at 6000/1000 chars, JSON parsing wrapped in try/except with safe fallbacks.

## Self-Check

All files verified:
- `src/summarizer.py` contains `def summarize_items_structured` and `def _safe_structured`
- `tests/test_summarizer.py` has 21 tests, all passing
- `import sys` present at line 3 of summarizer.py
- Commits `a614a47` (RED) and `043c65c` (GREEN) exist in git log
