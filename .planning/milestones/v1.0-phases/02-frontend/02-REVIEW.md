---
phase: 02-frontend
reviewed: 2026-05-12T00:00:00Z
depth: standard
files_reviewed: 2
files_reviewed_list:
  - src/templates/style.css
  - src/html_renderer.py
findings:
  critical: 2
  warning: 3
  info: 1
  total: 6
status: issues_found
---

# Phase 02: Code Review Report

**Reviewed:** 2026-05-12
**Depth:** standard
**Files Reviewed:** 2
**Status:** issues_found

## Summary

Reviewed `src/html_renderer.py` and `src/templates/style.css`, focusing on the new structured-summary feature (core idea + key points dropdown for RSS articles). The implementation is largely correct and follows project conventions. Two security issues were found: `_slug()` output is injected into HTML `id=` and `href=` attributes without escaping, and the Reddit `score` field is inserted into HTML without escaping. Three additional warnings cover a logic error that produces an empty but interactive dropdown, an inconsistent key lookup that could crash at runtime, and a hardcoded display string that is always wrong when fewer than 5 highlights exist.

---

## Critical Issues

### CR-01: `_slug()` output inserted unescaped into HTML attributes

**File:** `src/html_renderer.py:260` and `src/html_renderer.py:297`

**Issue:** `_slug()` only lowercases and replaces spaces/slashes with hyphens. It does not remove or escape `"`, `<`, `>`, or `&`. The result is placed directly into an `id="..."` attribute (line 260) and an `href="#..."` attribute (line 297) with no escaping. A section title containing a double-quote character (e.g., from a subreddit name or GitHub language label in `feeds.yaml`) allows attribute injection. For example, the title `foo" onmouseover="alert(1)` would produce:

```html
<details class="accordion" id="foo" onmouseover="alert(1)">
```

CLAUDE.md explicitly requires: "User content is always run through `_escape()` before insertion into HTML." `_slug` violates this.

**Fix:** Apply `_escape()` to the slug before inserting into the attribute:

```python
# line 260 — in _render_accordion:
slug_attr = _escape(_slug(section["title"]))
# ...
return f"""
  <details class="accordion"{open_attr} id="{slug_attr}">
    <summary style="background:{gradient}">
      ...
    </summary>"""

# line 297 — in render_html_digest:
nav_html += (
    f'<a class="nav-pill" href="#{_escape(_slug(s["title"]))}">'
    f'{_ICONS.get(s.get("type"), _DEFAULT_ICON)} {_escape(s["title"])}</a>'
)
```

Note: the `href="#..."` anchor must match the `id=` value exactly after both are escaped the same way.

---

### CR-02: Reddit `score` inserted into HTML without escaping

**File:** `src/html_renderer.py:236`

**Issue:** `item["score"]` is inserted directly into HTML with no conversion or escaping:

```python
badges.append(f'<span class="meta-badge">&#8679; {item["score"]}</span>')
```

The data model declares `score` as `int` (set by the Reddit scraper via `d.get("score", 0)`), but the renderer does not enforce this type. If the Reddit JSON API returns an unexpected type (string, float with special characters, or a value injected through a compromised feed), the raw value reaches the browser. The comparable `stars` field on the same line correctly applies `_escape(str(item["stars"]))`.

**Fix:** Apply the same pattern used for `stars`:

```python
badges.append(f'<span class="meta-badge">&#8679; {_escape(str(item["score"]))}</span>')
```

---

## Warnings

### WR-01: Empty `<details>` dropdown rendered when only `core_idea` is present

**File:** `src/html_renderer.py:163-192`

**Issue:** The condition on line 163 is `if has_core_idea or has_dropdown:`. When an article has a `core_idea` but no non-empty `key_points` (i.e., `has_core_idea=True`, `has_dropdown=False`), the code still constructs a full `<details>` element with an expand chevron. Inside that dropdown, the only content is the "Read full article" link — no key points. The user sees a clickable disclosure widget that expands to reveal only a link they could have accessed another way. This is a misleading UX and was not the design intent (the dropdown was introduced to show key points).

