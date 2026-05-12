# Daily Info Digest

## What This Is

A personal daily newspaper that scrapes RSS feeds, GitHub trending repos, and subreddits each morning, summarizes the content with Claude AI, and renders a polished HTML + Markdown digest. It runs automatically via GitHub Actions at 07:00 ICT and opens the result in Chrome on macOS.

## Core Value

Each morning, every RSS article has a structured AI breakdown — core idea plus 5 key points — so the user can scan the most important insights without reading the full article.

## Requirements

### Validated

- ✓ RSS feed scraping from multiple sources via feedparser — existing
- ✓ GitHub trending repo scraping (HTML scrape, no auth) — existing
- ✓ Reddit top post scraping (public JSON API, no auth) — existing
- ✓ Claude AI section-level summaries (2-3 sentences per section) — existing
- ✓ Claude AI per-article 1-2 sentence summaries for all sections — existing
- ✓ Top 5 highlight selection (AI-powered, RSS only) — existing
- ✓ HTML output: newspaper masthead, source-filter tabs, per-article dropdowns — existing
- ✓ Markdown output alongside HTML — existing
- ✓ GitHub Actions daily CI (00:00 UTC = 07:00 ICT), auto-commit output — existing
- ✓ RSS keyword filtering, URL deduplication, XSS-safe URL handling — existing
- ✓ Parallel section summarization via ThreadPoolExecutor — existing
- ✓ Fetch full article text from each RSS article URL via trafilatura (parallel, 10s timeout) — v1.0
- ✓ Fall back to RSS feed summary if fetch fails, returns empty, or content is too short — v1.0
- ✓ Claude AI produces structured breakdown per article: core idea (1 sentence) + 5 key points — v1.0
- ✓ Structured breakdown replaces `ai_summary` for RSS articles (`core_idea` + `key_points` fields) — v1.0
- ✓ HTML always-visible core-idea quote box below title + expandable numbered key-points list — v1.0
- ✓ Article fetching parallelized via ThreadPoolExecutor before summarization — v1.0
- ✓ Feature applies to all RSS articles (not just highlights) — v1.0

### Active

(none — all v1.0 requirements shipped)

### Out of Scope

- Apply structured breakdown to GitHub/Reddit items — those items link to repos/threads, not articles; structure doesn't fit
- Cache fetched article content between runs — adds persistence complexity; not worth it for a daily digest
- Paywall bypass — legal and technical complexity out of proportion to benefit
- User-configurable number of key points — 5 is the fixed format; no knob needed yet

## Context

**Shipped v1.0 on 2026-05-12.** ~1553 LOC Python, 64 tests, 22 files changed.

Tech stack: Python 3.9, feedparser, trafilatura 2.0.0, requests, BeautifulSoup4, anthropic SDK, PyYAML.

- RSS items now carry `core_idea` (str) + `key_points` (list[str, 5]) instead of `ai_summary`.
- GitHub/Reddit items retain `ai_summary`; their accordions are unchanged.
- `src/scrapers/article.py` fetches full article text concurrently (ThreadPoolExecutor, 10 workers, 10s timeout); skips PDFs, YouTube, GitHub URLs.
- `summarize_items_structured()` in `src/summarizer.py` sends one batched Claude call per RSS section with assistant prefill `"["` to force JSON array output.
- `_render_rss_items()` and `_render_highlights()` in `src/html_renderer.py` emit `.article-core-idea` quote box (always-visible) and `.article-keypoints` expandable list.
- Fallback path (paywall/empty fetch) degrades to plain link with no broken layout.
- 64 tests pass; no regressions in existing GitHub/Reddit rendering.

## Constraints

- **Tech stack**: Python 3.9+, `requests` + `BeautifulSoup4` (already in requirements) for fetching/parsing
- **API cost**: Fetching full article text + structured summarization increases Claude API usage; keep calls batched where possible
- **Time budget**: GitHub Actions has a 6-hour job limit; parallel fetching keeps total time reasonable
- **Compatibility**: Must not break existing GitHub/Reddit accordion rendering (they don't use the new structured format)

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Replace `ai_summary` string with structured fields | Clean data model; no legacy format to carry | ✓ Good — clean split confirmed; RSS items never carry `ai_summary` |
| Parallel article fetching before summarization | Network I/O dominates; parallelism keeps latency low | ✓ Good — ThreadPoolExecutor(10 workers) delivers all fetches before summarization |
| Fall back to RSS text on any fetch failure | Robustness over completeness; a short summary is better than nothing | ✓ Good — fallback path tested; pipeline never crashes on bad URLs |
| Structured prompt returns JSON per article (one call per section) | Keeps API calls batched; avoids N individual Claude calls | ✓ Good — assistant prefill `"["` eliminates markdown fences; malformed JSON handled |
| Use trafilatura instead of BeautifulSoup for extraction | Higher extraction quality; handles edge cases (encoding, tables, comments) | ✓ Good — lxml_html_clean transitive dep required for v2.0.0 |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-05-12 after v1.0 milestone — Full-Text Article Breakdown shipped. All 13 v1 requirements delivered and validated.*
