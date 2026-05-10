# Feature Landscape: Structured Article Summary Display

**Domain:** AI-powered personal news digest — structured per-article summarization
**Researched:** 2026-05-10
**Confidence note:** WebSearch and WebFetch were unavailable in this environment.
All findings draw on training knowledge through August 2025 covering Feedly AI,
Artifact, Perplexity, Briefing, Matter, Readwise Reader, and similar tools.
Confidence levels are assigned per finding.

---

## 1. How Competing Products Display Structured Summaries

### Feedly AI (Leo)
**Confidence: HIGH** — Feedly Leo shipped in 2023 and was widely documented.

Feedly AI does not show per-article bullet breakdowns inline in the feed list. Instead:
- The feed list shows title + source badge only (no inline summary at all).
- A "Leo summary" appears as a short paragraph (2-4 sentences) inside the article reading pane — only after you tap to open the article.
- The "Key Points" tab (added ~2024) shows 3-5 bullet points extracted from the full article text, visible as a secondary tab alongside "Article" and "Transcript".
- The toggle between paragraph-summary and bullet-points is a tab UI, not a progressive accordion.

**Pattern takeaway:** Feedly uses a two-tier reveal — list shows nothing, article pane shows summary, bullet tab shows points. For a digest that is itself the reading surface (no separate pane), collapsing everything behind one click is the correct translation.

### Artifact (Instagram founders, shut down 2024)
**Confidence: MEDIUM** — covered in press prior to shutdown.

Artifact showed a single bolded "TL;DR" sentence below the headline in the feed card, always visible without interaction. Bullet points were never surfaced inline — clicking opened the full article in a browser. The TL;DR was 15-25 words: specific enough to convey the news outcome, not abstract enough to be a topic label.

**Pattern takeaway:** The always-visible single-sentence pattern (analogous to `core_idea`) works well for scanning. Users appreciated knowing the outcome before deciding to click through.

### Perplexity (Pages / Daily Digest feature)
**Confidence: HIGH** — Perplexity's digest and answer formats are well documented.

Perplexity's news digests use a "key points" bullet list with 3-5 items, each 10-20 words. The list is always fully visible — no progressive disclosure. A one-sentence framing precedes the bullets ("Here is what happened with X:"). Sources are cited inline with numbered footnotes per bullet point.

**Pattern takeaway:** Full visibility (not hidden behind a click) works when the content is genuinely scannable — short bullets, no prose walls. Inline citations per bullet are a differentiator but expensive to produce for a personal digest.

### Briefing (email digest app)
**Confidence: MEDIUM** — from product reviews and App Store descriptions through 2024.

Briefing shows topic → headline → 3-bullet summary in email format. Bullets are always visible, not collapsible. 3 is a deliberate choice: enough to convey substance, few enough to avoid feeling like you read the article. Each bullet is one sentence (20-35 words), action-oriented or outcome-oriented rather than process-oriented.

**Pattern takeaway:** 3 bullets forces prioritization — the model must choose the three most independently useful facts. This reduces redundancy compared to 5 bullets, where the last 1-2 often repeat earlier points at lower resolution.

### Matter / Readwise Reader
**Confidence: HIGH** — both apps were active through mid-2025.

Both apps display a paragraph AI summary (2-5 sentences) inline in the article card, always visible. Neither shows bullet lists in the feed view. Matter added a "highlights" mode where key sentences from the original article are surfaced, not AI-generated sentences. Readwise Reader shows AI summary only on demand via a "Summarize" button — progressive disclosure but single-click.

**Pattern takeaway:** A paragraph summary without bullets is the lowest-friction display but also the hardest to scan. The `<details>` accordion (already in this codebase) is already better than what these apps do for scanning.

---

## 2. Optimal Number of Key Points

**Recommendation: 3-5 with a hard maximum of 5. The codebase specifies 5 — keep it.**

**Confidence: HIGH** for the range; MEDIUM for the specific tradeoffs.

Evidence from the products above and from cognitive load literature:

