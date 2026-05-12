# Milestones

## v1.0 — Full-Text Article Breakdown

**Status:** ✅ SHIPPED 2026-05-12
**Phases:** 1–2
**Plans:** 6
**Timeline:** 2026-05-09 → 2026-05-12 (3 days)
**Stats:** 22 files changed (+2737 / -35), ~1553 Python LOC, 64 tests

### Delivered

Every RSS article in the daily digest now shows a structured AI breakdown — a prominent core-idea quote always visible below the title, plus 5 numbered key points inside the expandable dropdown. The pipeline fetches full article text in parallel before summarization, falls back to RSS feed text when fetch fails, and the HTML renderer handles both structured and legacy plain-link paths without breaking GitHub/Reddit accordions.

### Key Accomplishments

1. Concurrent article text fetcher (`src/scrapers/article.py`) via trafilatura with URL skip patterns, robust encoding handling, and HTML entity stripping in RSS summaries
2. Structured Claude summarizer (`summarize_items_structured` + `_safe_structured`) with bullet-proof JSON handling, assistant prefill `"["`, proportional token budget, and 14 edge-case tests
3. Orchestrator wiring (`main.py`): `fetch_article_texts` + branched `_summarize_one` delivers `core_idea`/`key_points` to all RSS items and preserves `ai_summary` for GitHub/Reddit
4. Four new CSS classes (`.article-core-idea`, `.article-keypoints`, `.article-keypoint-chip`, `.hl-core-idea`) added as purely additive rules in `src/templates/style.css`
5. HTML renderer (`_render_rss_items`, `_render_highlights`) extended to emit always-visible core-idea quote box and expandable numbered key-points list; fallback plain-link path preserved
6. End-to-end visual verification approved — all 4 REND criteria passed in Google Chrome, GitHub/Reddit accordions visually unchanged

### Known Gaps

None — all 13 v1 requirements delivered (requirement checkboxes were not updated during execution; delivery confirmed by phase summaries and live user verification).

---

*See `.planning/milestones/v1.0-ROADMAP.md` for full phase archive.*
*See `.planning/milestones/v1.0-REQUIREMENTS.md` for requirements archive.*
