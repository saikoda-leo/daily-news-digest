# Architecture

daily-info-digest is a single-run Python script that scrapes configured sources,
summarizes them with Claude AI, and writes a dated HTML (and Markdown) digest to
the `output/` directory.

## Pipeline

```
feeds.yaml
    │
    ▼
main.py  (orchestrator)
    │
    ├── src/scrapers/rss.py       ── feedparser → [{title, url, summary}]
    ├── src/scrapers/github.py    ── requests + BeautifulSoup HTML scrape
    │                                  → [{title, url, summary, stars}]
    └── src/scrapers/reddit.py    ── public Reddit JSON API, no auth
                                       → [{title, url, summary, score}]
    │
    ▼
    sections = [{title, items, type}, ...]
    │
    ├── src/summarizer.py  (Anthropic API — claude-haiku-4-5-20251001)
    │     ├── get_top_highlights()   one call: pick 5 most notable RSS items
    │     ├── summarize_section()    one call per section: 2-3 sentence theme summary
    │     └── summarize_items()      one call per section: 1-2 sentence per article
    │
    ▼
    sections enriched with summary, highlights, per-item ai_summary
    │
    ├── src/renderer.py         → output/YYYY-MM-DD.md
    └── src/html_renderer.py    → output/YYYY-MM-DD.html
                                   (auto-opened in Google Chrome)
```

## Key Design Decisions

**Fault isolation.** Every scraper is wrapped in `_scrape()` in `main.py`. A
failing source prints a warning to stderr and the rest of the run continues
unaffected.

**Prompt caching.** All Claude calls mark the system prompt with
`"cache_control": {"type": "ephemeral"}` to benefit from Anthropic's prompt
cache across the repeated calls within a single run.

**No auth required.** GitHub trending is scraped as HTML. Reddit uses the public
`.json` endpoint. RSS feeds are unauthenticated.

**Config-only source management.** All sources (RSS URLs, GitHub languages,
subreddit names, item counts) live in `feeds.yaml`. No code changes are needed
to add or remove sources.

**Two output formats.** `renderer.py` writes a plain Markdown file suitable for
archiving or reading in any editor. `html_renderer.py` writes a self-contained
styled HTML file (all CSS/JS inlined) with a newspaper masthead, top-5 highlight
cards, source-filter tabs, collapsible per-article AI summaries, and accordion
sections for GitHub/Reddit.

## Data Shape

Each scraper returns a list of items. All items share a common base:

```python
{
    "title":   str,
    "url":     str,
    "summary": str,          # raw excerpt / description / selftext
}
```

Source-specific additions:
- RSS items gain `"source": feed["name"]` in `main.py`.
- GitHub items include `"stars": str`.
- Reddit items include `"score": int`.

After summarization each item gains `"ai_summary": str`. The RSS section also
gains `"highlights": [{"index": int, "reason": str}, ...]` and
`"summary": str`.

## External Dependencies

| Package        | Purpose                              |
|----------------|--------------------------------------|
| anthropic      | Claude API calls (Haiku model)       |
| feedparser     | RSS/Atom feed parsing                |
| requests       | HTTP for GitHub and Reddit scrapers  |
| beautifulsoup4 | HTML parsing for GitHub trending     |
| pyyaml         | feeds.yaml config loading            |