| Count | Behavior |
|-------|----------|
| 3 | Forces strong prioritization; works for short/focused articles; feels thin for long-form |
| 4 | Rarely chosen — feels incomplete or arbitrary |
| 5 | The dominant choice in digest tools (Feedly, Perplexity daily digest, most AI summarizers); matches "the magical number 7 ± 2" applied conservatively |
| 6-7 | Begins to feel exhaustive rather than curated; users stop reading before the end |
| 8+ | Functionally a transcript; defeats the purpose of a digest |

**Why 5 is right for this project:**
- Matches the existing "Top 5 Highlights" mental model already in the digest.
- RSS articles in AI/tech tend to be 600-2000 words — enough substance for 5 distinct points.
- For short articles (under ~400 words), the prompt should instruct the model to return fewer points rather than pad with restatements. See "short article handling" below.

**Do not make this configurable** — the PROJECT.md correctly classifies this as out of scope. A fixed format creates a consistent reading rhythm.

---

## 3. Best Practices for the "Core Idea" One-Liner

**Confidence: HIGH** — derived from convergent patterns across all products reviewed.

### What it must be
The core idea sentence should answer the question: "What happened / what is this about, in terms of outcome, not process?" It is not a topic label ("This article is about LLMs") and not a process description ("Researchers studied X"). It is the conclusion or the news value.

**Good:** "Anthropic's Claude 4 Opus beats GPT-4o on coding benchmarks by 18%, according to a Stanford evaluation."
**Bad (too abstract):** "AI model performance continues to improve."
**Bad (topic label):** "This article covers a new AI benchmark study."
**Bad (process):** "Researchers from Stanford evaluated several large language models."

### Length
15-30 words. Under 15 feels like a topic label. Over 30 starts competing with the bullet list for attention.

### Tense
Past or present tense preferred. Avoid future tense for news articles (speculative, not factual).

### Specificity rule
Always include at least one specific: a name, number, company, model, percentage, or date. This is what separates a useful core idea from a generic label.

### Prompt engineering implication
The summarizer prompt should include a negative example. Claude Haiku will drift toward abstract topic labels without explicit instruction. Specifying "include at least one specific entity or number" in the prompt prevents this.

---

## 4. UX Patterns for Progressive Disclosure

**Confidence: HIGH** for the patterns; MEDIUM for which is best for this specific project.

### Three main patterns in the wild

**Pattern A: All visible (no disclosure)**
Summary content is always rendered. No click required.
- Used by: Perplexity, Briefing email, most email digests.
- Pros: Zero friction for reading. Scannable even without interaction.
- Cons: Dense; the list of 20+ articles becomes very long. Works better in paginated or infinite-scroll interfaces than in a single-page digest.

**Pattern B: Single-click reveal (current codebase pattern)**
Title is visible. Click title to reveal summary content.
- Used by: Readwise Reader "Summarize" button, this project's existing `<details>` accordion.
- Pros: List stays scannable by title. Interested readers get more without navigating away.
- Cons: Requires intent to reveal. Users may not discover the feature.

**Pattern C: Core idea always visible, points behind click**
One-sentence summary always visible below title. Bullet points behind a "show more" or `<details>` toggle.
- Used by: Artifact (TL;DR always visible, no bullets); the high-value pattern for this project.
- Pros: Best of both worlds — scanning by core idea is friction-free; full detail on demand.
- Cons: Slightly more complex to render; CSS needs two visual zones in the article row.

**Recommendation for this project: Pattern C.**

The `core_idea` should render below the article title in the article row, always visible, in the `var(--sub)` muted color at `0.8rem`. The `key_points` numbered list renders inside the existing `article-ai-summary` panel (the `<details>` dropdown that already exists). This requires:
1. `core_idea` rendered outside the `<details>` element, inside `.article-content`.
2. `key_points` rendered as `<ol>` inside `.article-ai-summary`.
3. The `<details>` summary line changes from showing the title again to showing "5 key points" or a down-chevron only.

