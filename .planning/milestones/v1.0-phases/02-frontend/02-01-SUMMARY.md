---
phase: 02-frontend
plan: "01"
subsystem: frontend/css
tags: [css, styling, rss, highlights, accordion]
dependency_graph:
  requires: []
  provides: [02-02]
  affects: [src/templates/style.css]
tech_stack:
  added: []
  patterns: [bordered-quote-box, circular-chip, compact-list]
key_files:
  created: []
  modified:
    - src/templates/style.css
decisions:
  - "Appended new CSS rules after .article-read-more block to keep per-article rules grouped"
  - "Copied .acc-summary-box pattern verbatim for .article-core-idea (same bordered italic quote-box)"
  - "Copied .acc-index pattern verbatim for .article-keypoint-chip (same circular chip)"
  - ".hl-core-idea intentionally has no border/italic to differentiate from .hl-reason (D-10)"
metrics:
  duration: "1 minute"
  completed: "2026-05-12"
  tasks_completed: 1
  tasks_total: 1
---

# Phase 2 Plan 1: CSS Rules for Article Core Idea and Key Points Summary

## One-liner

Four new CSS classes — `.article-core-idea`, `.article-keypoints`, `.article-keypoint-chip`, `.hl-core-idea` — appended to `style.css` as purely additive rules, providing the visual foundation for Phase 2's HTML renderer changes.

## What Was Built

Added 4 CSS rule blocks to `src/templates/style.css` to support the structured per-article breakdown (core idea + 5 key points) introduced in Phase 1. This plan is a pure CSS addition — no Python was modified.

**New classes:**
- `.article-core-idea`: italic, muted-serif bordered quote box with left accent bar (D-01). Color injected inline by Python `style="border-color:{color}"`.
- `.article-keypoints`: unstyled `<ul>` wrapper for the key-points list.
- `.article-keypoints > li`: flex row with 7px vertical padding, `0.84rem` font size, light bottom border, `:last-child` no-border rule (D-06 compact density).
- `.article-keypoint-chip`: circular 20x20 chip, white text, `border-radius: 50%`, inline color injected by Python `style="background:{color}"` (D-05).
- `.hl-core-idea`: plain serif paragraph, no border, no italic (D-10) — visually contrasts with the bordered `.hl-reason` directly below it in highlight cards.

## Tasks

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Add four new CSS rules to style.css | 8a137e8 | src/templates/style.css |

## Verification Results

All acceptance criteria passed:
- `.article-core-idea {` — 1 occurrence
- `.article-keypoints {` — 1 occurrence
- `.article-keypoints > li {` — 1 occurrence
- `.article-keypoints > li:last-child` — 1 occurrence
- `.article-keypoint-chip {` — 1 occurrence
- `.hl-core-idea {` — 1 occurrence
- `border-radius: 50%` count — 3 (`.hl-rank`, `.acc-index`, `.article-keypoint-chip`)
- `font-style: italic` count — 4 (`.masthead-sub`, `.acc-summary-box`, `.hl-reason`, `.article-core-idea`); `.hl-core-idea` correctly adds NO fifth italic
- Git diff: 0 lines removed (purely additive)
- `python -c "from src.html_renderer import _CSS; assert '.article-core-idea' in _CSS ..."` — OK
- All accordion classes (`.acc-summary-box`, `.acc-index`, `.acc-item`, `.acc-link`, `.acc-details`, `.acc-ai-summary`, `.acc-read-more`) unchanged

## Deviations from Plan

None — plan executed exactly as written.

## Known Stubs

None. This plan adds CSS only; no data wiring or UI rendering is involved.

## Threat Flags

None. This plan modifies only a static CSS file with no network endpoints, auth paths, or dynamic data handling.

## Self-Check: PASSED

- [x] `src/templates/style.css` modified with 39 insertions, 0 deletions
- [x] Commit `8a137e8` exists: `feat(02-01): add CSS rules for article-core-idea, keypoints, hl-core-idea`
- [x] All 6 new CSS class selectors present and verified via grep
- [x] Python import test passes
- [x] No unexpected file deletions
