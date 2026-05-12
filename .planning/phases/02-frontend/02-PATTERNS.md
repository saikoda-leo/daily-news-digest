# Phase 2: Frontend - Pattern Map

**Mapped:** 2026-05-12
**Files analyzed:** 2 (modified)
**Analogs found:** 2 / 2 (all in-file analogs)

## File Classification

| Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---------------|------|-----------|----------------|---------------|
| `src/html_renderer.py` (`_render_rss_items`, `_render_highlights`) | renderer (HTML view layer) | transform (dict → HTML string via f-string) | self — `_render_accordion()` (line 184) and existing `if ai_summary:` branch in same file (line 156) | exact (same module, same renderer pattern) |
| `src/templates/style.css` (new rules) | stylesheet | static asset (loaded once at import, embedded in HTML) | self — `.acc-summary-box` (line 251), `.acc-index` (line 264), `.article-read-more` (line 298), `.hl-reason` (line 135) | exact (same file, same convention) |

## Pattern Assignments

### `src/html_renderer.py` — `_render_rss_items()` extension (renderer, transform)

**Analog 1:** existing `if ai_summary:` branch in same function (`html_renderer.py:156-164`).
This is the closest analog because it is the exact branch being replaced/extended into `if core_idea or any(key_points):`.

**Existing code to copy/extend** (`html_renderer.py:156-164`):
```python
if ai_summary:
    read_more = (
        f'<a class="article-read-more" href="{_escape(url)}" target="_blank" rel="noopener">Read full article &#8599;</a>'
        if url != "#" else ""
    )
    content = f"""<details class="article-details">
      <summary><span class="article-title-text">{title}</span><i class="article-toggle-icon">&#9660;</i></summary>
      <div class="article-ai-summary" style="border-color:{color}">{_escape(ai_summary)}{read_more}</div>
    </details>"""
```

**Patterns to copy:**
- `<details class="article-details">` + `<summary>` + `<i class="article-toggle-icon">` chevron — keep exactly this structure (D-03: summary content unchanged).
- `style="border-color:{color}"` for source-color tinting on the inner box (D-01: same pattern for `.article-core-idea` accent bar).
- `_escape()` on every dynamic string before f-string interpolation (`title`, `ai_summary`).
- `_safe_url(url)` already computed at top; reuse for "Read full article" link (D-08).
- `read_more` ternary on `url != "#"` — preserve so empty URLs don't render a broken link.

**Analog 2 — fallback branch** (`html_renderer.py:165-168`):
```python
elif url != "#":
    content = f'<a class="article-link" href="{_escape(url)}" target="_blank" rel="noopener">{title}</a>'
else:
    content = f'<span class="article-link">{title}</span>'
```

**Pattern to copy:** This branch is the D-04 fallback (no `core_idea` AND no `key_points`). Keep verbatim — only the guarding condition above it changes from `if ai_summary:` to `if core_idea or any(key_points):`.

**Analog 3 — outer row layout** (`html_renderer.py:170-180`):
```python
out += f"""
    <li class="article-item{hl_class}" data-source="{_escape(source)}">
      <span class="article-num">{i + 1}</span>
      <div class="article-content">
        <div class="article-meta-top">
          <span class="source-chip" style="background:{color}">{_escape(source)}</span>
          {hl_tag}
        </div>
        {content}
      </div>
    </li>"""
```

**Pattern to copy:** Outer `<li class="article-item">` row stays untouched. Per D-02, the new `core_idea` quote box renders **outside** `<details>` but **inside** `<div class="article-content">`, below `{content}` (or absorbed into the content block via the new branch). Newspaper-deck pattern: title (inside `<summary>`) then full-width core idea below it.

---

### `src/html_renderer.py` — key-points list inside `<details>` (renderer, transform)

**Analog:** items list inside `_render_accordion()` (`html_renderer.py:225-229`).

**Existing code** (`html_renderer.py:225-229`):
```python
items_html += f"""
      <li class="acc-item">
        <div class="acc-index" style="background:{accent}">{i}</div>
        <div style="flex:1">{inner}</div>
      </li>"""
```

