# Phase 2: Frontend - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-05-12
**Phase:** 02-frontend
**Areas discussed:** Core idea visual style, Key points list styling, Highlights cards content

---

## Core idea visual style

### Q1. How should the core idea sentence be styled in the always-visible position below each article title?

| Option | Description | Selected |
|--------|-------------|----------|
| Quoted box with accent | Short bordered box like the existing `.acc-summary-box`, with a left accent bar tinted by source color. Visually distinct from the title, scannable. | ✓ |
| Plain italic line | One italic, muted-gray serif line directly below the title — no border, no label, no box. | |
| Labeled 'Core idea:' line | Prefix the sentence with a bold 'Core idea:' label, then the sentence in regular weight. | |

**User's choice:** Quoted box with accent.

### Q2. Should the dropdown summary text (the clickable line) change with the new core idea above?

| Option | Description | Selected |
|--------|-------------|----------|
| Keep title only | Title remains the disclosure. Core idea is the new content below the title. | ✓ |
| Add 'Show 5 key points' label | Replace the bare chevron with a small label. | |
| Move chevron below core idea | Title stays clean on its own row; toggle row below core idea. | |

**User's choice:** Keep title only.

### Q3. Where should the core idea sit relative to the [Source] chip, '★ Highlight' tag, and article title?

| Option | Description | Selected |
|--------|-------------|----------|
| Below title, full-width | Title row stays compact; core idea wraps full width below it. Newspaper deck pattern. | ✓ |
| Below the meta-top row only | Source chip + highlight tag on first row, title + core idea both indented. | |
| Inline next to title (wrap) | Core idea flows directly after the title as muted text. Most compact. | |

**User's choice:** Below title, full-width.

### Q4. When the core idea is empty (fallback case) but the article has a valid URL, what should the row look like?

| Option | Description | Selected |
|--------|-------------|----------|
| Plain link, no dropdown | No chevron, no expandable area. Matches REND-04. | ✓ |
| Dropdown stays, only 'Read full article' | Keep the chevron + expandable area, only the read link inside. | |
| Plain link + show RSS feed summary | Render the RSS feed summary like the old `ai_summary` dropdown. | |

**User's choice:** Plain link, no dropdown.

---

## Key points list styling

### Q1. How should the 5 key points be visually rendered inside the expanded dropdown?

| Option | Description | Selected |
|--------|-------------|----------|
| Colored numbered chips | Small circular badges with source-color background showing 1–5, then point text. Like `.acc-index`. | ✓ |
| Native `<ol>` numbered list | Plain semantic HTML ordered list with default browser-style numbers. | |
| Card rows | Each point in its own padded row with subtle bottom border. | |

**User's choice:** Colored numbered chips.

### Q2. How dense should the key points list be?

| Option | Description | Selected |
|--------|-------------|----------|
| Comfortable | ~10–12px padding per row, line-height ~1.55, 0.85rem font. | |
| Compact | Tighter 6–8px padding per row, line-height ~1.4. Fits all 5 points in less screen height. | ✓ |
| Spacious | 14–16px padding, line-height ~1.7. Magazine-like. | |

**User's choice:** Compact.

### Q3. How should the renderer handle partial empties (e.g., 3 of 5 key points present)?

| Option | Description | Selected |
|--------|-------------|----------|
| Skip empties, show only non-empty | Render only points with text. Renumbering matches what's shown. | ✓ |
| Show all 5 slots, blank rows visible | Always render 5 numbered slots; empty ones show as a blank line. | |
| If any are empty, fall back to plain link | Treat partial-empty as the full fallback case. | |

**User's choice:** Skip empties, show only non-empty.

### Q4. Where does the 'Read full article ↗' link sit relative to the key points list?

| Option | Description | Selected |
|--------|-------------|----------|
| Below points, left-aligned | Plain link styled like today's `.article-read-more`. Familiar pattern. | ✓ |
| Below points, right-aligned | Same link but pushed to the right edge. | |
| Styled as a CTA button | Small filled or outlined button at the bottom. Stronger affordance. | |

**User's choice:** Below points, left-aligned.

---

## Highlights cards content

### Q1. Should the Top-5 highlight cards be updated to show the new `core_idea`, or stay as-is showing the AI-picked `reason`?

| Option | Description | Selected |
|--------|-------------|----------|
| Keep current 'reason' only | Highlights stay unchanged. Phase 2 scope stays tight to article list. | |
| Show core_idea + reason | Add the core idea sentence to each highlight card alongside the reason. | ✓ |
| Replace reason with core_idea | Highlights show title + core_idea only (no separate reason). | |

**User's choice:** Show core_idea + reason.

### Q2. Within a highlight card, where should core_idea sit relative to the title and the reason quote box?

| Option | Description | Selected |
|--------|-------------|----------|
| Title → core_idea → reason | Core idea acts as sub-headline under title; reason quote box below. | ✓ |
| Title → reason → core_idea | Reason directly under title (today's position); core_idea below. | |
| Title → core_idea only, reason on hover | core_idea in card by default; reason on hover/tooltip. | |

**User's choice:** Title → core_idea → reason.

### Q3. Visually, how should core_idea look inside the highlight card?

| Option | Description | Selected |
|--------|-------------|----------|
| Plain serif paragraph | Short serif paragraph below the title — no border, no quote box. | ✓ |
| Italic muted line | Italic, muted-gray sub-headline like a newspaper deck. | |
| Bordered box (same as article rows) | Same accent-bordered quote box treatment as article rows. | |

**User's choice:** Plain serif paragraph.

### Q4. If a highlighted article has an empty core_idea (fallback case), what should the card show?

| Option | Description | Selected |
|--------|-------------|----------|
| Skip core_idea, keep reason | Omit the line; card still renders title + reason quote box. | ✓ |
| Show RSS feed summary instead | Fall back to RSS feed `summary` in place of the missing core_idea. | |
| Show '—' placeholder | Keep the slot but show an em-dash so layout is identical across cards. | |

**User's choice:** Skip core_idea, keep reason.

---

## Claude's Discretion

- Whether to introduce new CSS classes (e.g., `.article-core-idea`, `.article-keypoints`) or extend existing ones — planner's call.
- Whether to extract `_render_core_idea` / `_render_key_points` helpers or keep markup inline — only extract if reused in both `_render_rss_items` and `_render_highlights`.
- Exact glyph for numbered chip (styled span with digit vs unicode `➊…➎`).
- Reuse of `_source_color()` for the accent bar and chip background is left to the planner.

## Deferred Ideas

- Markdown renderer (`src/renderer.py`) update to surface `core_idea` + `key_points` — out of scope for Phase 2.
- Expand-affordance for key points on highlight cards — out of scope; highlights are intentionally a preview.
- Animation/transition tuning for the new core-idea quote box — defer to a polish pass.
- Per-source accent palette refresh — orthogonal.
