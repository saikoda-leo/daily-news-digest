# Retrospective

## Milestone: v1.0 — Full-Text Article Breakdown

**Shipped:** 2026-05-12
**Phases:** 2 | **Plans:** 6 | **Timeline:** 3 days (2026-05-09 → 2026-05-12)

### What Was Built

- Concurrent article text fetcher via trafilatura with URL skip patterns, robust encoding handling, and HTML entity stripping in RSS summaries
- Structured Claude summarizer with bullet-proof JSON handling, assistant prefill, and proportional token budget
- Orchestrator wiring that cleanly splits RSS (structured fields) from GitHub/Reddit (plain `ai_summary`)
- Four new CSS classes as purely additive rules, then HTML renderer extensions for always-visible core-idea + expandable key-points
- End-to-end verified visually in Chrome with all REND success criteria passing

### What Worked

- **TDD discipline**: RED → GREEN commits caught two non-obvious bugs (double-unescape in `_strip_html`, character-counting test assertions)
- **Surgical plan scope**: Each plan touched exactly the files it needed; no cross-plan blast radius
- **Assistant prefill `"["`**: Eliminated the need to strip markdown fences from Claude responses — simple and robust
- **`_safe_structured()` normalizer**: Centralizing JSON shape validation in one function made all edge cases (wrong length, string instead of list, non-dict) predictable

### What Was Inefficient

- REQUIREMENTS.md checkboxes were never updated during execution — required cleanup at milestone close
- `lxml_html_clean` transitive dep surfaced at runtime rather than during dependency planning

### Patterns Established

- Split data shape by section type at the orchestrator level — avoids dual-shape items and makes renderer logic simple
- Proportional `max_tokens = min(4096, n*120+200)` for batched Claude calls — scales with section size
- Substring presence test (`"x"*N in prompt`) preferred over character count for truncation assertions

### Key Lessons

- Pre-install and verify transitive Python deps before writing tests that depend on them
- Keep REQUIREMENTS.md traceability updated as each plan completes, not only at milestone close
- Assistant prefill is underused — it reliably forces structured output without post-processing

---

## Cross-Milestone Trends

| Milestone | Phases | Plans | Days | Tests | LOC |
|-----------|--------|-------|------|-------|-----|
| v1.0 | 2 | 6 | 3 | 64 | ~1553 |