**Patterns to copy:**
- Numbered chip pattern: `<div class="acc-index" style="background:{accent}">{i}</div>` is exactly the chip required by D-05. New class (`.article-keypoint-chip` or similar) reuses the same `style="background:{color}"` inline-color pattern.
- The chip color comes from `_source_color(source, source_list)` (already computed as `color` at line 148) — NOT from `_SECTION_COLORS` (which is the gradient/accent for the accordion header only).
- Numbering is via Python `enumerate(..., 1)` — for D-07 "skip empty slots and renumber", iterate the filtered (non-empty) `key_points` list with `enumerate(..., 1)`.

**Implementation guidance for D-07:**
```python
non_empty = [kp for kp in (key_points or []) if kp and kp.strip()]
for n, kp in enumerate(non_empty, 1):
    # render row with chip number n
```

---

### `src/html_renderer.py` — `_render_highlights()` extension (renderer, transform)

**Analog:** existing `_render_highlights()` body (`html_renderer.py:118-133`).

**Existing code** (`html_renderer.py:124-133`):
```python
out += f"""
  <div class="{card_class}">
    <div class="hl-accent-bar" style="background:{color}"></div>
    <div class="hl-rank">{rank}</div>
    <div class="hl-body">
      <span class="hl-source-badge" style="background:{color}">{_escape(source)}</span>
      <a class="hl-title" href="{_escape(url)}" target="_blank" rel="noopener">{title}</a>
      {"<p class='hl-reason' style='border-color:" + color + "'>" + _escape(reason) + "</p>" if reason else ""}
    </div>
  </div>"""
```

**Patterns to copy:**
- Conditional inline-render pattern: `{"<p class='...'>" + ... + "</p>" if reason else ""}` — reuse this exact pattern for the new `core_idea` line per D-09 + D-11 (omit when empty).
- Insertion point: directly after `<a class="hl-title">…</a>` and before the `hl-reason` block (D-09 ordering: source chip → title → core_idea → reason).
- Per D-10, `core_idea` is a plain `<p>` (no border, no quote box). Use a NEW class (e.g., `.hl-core-idea`) — do NOT reuse `.hl-reason` (which is bordered/italic).

**Suggested insertion:**
```python
core_idea = item.get("core_idea", "")
# ...inside the f-string, between hl-title and hl-reason:
{"<p class='hl-core-idea'>" + _escape(core_idea) + "</p>" if core_idea else ""}
```

---

### `src/templates/style.css` — new CSS rules (stylesheet, static asset)

**Analog 1 for `.article-core-idea`:** `.acc-summary-box` (`style.css:251-256`).
```css
.acc-summary-box {
  font-size: .85rem; line-height: 1.7; color: var(--sub);
  font-style: italic; background: #f7f9fc;
  border-left: 3px solid; border-radius: 0 8px 8px 0;
  padding: 9px 14px; margin-bottom: 14px;
}
```
**Pattern to copy:** Italic muted-serif text, light bg, `border-left: 3px solid` (color injected inline via `style="border-color:{color}"` in Python). This is the bordered-quote-box look D-01 calls for. Adapt margins for the article-row context (likely `margin: 8px 0` instead of `margin-bottom: 14px`).

**Analog 2 for `.article-keypoint-chip`:** `.acc-index` (`style.css:264-268`).
```css
.acc-index {
  font-size: .68rem; font-weight: 700; min-width: 20px; height: 20px;
  border-radius: 50%; display: flex; align-items: center; justify-content: center;
  color: #fff; flex-shrink: 0; margin-top: 2px;
}
```
**Pattern to copy:** Circular chip via `border-radius: 50%`, fixed 20×20, white text, `flex-shrink: 0`. Background color injected inline via `style="background:{color}"`.

