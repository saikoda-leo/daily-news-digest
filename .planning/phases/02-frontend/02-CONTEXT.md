# Phase 2: Frontend - Context

**Gathered:** 2026-05-12
**Status:** Ready for planning

<domain>
## Phase Boundary

Update `src/html_renderer.py` and `src/templates/style.css` so each RSS article shows its `core_idea` always-visible below the title, and its `key_points` (numbered 1–5) inside the expanded `<details>` dropdown. Top-5 highlight cards also surface `core_idea` alongside the existing `reason`. GitHub/Reddit accordion paths stay visually unchanged. The markdown renderer (`src/renderer.py`) is out of scope for this phase.

</domain>

<decisions>
## Implementation Decisions

### Core idea visual style (article rows)
- **D-01:** Core idea renders as a short bordered quote box (style analogous to the existing `.acc-summary-box`) with a left accent bar tinted by the article's source color. Inner text is italic, muted serif.
- **D-02:** Core idea sits below the article title, full width, outside the `<details>` element — the title row stays compact and the core idea wraps full width below it (newspaper-deck pattern).
- **D-03:** The `<details>` `<summary>` keeps the same content it has today (title + chevron icon). No "Show 5 key points" label added.
- **D-04:** When both `core_idea` and `key_points` are empty (Phase 1 fallback case), render the article title as a plain link — no chevron, no `<details>` wrapper, no expandable area. Matches REND-04.

### Key points list styling (inside dropdown)
- **D-05:** Render the 5 key points as a vertical list where each row has a small colored circular numbered chip (1–5) styled like the existing `.acc-index` chip — chip background uses the article's source color.
- **D-06:** Density is compact: ~6–8 px vertical padding per row, line-height ~1.4, font size around 0.83–0.85 rem (consistent with existing dropdown text).
- **D-07:** Skip empty slots. If Claude returned partial fills (e.g., 3 of 5 strings non-empty), render only the non-empty entries and renumber to match what's shown.
- **D-08:** "Read full article ↗" sits below the key points list, left-aligned, styled like the current `.article-read-more` (source-colored, small font). Satisfies REND-03.

### Highlights cards content
- **D-09:** Highlight cards now show BOTH `core_idea` and the existing `reason`. Order inside each card: `[Source chip] → Article title → core_idea → reason quote box`.
- **D-10:** Inside the highlight card, `core_idea` is rendered as a plain serif paragraph (no border, no quote box). This visually differentiates it from the bordered `reason` line directly below.
- **D-11:** When a highlighted article has an empty `core_idea` (fallback), omit the core idea line entirely — the card falls back to today's appearance (title + reason quote box).

### Markdown renderer (scope clarification)
- **D-12:** `src/renderer.py` is **not** updated in this phase. The markdown file is a simpler fallback and the phase goal explicitly targets the HTML renderer. The markdown renderer can continue to ignore `core_idea` / `key_points` for RSS items.

### Claude's Discretion
- Whether to introduce new CSS classes (e.g., `.article-core-idea`, `.article-keypoints`, `.article-keypoint-chip`) or extend existing classes — leave that to the planner. Pattern: new module-level CSS strings inside `src/templates/style.css`, following existing `_UPPER_SNAKE` and accent-color conventions.
- Whether to extract a `_render_core_idea(item, color)` and `_render_key_points(item, color)` helper or keep the markup inline inside `_render_rss_items()` — Karpathy/simplicity-first: only extract if the same markup is reused in `_render_highlights` AND `_render_rss_items`, otherwise keep inline.
- Exact emoji/glyph for the numbered chip (e.g., `1` rendered inside a styled `<span>` vs unicode `➊…➎`) — leave to planner; either is fine as long as the chip background uses the source color.
- The "left accent bar tinted by source color" implementation may reuse the source palette already computed by `_source_color(source, source_list)` in `html_renderer.py:100`.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase-defining docs (in this repo)
- `.planning/REQUIREMENTS.md` §HTML Rendering — REND-01..REND-04 (locked requirements)
- `.planning/ROADMAP.md` §Phase 2 Frontend — success criteria 1–4
- `.planning/PROJECT.md` — Core value statement; "compatibility: must not break GitHub/Reddit accordion rendering" constraint

### Code that must be modified
- `src/html_renderer.py` — `_render_rss_items()` (line 144) is the primary surface for the core-idea + key-points changes; `_render_highlights()` (line 108) is the surface for the highlight-card change.
- `src/templates/style.css` — add new CSS rules for `.article-core-idea`, `.article-keypoints`, and the numbered chip. Reuse existing patterns: `.acc-summary-box` (lines 251–256) for the quote-box look, `.acc-index` (lines 264–268) for the numbered chip style, `.article-read-more` (lines 298–303) for the Read-link styling.

### Code that must NOT be modified
- `src/html_renderer.py` — `_render_accordion()` (line 184) handles GitHub/Reddit and must remain visually unchanged.
- `src/renderer.py` — markdown renderer; out of scope per D-12.
- `src/summarizer.py`, `src/scrapers/article.py`, `main.py` — Phase 1 backend; data shape is frozen.

