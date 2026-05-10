# Project Structure

```
daily-info-digest/
│
├── main.py                  # Entry point and orchestrator
│                              Loads feeds.yaml, runs scrapers, calls
│                              summarizer, writes both output files,
│                              and opens the HTML in Chrome.
│
├── feeds.yaml               # All source configuration (no code changes needed)
│                              Sections: rss_feeds, github_trending,
│                              subreddits, summarization, output.
│
├── requirements.txt         # Python dependencies (pip install -r)
│
├── CLAUDE.md                # Project guidance for Claude Code
│
├── src/
│   ├── __init__.py
│   │
│   ├── scrapers/
│   │   ├── __init__.py
│   │   ├── rss.py           # fetch_rss(url, max_items) → list[dict]
│   │   │                      Uses feedparser. Returns title/url/summary.
│   │   ├── github.py        # fetch_github_trending(language, since, max_repos)
│   │   │                      HTML scrape of github.com/trending.
│   │   │                      Returns title/url/summary/stars.
│   │   └── reddit.py        # fetch_reddit_posts(subreddit, max_posts)
│   │                          Public Reddit JSON API, top posts by day.
│   │                          Returns title/url/summary/score.
│   │
│   ├── summarizer.py        # All Claude API calls
│   │                          summarize_section()   – section-level summary
│   │                          summarize_items()     – per-article summaries
│   │                          get_top_highlights()  – pick top 5 RSS items
│   │                          Uses claude-haiku-4-5-20251001 with prompt caching.
│   │
│   ├── renderer.py          # render_digest() → output/YYYY-MM-DD.md
│   │                          Plain Markdown with blockquote summaries.
│   │
│   └── html_renderer.py     # render_html_digest() → output/YYYY-MM-DD.html
│                              Self-contained HTML (CSS + JS inlined).
│                              Newspaper masthead, top-5 highlight cards,
│                              source-filter tabs, per-article AI summary
│                              dropdowns, GitHub/Reddit accordion sections.
│
└── output/                  # Generated digests (gitignored)
    └── YYYY-MM-DD.md / .html
```

## Module Responsibilities

### main.py
Orchestrates the full pipeline. Calls each scraper via the fault-isolating
`_scrape()` wrapper, collects sections, drives the summarizer in order
(highlights → section summaries → per-item summaries), then calls both
renderers. Finally opens the HTML output in Google Chrome with `subprocess`.

### src/scrapers/rss.py
Single function `fetch_rss`. Uses `feedparser.parse`. Extracts `title`, `link`,
and `summary`/`description` from each entry.

### src/scrapers/github.py
Single function `fetch_github_trending`. HTTP GET with a browser User-Agent,
parsed with BeautifulSoup. Selects `article.Box-row` elements and extracts
repo name, URL, description, and star count.

### src/scrapers/reddit.py
Single function `fetch_reddit_posts`. Calls the public
`reddit.com/r/{sub}/top.json` endpoint with `t=day`. No authentication.

### src/summarizer.py
Three public functions, all using `claude-haiku-4-5-20251001` with a cached
system prompt:
- `summarize_section` – 2-3 sentence thematic summary for one section.
- `summarize_items` – returns a JSON array of 1-2 sentence summaries, one per
  item, in a single API call.
- `get_top_highlights` – returns a JSON array of `{index, reason}` objects
  identifying the 5 most notable RSS stories.

A module-level singleton `_client` avoids constructing the Anthropic client
more than once per run.

### src/renderer.py
Single function `render_digest`. Writes plain Markdown: a top-level heading,
then for each section an H2, an optional blockquote summary, and a bullet list
of linked items with star/score metadata where present.

### src/html_renderer.py
Single function `render_html_digest` backed by several private helpers. All CSS
and JavaScript are inlined as module-level string constants (`_CSS`, `_JS`,
`_HTML_TEMPLATE`). Key features:
- Newspaper-style masthead with date and story count.
- Navigation pill bar linking to each section by anchor.
- Top-5 highlight cards rendered as a responsive CSS grid.
- RSS section with source-filter tab bar (JavaScript-driven, no page reload).
- Per-article `<details>` dropdowns showing the AI summary.
- GitHub and Reddit sections as `<details>` accordions with their own
  per-item AI summary dropdowns.

## Naming Conventions

| Thing | Convention | Example |
|---|---|---|
| Functions | `snake_case` | `fetch_rss`, `render_html_digest` |
| Private helpers | `_snake_case` | `_escape`, `_render_highlights` |
| Constants | `_UPPER_SNAKE` | `_SYSTEM_PROMPT`, `_SOURCE_PALETTE` |
| Variables | `snake_case` | `rss_items`, `highlight_indices` |
| Files | `snake_case.py` | `html_renderer.py` |