**Fix:** Only render the `<details>` wrapper when there are actual key points to display:

```python
if has_dropdown:
    # build details_html with key_points + read_more (existing logic)
    ...
    core_idea_html = (
        f'<p class="article-core-idea" style="border-color:{color}">{_escape(core_idea)}</p>'
        if has_core_idea else ""
    )
    content = core_idea_html + details_html   # or whichever order is preferred
elif has_core_idea:
    # No key points, just show core idea + plain link (no dropdown)
    read_more = (
        f'<a class="article-read-more" href="{_escape(url)}" target="_blank" rel="noopener">Read full article &#8599;</a>'
        if url != "#" else ""
    )
    content = (
        f'<p class="article-core-idea" style="border-color:{color}">{_escape(core_idea)}</p>'
        + (f'<a class="article-link" href="{_escape(url)}" target="_blank" rel="noopener">{title}</a>' if url != "#" else f'<span class="article-link">{title}</span>')
    )
elif url != "#":
    content = f'<a class="article-link" href="{_escape(url)}" target="_blank" rel="noopener">{title}</a>'
else:
    content = f'<span class="article-link">{title}</span>'
```

---

### WR-02: Inconsistent access to `h["index"]` — direct vs. `.get()` — risks KeyError

**File:** `src/html_renderer.py:283`

**Issue:** `render_html_digest` builds `highlight_indices` at line 283 with a bare dict key access:

```python
highlight_indices = {h["index"] for h in highlights}
```

But `_render_highlights` (line 113) uses the safe `.get()` form:

```python
idx = h.get("index", 0)
```

If any element of `highlights` lacks an `"index"` key, line 283 raises `KeyError` and aborts the entire render. The summarizer currently guarantees the key exists (it filters highlights at `summarizer.py:79`), but `render_html_digest` takes a raw `sections` list and documents no preconditions. A future caller, a config-supplied highlights list, or a refactor of the summarizer could break this silently.

**Fix:** Use `.get()` with the same default used in `_render_highlights`:

```python
highlight_indices = {h.get("index", 0) for h in highlights if "index" in h}
```

Or, to be fully defensive and match the intent of "skip if out of range":

```python
highlight_indices = {h["index"] for h in highlights if isinstance(h.get("index"), int)}
```

---

### WR-03: Masthead hardcodes "5 highlights" regardless of actual count

**File:** `src/html_renderer.py:60`

**Issue:** The `_HTML_TEMPLATE` contains the literal string `&#9733; 5 highlights` in the masthead metadata bar. The actual number of highlights rendered depends on `highlights[:5]` in `_render_highlights`, which can produce 0–5 cards depending on what the summarizer returns. When highlights are empty (summarization disabled, or a scrape failure) or fewer than 5, the header always claims 5.

**Fix:** Pass the actual highlight count as a template variable:

```python
# in render_html_digest:
highlight_count = len(highlights[:5])

html = _HTML_TEMPLATE.format(
    ...
    highlight_count=highlight_count,
    ...
)
```

In `_HTML_TEMPLATE`:
```html
<span>&#9733; {highlight_count} highlights</span>
```

---

## Info

### IN-01: `ai_summary` variable retained in `_render_rss_items` but never used in new code path

**File:** `src/html_renderer.py:153`

**Issue:** `ai_summary = item.get("ai_summary", "")` is assigned at line 153 with the comment "legacy compat — no longer drives dropdown". The variable is never read in the function after this assignment. It is dead code in the new implementation. While it documents a migration note, it adds noise and could confuse future maintainers into thinking it affects behavior.

**Fix:** Remove the assignment, or if intentionally kept for documentation, note it explicitly:

```python
# ai_summary field is no longer rendered; key_points/core_idea replace it.
# item.get("ai_summary") is preserved in the data model for backward compat.
```

---

_Reviewed: 2026-05-12_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