### Codebase maps consulted
- `.planning/codebase/CONVENTIONS.md` §HTML Output — `_CSS`/`_JS` are module-level string constants loaded from `src/templates/`; user content always escaped via `_escape()`; section type drives color via `_SECTION_COLORS`; source colors come from `_SOURCE_PALETTE` (cycled by insertion order).
- `.planning/codebase/STRUCTURE.md` — `html_renderer.py` is the visual source of truth; markdown renderer is the simpler fallback.
- `.planning/codebase/STACK.md` — no frontend framework, no templating library; all HTML built via f-strings.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `_escape(t: str) -> str` (`html_renderer.py:22`) — every dynamic string (core_idea, key_points entries) must go through this before being inlined into the template. Phase 1 stores them as plain Python strings; no pre-escaping happened upstream.
- `_safe_url(url)` (`html_renderer.py:26`) — already used for the "Read full article" link, keep using it.
- `_source_color(source, source_list)` (`html_renderer.py:100`) — returns the article-source color from `_SOURCE_PALETTE` (cycles by insertion order). Use this for the core-idea accent bar and the key-point numbered chips so both colors stay consistent with the source chip already shown above.
- `.acc-summary-box` CSS (`style.css:251`) — left-border italic quote-box look; copy/adapt for the new `.article-core-idea`.
- `.acc-index` CSS (`style.css:264`) — circular numbered chip used in GitHub/Reddit accordion items; copy/adapt for the new key-point chips.
- `.article-read-more` CSS (`style.css:298`) — small source-colored "Read full article ↗" link; keep using as-is for the new dropdown body.

### Established Patterns
- All CSS lives in `src/templates/style.css` (loaded once at import via `_CSS = (_TEMPLATES_DIR / "style.css").read_text()`); add new rules there — never inject styles inline in the HTML template (except for source-color tints via `style=""`, which is the project's existing convention for color cycling).
- HTML is assembled via Python f-strings inside `_render_*` helpers and concatenated. No templating library. New helpers (if introduced) follow `_snake_case` private-helper naming.
- Section-type color mapping (`_SECTION_COLORS`) is RSS-specific gradient — not relevant for the per-article work, but stays untouched. The per-article accent color always comes from `_source_color()`, not `_SECTION_COLORS`.
- Phase 1 stores `core_idea: str` and `key_points: list[str]` (always length 5, padded with empty strings on parse failures per `src/summarizer.py:122`). The renderer must defensively treat `key_points` as possibly-missing (legacy items) or partially-empty (fallback case) and follow D-07.

### Integration Points
- `_render_rss_items(items, highlight_indices, source_list)` (`html_renderer.py:144`) — extend the `if ai_summary:` branch (which renders the dropdown today) into a `if core_idea or any(key_points):` branch that produces the new structure. The `elif url != "#"` (plain link) branch stays the same and now also handles D-04 (empty structured fields).
- `_render_highlights(items, highlights, source_list)` (`html_renderer.py:108`) — after the existing `hl-title` line, conditionally insert a `<p class="hl-core-idea">…</p>` (or similar) when the highlighted item's `core_idea` is non-empty; the existing `hl-reason` block stays.
- Template format string `_HTML_TEMPLATE` (`html_renderer.py:41`) — no structural change needed; only the contents of `{rss_items_html}` and `{highlights_html}` are affected.

</code_context>

<specifics>
## Specific Ideas

- The new article-row visual should read like a newspaper article preview: source chip + ★ Highlight tag on the top row, title (the headline) on its own row, core idea (the deck/sub-headline) as a quoted box below, then expandable key-points as the body.
- Highlight cards should answer two questions at a glance: "What is this story?" (core_idea) and "Why was it picked?" (reason). Keeping them visually distinct (plain paragraph vs bordered quote) makes that contrast obvious.
- Numbered chip should use the same source color that already tints the source chip on the row above — color consistency tells the user "this whole block is from <source>".
- The compact list density is deliberate: 5 short key points × ~30–40 chars each should fit in roughly 5 lines, so users can scan all 5 without scrolling inside the dropdown.

</specifics>

<deferred>
## Deferred Ideas

- Markdown renderer (`src/renderer.py`) update to surface `core_idea` + `key_points` — deferred. Not in Phase 2 scope; track for a future polish phase if the markdown output ever becomes a primary surface.
- Highlight-card numbered key points (expand affordance on cards) — out of scope. Highlights are intentionally a digest preview, not a full reader surface.
- Animation/transition tuning for the new core-idea quote box on first paint — defer to a polish pass; the existing `slideDown` keyframe used elsewhere is sufficient.
- Per-source accent palette refresh — orthogonal; today's `_SOURCE_PALETTE` continues to drive color.

</deferred>

---

*Phase: 2-Frontend*
*Context gathered: 2026-05-12*
