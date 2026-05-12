---
phase: 02-frontend
plan: "02"
subsystem: ui
tags: [html, python, rendering, ai-summary, rss]

requires:
  - phase: 02-01
    provides: CSS classes (.article-core-idea, .article-keypoints, .article-keypoint-chip, .hl-core-idea)

provides:
  - _render_rss_items() emits core_idea quote box (always-visible) and key_points numbered list (inside dropdown)
  - _render_highlights() emits .hl-core-idea paragraph between title and reason
  - Fallback: items with no core_idea and no key_points render as plain links (REND-04 preserved)
  - GitHub/Reddit accordion (_render_accordion) untouched

affects: [02-03, html_renderer]

tech-stack:
  added: []
  patterns: [conditional rendering guard (has_core_idea / has_dropdown), _escape() for all user content]

key-files:
  created: []
  modified: [src/html_renderer.py]

key-decisions:
  - "core_idea placed as sibling after <details> so it is always visible without expanding (D-02)"
  - "key_points rendered as <ul class=article-keypoints> inside dropdown body, chip colored per source"
  - "Non-empty filter applied to key_points list before rendering to skip blank entries"
  - "ai_summary retained as legacy compat comment — no longer drives dropdown body"

patterns-established:
  - "Conditional HTML: f-string with inline ternary guards (has_core_idea, has_dropdown)"
  - "Source color applied to both core_idea border and keypoint chip background"

requirements-completed: [REND-01, REND-02, REND-03, REND-04]

duration: 5min
completed: 2026-05-12
---

# Phase 02: Frontend — Plan 02 Summary

**Extended `_render_rss_items()` and `_render_highlights()` to emit structured AI summary fields (core_idea, key_points) while preserving all existing GitHub/Reddit accordion behavior.**

## Performance

- **Duration:** ~5 min
- **Completed:** 2026-05-12
- **Tasks:** 2/2 (task 3 was docs — rate-limited before SUMMARY commit)
- **Files modified:** 1 (src/html_renderer.py)

## Accomplishments

### Task 1 — Extend `_render_rss_items()`

Added `core_idea` and `key_points` extraction from each RSS item dict. When either field is present, the renderer now produces:

- `<details>` dropdown containing a `<ul class="article-keypoints">` with per-point `<span class="article-keypoint-chip">` chips, colored by source
- `<p class="article-core-idea">` placed as a sibling **after** `<details>` so it is always visible without expanding (REND-01)

Fallback: when both `core_idea` and `key_points` are absent/empty, the existing plain `<a class="article-link">` path fires (REND-04).

### Task 2 — Extend `_render_highlights()`

Extracted `core_idea` from each highlight item and inserted `<p class='hl-core-idea'>` between the title anchor and the existing `.hl-reason` paragraph. Empty `core_idea` produces no output (conditional guard).

## Self-Check: PASSED

- _render_rss_items: core_idea + key_points branch implemented ✓
- _render_highlights: hl-core-idea paragraph injected ✓
- Fallback (no core_idea, no key_points) → plain link ✓
- _render_accordion (GitHub/Reddit) untouched ✓
- _escape() applied to all user content ✓
