# Requirements: Daily Info Digest — Full-Text Article Breakdown

**Defined:** 2026-05-10
**Core Value:** Each morning, every RSS article has a structured AI breakdown — core idea plus 5 key points — so the user can scan the most important insights without reading the full article.

## v1 Requirements

### Article Fetching

- [ ] **FETCH-01**: System fetches full HTML of each RSS article URL using `requests` with a 10-second timeout
- [ ] **FETCH-02**: System extracts clean article body text from HTML using `trafilatura`
- [ ] **FETCH-03**: System falls back to RSS feed summary text if fetch fails, times out, or extracted text is fewer than 200 characters
- [ ] **FETCH-04**: Extracted article text is truncated to 6000 characters before being sent to Claude
- [ ] **FETCH-05**: All RSS article fetches run concurrently via `ThreadPoolExecutor` before summarization begins

### Structured Summarization

- [ ] **SUMM-01**: Claude produces a structured JSON object per article: `{"core_idea": "...", "key_points": ["...", "...", "...", "...", "..."]}`
- [ ] **SUMM-02**: Claude calls are batched per section (one call per RSS section, not one call per article) to minimize API usage
- [ ] **SUMM-03**: If Claude returns malformed JSON or a `key_points` list with the wrong length, system falls back to empty structured summary (no crash)
- [ ] **SUMM-04**: Existing 1-2 sentence `ai_summary` string field on RSS items is replaced by `core_idea` (str) and `key_points` (list[str]) fields

### HTML Rendering

- [ ] **REND-01**: Article dropdown in HTML shows "Core idea:" label followed by the core idea sentence
- [ ] **REND-02**: Article dropdown shows a numbered list (1–5) of key points below the core idea
- [ ] **REND-03**: "Read full article" link appears at the bottom of the dropdown (unchanged behavior)
- [ ] **REND-04**: If an article has no structured summary (fallback case), dropdown degrades gracefully to a plain link (no broken layout)

## v2 Requirements

### Enhanced Extraction

- **FETCH-V2-01**: Detect and skip non-article URLs (PDF, podcast, video) before attempting fetch
- **FETCH-V2-02**: Configurable per-feed fetch toggle in `feeds.yaml` (enable/disable full-text fetch per source)
- **FETCH-V2-03**: Article text cached locally between runs to avoid re-fetching the same URL on the same day

### Enhanced Summarization

- **SUMM-V2-01**: Configurable number of key points (default 5) via `feeds.yaml`
- **SUMM-V2-02**: Confidence/quality score shown per summary (low confidence when fell back to RSS text)

## Out of Scope

| Feature | Reason |
|---------|--------|
| Apply structured breakdown to GitHub/Reddit items | Those link to repos and threads, not articles; the format doesn't fit |
| Paywall bypass (cookie injection, archiver services) | Legal and technical complexity out of proportion to benefit |
| Headless browser for JS-rendered pages | Adds 150-300 MB binary deps to GitHub Actions for marginal gain; trafilatura + fallback is sufficient |
| Separate Claude call per article | Too expensive; batch-per-section approach keeps costs proportional |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| FETCH-01 | Phase 1 | Pending |
| FETCH-02 | Phase 1 | Pending |
| FETCH-03 | Phase 1 | Pending |
| FETCH-04 | Phase 1 | Pending |
| FETCH-05 | Phase 1 | Pending |
| SUMM-01 | Phase 1 | Pending |
| SUMM-02 | Phase 1 | Pending |
| SUMM-03 | Phase 1 | Pending |
| SUMM-04 | Phase 1 | Pending |
| REND-01 | Phase 2 | Pending |
| REND-02 | Phase 2 | Pending |
| REND-03 | Phase 2 | Pending |
| REND-04 | Phase 2 | Pending |

**Coverage:**
- v1 requirements: 13 total
- Mapped to phases: 13
- Unmapped: 0 ✓

---
*Requirements defined: 2026-05-10*
*Last updated: 2026-05-10 after initial definition*