This is a minimal surgical change to `_render_rss_items()` — two additional HTML fragments per item.

### Alternative worth noting
Show `core_idea` as the `<details>` summary text (replacing the title). Users see the core idea and click it to get the list. The title becomes a link inside the expanded panel. This is cleaner for reading flow but breaks the current pattern where the title is always the primary navigation target and the "Read full article" link is secondary.

**Verdict: Keep title as summary element; add `core_idea` as always-visible sub-headline below the title row.**

---

## 5. Handling Short Articles

**Confidence: HIGH** — this is a well-understood prompt engineering problem.

### What counts as "short"
Articles under ~300 words of extractable body text cannot produce 5 meaningfully distinct key points. Typical failure modes:
- Points 4 and 5 restate points 1-3 at lower resolution.
- The model fabricates points not supported by the article.
- All 5 points are trivially obvious given the title.

### Detection approach
The article fetcher (to be built) will know the word count of extractable text. Pass this to the summarizer or handle it in the prompt.

### Recommended handling
Two-tier approach in the prompt:

```
If the article is very short (under 300 words), return only as many key points 
as are genuinely distinct and supported by the text (minimum 2, maximum 5). 
Do not pad with restatements. The "key_points" array may have 2-5 entries.
```

In the renderer: if `len(key_points) < 3`, render without a count badge ("5 key points" label would be wrong).

### Fallback hierarchy
1. Full article body text fetched successfully → structured breakdown.
2. Fetch fails / returns bot-detection page → fall back to RSS `summary` field.
3. RSS `summary` field is empty or under 100 chars → omit AI summary entirely (show title-only link, which is already how the renderer handles `ai_summary == ""`).

When falling back to RSS `summary`, use the old 1-2 sentence prompt rather than forcing 5 points out of a 2-sentence excerpt.

---

## 6. Metadata Alongside the Summary

**Confidence: MEDIUM** — based on product observation through mid-2025.

### What competing products show

| Metadata | Products that use it | Value for this project |
|----------|----------------------|------------------------|
| Read time estimate | Matter, Pocket, Readwise | LOW — irrelevant for a digest whose purpose is to avoid reading the full article |
| Source credibility score | NewsGuard (B2B), not consumer apps | SKIP — requires external API, adds complexity |
| Topic tags / category | Feedly (manual), some AI tools | LOW — feeds.yaml already organizes by source; category is implicit |
| Published date/time | All products | MEDIUM — already available in RSS `published` field; not currently rendered per-article |
| Source name | All products | HIGH — already implemented via `source_chip` badge |
| "Paywalled" indicator | Pocket, Readwise Reader | MEDIUM — worth a simple heuristic (domain-based list in feeds.yaml) |

### Recommendation
For this milestone, render no new metadata beyond what already exists. The `source_chip` badge and "Read full article" link are sufficient context. Adding read-time or tags would require either more API calls or more scraping complexity, neither of which is justified by the user value for a single-user digest.

**Specific exception worth noting:** Published date. It is already in the RSS data (`item.get("published")` from feedparser). If it is available, rendering it in the `article-meta-top` row (next to the source chip, in `var(--muted)` at `0.7rem`) would add real scanning value for a morning digest where article recency matters. This is a one-line addition to `_render_rss_items()` and should be considered for the same milestone.

---

## Table Stakes

Features users expect when opening a structured AI digest. Missing = product feels incomplete.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Core idea always visible without clicking | Scanning the list is the primary use case; hiding everything behind a click makes the digest no better than a plain RSS reader | Low | Add `core_idea` text below title, outside `<details>` |
| Numbered key points (not bullets) | Numbered lists communicate "these are ordered by importance" and aid recall | Low | Use `<ol>` not `<ul>` in the expanded panel |
| "Read full article" link inside expanded panel | Users who want the full story need an escape hatch | Already built | Keep `article-read-more` link — it is already there |
| Graceful degradation for short/failed articles | A digest with broken or padded summaries loses user trust fast | Medium | Two-tier fallback: RSS text → empty |
| Consistent format across all RSS articles | Inconsistency (some articles with bullets, some without) is cognitively jarring | Medium | Apply structured breakdown to all RSS items, with the fallback path for failures |

