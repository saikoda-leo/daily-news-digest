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

### Active

- [ ] Fetch full article text from each RSS article URL (requests + BeautifulSoup, extract `<p>` text)
- [ ] Fall back to RSS feed summary if fetch fails, returns empty, or content is too short
- [ ] Claude AI produces structured breakdown per article: core idea (1 sentence) + 5 key points
- [ ] Structured breakdown replaces the current 1-2 sentence `ai_summary` for RSS articles
- [ ] HTML dropdown renders "Core idea: [sentence]" followed by a numbered list of 5 points
- [ ] Article fetching parallelized (all RSS articles fetched concurrently before summarization)
- [ ] Feature applies to all RSS articles (not just highlights)

### Out of Scope

- Apply structured breakdown to GitHub/Reddit items — those items link to repos/threads, not articles; structure doesn't fit
- Cache fetched article content between runs — adds persistence complexity; not worth it for a daily digest
- Paywall bypass — legal and technical complexity out of proportion to benefit
- User-configurable number of key points — 5 is the fixed format; no knob needed yet

## Context

- The current `ai_summary` field on each item is a plain string (1-2 sentences). The new structured breakdown will replace this field's content or introduce new fields (`core_idea`, `key_points`) on RSS items.
- `src/summarizer.py` contains `summarize_items()` — the function to extend or replace. It currently makes one Claude API call per section with all items batched.
- `src/html_renderer.py` renders the dropdown in `_render_rss_items()` and `_render_accordion()`. The RSS section uses `_render_rss_items()`.
- Full article fetching adds network latency. With 20-30 RSS articles, parallel fetching via `ThreadPoolExecutor` is essential.
- Claude Haiku is used for all summarization. The structured breakdown prompt must request JSON output: `{"core_idea": "...", "key_points": ["...", "...", "...", "...", "..."]}`.
- Articles may be behind paywalls, return bot-detection pages, or have very little extractable text. The fallback to RSS summary must be robust.

## Constraints

- **Tech stack**: Python 3.9+, `requests` + `BeautifulSoup4` (already in requirements) for fetching/parsing
- **API cost**: Fetching full article text + structured summarization increases Claude API usage; keep calls batched where possible
- **Time budget**: GitHub Actions has a 6-hour job limit; parallel fetching keeps total time reasonable
- **Compatibility**: Must not break existing GitHub/Reddit accordion rendering (they don't use the new structured format)

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Replace `ai_summary` string with structured fields | Clean data model; no legacy format to carry | — Pending |
| Parallel article fetching before summarization | Network I/O dominates; parallelism keeps latency low | — Pending |
| Fall back to RSS text on any fetch failure | Robustness over completeness; a short summary is better than nothing | — Pending |
| Structured prompt returns JSON per article (one call per section) | Keeps API calls batched; avoids N individual Claude calls | — Pending |

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
*Last updated: 2026-05-10 after initialization*
