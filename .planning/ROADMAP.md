# Roadmap: Daily Info Digest — Full-Text Article Breakdown

## Overview

Two phases deliver the full-text structured breakdown feature. Phase 1 wires in article fetching and structured Claude summarization — the backend pipeline that produces `core_idea` and `key_points` per RSS article. Phase 2 updates the HTML renderer to display that structured data in the article dropdowns, completing the user-visible feature.

## Phases

- [x] **Phase 1: Backend** - Fetch full article text and produce structured AI breakdown (core idea + 5 key points) per RSS article
- [x] **Phase 2: Frontend** - Update HTML renderer to show structured breakdown in article dropdowns

## Phase Details

### Phase 1: Backend
**Goal**: Every RSS article has a structured AI breakdown — core idea and 5 key points — computed from full article text before rendering begins
**Depends on**: Nothing (first phase)
**Requirements**: FETCH-01, FETCH-02, FETCH-03, FETCH-04, FETCH-05, SUMM-01, SUMM-02, SUMM-03, SUMM-04
**Success Criteria** (what must be TRUE):
  1. Running `python main.py` completes without error and each RSS item in the output data has `core_idea` (non-empty string) and `key_points` (list of 5 strings) fields
  2. When an article URL is unreachable or returns fewer than 200 characters of text, the digest still completes using the RSS feed summary as fallback — no articles are skipped
  3. All RSS article fetches complete before summarization starts, and total fetch time for 20-30 articles is visibly parallel (not sequential)
  4. A malformed or truncated Claude JSON response does not crash the pipeline — the affected article gets empty structured fields and the rest of the digest renders normally
**Plans**: 3 plans
  - [x] 01-01-PLAN.md — Article fetcher module + RSS HTML stripping (FETCH-01..05)
  - [x] 01-02-PLAN.md — Structured Claude summarizer (SUMM-01..03)
  - [x] 01-03-PLAN.md — Wire fetch + branched summarizer into main.py (SUMM-04, FETCH-05 orchestration)

### Phase 2: Frontend
**Goal**: The HTML digest renders each RSS article's structured breakdown — core idea sentence and numbered key points — inside the existing article dropdown
**Depends on**: Phase 1
**Requirements**: REND-01, REND-02, REND-03, REND-04
**Success Criteria** (what must be TRUE):
  1. Each RSS article row shows the core idea sentence always-visible below the title (outside the dropdown); expanding the dropdown shows a numbered list of 5 key points
  2. The "Read full article" link appears at the bottom of every expanded dropdown, unchanged from the current behavior
  3. An RSS article with empty structured fields (fallback case) renders a plain link without broken layout or missing elements
  4. GitHub and Reddit accordion sections are visually unchanged — they do not show a "Core idea" or key points section
**Plans**: 3 plans
  - [x] 02-01-PLAN.md — Add new CSS rules to style.css (.article-core-idea, .article-keypoints, .article-keypoint-chip, .hl-core-idea) [REND-01, REND-02, REND-04]
  - [x] 02-02-PLAN.md — Extend _render_rss_items() and _render_highlights() in html_renderer.py [REND-01..04]
  - [x] 02-03-PLAN.md — End-to-end run + human-verify checkpoint on real digest [REND-01..04]
**UI hint**: yes

## Progress

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Backend | 3/3 | Complete | 2026-05-10 |
| 2. Frontend | 3/3 | Complete | 2026-05-12 |
</content>
</invoke>