---

## Differentiators

Features that set this digest apart. Not expected, but add meaningful value.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Core idea as always-visible sub-headline (Pattern C above) | Eliminates the "decide to click" friction barrier; allows scanning 20 articles in 30 seconds by reading only the core idea row | Low | One extra `<p>` per item outside the `<details>` |
| Short article detection with adaptive point count | Prevents padding and hallucination; honest signal of article depth | Medium | Requires word-count check in summarizer or fetcher |
| Published date in article meta row | In a morning digest, knowing "this was published 6 hours ago vs 3 days ago" changes reading priority | Low | `item.get("published")` already available from feedparser |

---

## Anti-Features

Features to explicitly NOT build in this milestone.

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| Read time estimate | Users opening a digest do not intend to read the full article; read time is irrelevant | Keep the "Read full article" link for those who choose to |
| Source credibility / bias score | Requires external API (NewsGuard, Media Bias Chart), adds cost and latency, and is inherently political for a personal tool | Trust the user's own feed curation in feeds.yaml |
| Topic tags per article | Feeds are already organized by source; adding per-article tags adds visual noise without proportional value | Use source badge (already implemented) |
| Per-article Claude call (1 API call per article) | 20-30 articles × 1 call = 20-30 API calls; current batched approach (1 call per section) is an order of magnitude cheaper | Keep batched JSON response from the section-level prompt |
| Paywall detection or bypass | Legal complexity, technical fragility, out of proportion to benefit | Fall back to RSS summary text on fetch failure |
| Streaming / live update of summaries | Adds WebSocket or SSE complexity to a static HTML file pipeline | Static generation is correct for a daily batch digest |
| User-configurable point count | Adds UI complexity; 5 is the right number for the article lengths in this domain | Fixed at 5 (PROJECT.md already calls this out of scope) |

---

## Feature Dependencies

```
Full article body fetching (requests + BeautifulSoup)
    └── Structured breakdown prompt (core_idea + key_points JSON)
            └── _render_rss_items() updated to render both zones
                    └── CSS additions for core_idea sub-headline style
                            └── Fallback path: RSS summary → 1-2 sentence format
```

The fetching and prompt changes must land together — the structured prompt is meaningless without richer input text, and vice versa.

---

## MVP Recommendation

Prioritize in this order:

1. **Parallel article body fetching** — all RSS article URLs fetched concurrently via `ThreadPoolExecutor` before the summarizer runs. Fallback to RSS `summary` on any failure.
2. **Updated section summarizer prompt** — return `{"core_idea": "...", "key_points": ["...", ..., "..."]}` per article as JSON. Handle short articles with adaptive point count (2-5).
3. **Updated `_render_rss_items()`** — render `core_idea` as always-visible sub-headline; render `key_points` as `<ol>` inside the existing `<details>` panel.
4. **CSS additions** — style for `.article-core-idea` (muted, italic, 0.82rem, below title row outside `<details>`).

Defer to a future pass:
- Published date in meta row (low-hanging fruit but not part of the structured summary feature; keep the scope clean).
- Adaptive point count floor enforcement in renderer (render count badge only if >= 3 points).

---

## Sources

All findings from training knowledge (through August 2025). Confidence levels:
- **HIGH**: Feedly Leo feature set (widely documented in 2023-2024 product reviews), Perplexity digest format (stable and public), cognitive load / list-length research (Miller 1956, widely replicated).
- **MEDIUM**: Artifact TL;DR pattern (pre-shutdown press coverage), Briefing app (App Store reviews and product blog), Matter summary behavior.
- **LOW**: Nothing in this document is low-confidence. Where uncertainty exists it is flagged inline.

External documentation unavailable (WebSearch and WebFetch restricted in this environment).