**Analog 3 for `.article-keypoints` list rows:** `.acc-item` (`style.css:258-263`).
```css
.acc-item {
  display: flex; align-items: flex-start; gap: 10px;
  padding: 9px 0; border-bottom: 1px solid var(--border);
  font-size: .86rem; font-family: Arial, sans-serif;
}
.acc-item:last-child { border-bottom: none; }
```
**Pattern to copy:** Flex row, chip+text, light bottom border, `:last-child { border-bottom: none; }`. Per D-06, target ~6–8px vertical padding (slightly tighter than `.acc-item`'s `9px 0`) and font-size ~0.83–0.85rem.

**Analog 4 for "Read full article" link in dropdown:** `.article-read-more` (`style.css:298-303`).
```css
.article-read-more {
  display: inline-block; margin-top: 6px;
  font-family: Arial, sans-serif; font-size: .76rem; font-weight: 600;
  color: #553c9a; text-decoration: none;
}
.article-read-more:hover { text-decoration: underline; }
```
**Pattern to copy:** Use **as-is** per D-08 — no new rule needed; reuse the existing class. Already injected by the existing `read_more` Python f-string.

**Analog 5 for `.hl-core-idea` (highlight card paragraph):** plain text variant of `.hl-title`/`.hl-reason` (`style.css:129-140`).
```css
.hl-title {
  font-size: .97rem; font-weight: 700; line-height: 1.45; color: var(--text);
  text-decoration: none; display: block;
}
.hl-reason {
  font-size: .82rem; line-height: 1.6; color: var(--sub);
  font-style: italic;
  border-left: 3px solid;
  padding-left: 10px;
}
```
**Pattern to copy:** Per D-10, `.hl-core-idea` is a **plain serif paragraph — no border, no italic** (to differentiate from `.hl-reason`). Suggested: `font-size: .85rem; line-height: 1.55; color: var(--sub);` (slightly larger than `.hl-reason`, no italic, no border-left). Inherits Georgia serif from `body`.

---

## Shared Patterns

### Source-color tinting (inline `style=""`)

**Source:** `_source_color()` (`html_renderer.py:100-105`); already invoked in `_render_rss_items` line 148 (`color = _source_color(source, source_list)`).

**Apply to:** All new color-tinted elements in `_render_rss_items` (core-idea accent bar, keypoint chips). Same `color` variable already in scope — no new computation needed.

```python
color = _source_color(source, source_list)
# inline use:
style="border-color:{color}"   # for .article-core-idea left bar
style="background:{color}"     # for .article-keypoint-chip
```

This is the project's only sanctioned use of inline `style=""` (per CONVENTIONS.md §HTML Output: "never inject styles inline … except for source-color tints"). Keep it that way for all new color injection.

---

### HTML escaping (mandatory for all dynamic strings)

**Source:** `_escape()` (`html_renderer.py:22-23`).
```python
def _escape(t: str) -> str:
    return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")
```

**Apply to:** Every `core_idea` and every `key_points[i]` before f-string interpolation. Phase 1 stores raw strings — no upstream escape happened (per CONTEXT.md "Reusable Assets" line 74).

```python
_escape(core_idea)
_escape(kp)  # for each key point
```

---

### URL safety

**Source:** `_safe_url()` (`html_renderer.py:26-27`).
```python
def _safe_url(url: str) -> str:
    return url if url.startswith(("http://", "https://")) else "#"
```

**Apply to:** "Read full article" link in the new dropdown body (already used by the existing `read_more` line 158 — keep using it as-is).

---

### Conditional inline f-string render (omit-when-empty)

**Source:** existing pattern in `_render_highlights` (`html_renderer.py:131`):
```python
{"<p class='hl-reason' style='border-color:" + color + "'>" + _escape(reason) + "</p>" if reason else ""}
```

**Apply to:**
- `_render_highlights`: new `core_idea` line per D-11 (omit entirely when empty).
- `_render_rss_items`: optional — guard the core-idea quote-box with `{... if core_idea else ""}` if both `core_idea` and `key_points` paths are kept independent.

---

### Markup-extraction decision (Karpathy/simplicity-first)

**Per CONTEXT.md "Claude's Discretion":** Only extract `_render_core_idea(item, color)` / `_render_key_points(item, color)` helpers if the same markup is reused in BOTH `_render_highlights` AND `_render_rss_items`.

**Reality check from analogs:**
- `core_idea` markup differs between the two surfaces: bordered quote-box (`.article-core-idea`) in rows vs plain `<p>` (`.hl-core-idea`) in highlight cards (D-01 vs D-10). **Do not extract a shared helper.**
- `key_points` markup is only used in `_render_rss_items` (highlights don't show numbered points per "deferred" section). **Do not extract — keep inline.**

Conclusion: keep the new markup inline in each `_render_*` function. Matches CLAUDE.md guideline "No abstractions for single-use code".

---

## No Analog Found

None — every new rule and every new branch has a clear in-file analog in `html_renderer.py` and `style.css`. No external references or new patterns are required.

## Metadata

**Analog search scope:** `src/html_renderer.py`, `src/templates/style.css` (in-file analogs only — same module is the canonical pattern source per CONVENTIONS.md "html_renderer.py is the visual source of truth").
**Files scanned:** 2
**Pattern extraction date:** 2026-05-12
