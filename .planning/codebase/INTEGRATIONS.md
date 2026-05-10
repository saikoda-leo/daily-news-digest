# External Integrations

**Analysis Date:** 2026-05-10

## External APIs

**Anthropic Claude API:**
- Purpose: Summarize news sections (2-3 sentence digest per section), pick top 5 highlights, and generate per-article 1-2 sentence summaries
- Model: `claude-haiku-4-5-20251001`
- SDK: `anthropic` Python client (`src/summarizer.py`)
- Auth: `ANTHROPIC_API_KEY` environment variable — read automatically by `anthropic.Anthropic()`
- Features used: `messages.create` with prompt caching (`cache_control: ephemeral` on system prompts)
- All three functions in `src/summarizer.py` (`summarize_section`, `get_top_highlights`, `summarize_items`) use the same singleton client via `_get_client()`

**Reddit JSON API:**
- Purpose: Fetch top posts of the day from configured subreddits
- Endpoint: `https://www.reddit.com/r/{subreddit}/top.json?limit=N&t=day`
- Client: `requests` (no SDK)
- Auth: None — public API, unauthenticated
- User-Agent: `"daily-info-digest/1.0 (personal newspaper bot)"`
- Implementation: `src/scrapers/reddit.py`

**GitHub Trending (HTML scrape):**
- Purpose: Fetch trending repositories by language and time period
- Endpoint: `https://github.com/trending/{language}?since={daily|weekly|monthly}`
- Client: `requests` + `beautifulsoup4` (HTML parsing)
- Auth: None — no GitHub API token; scrapes public HTML
- User-Agent: `"Mozilla/5.0 (compatible; daily-info-digest/1.0)"`
- CSS selector: `article.Box-row` — brittle; will break if GitHub changes markup
- Implementation: `src/scrapers/github.py`

## Data Sources

**RSS/Atom Feeds (configured in `feeds.yaml`):**
- Hacker News: `https://news.ycombinator.com/rss`
- The Verge: `https://www.theverge.com/rss/index.xml`
- VnExpress: `https://vnexpress.net/rss/tin-moi-nhat.rss`
- Tuoi Tre: `https://tuoitre.vn/rss/tin-moi-nhat.rss`
- Tinhte.vn: `https://tinhte.vn/rss`
- Client: `feedparser` library (`src/scrapers/rss.py`)
- All feeds capped at `max_items: 5` per source (configurable in `feeds.yaml`)

**Reddit Subreddits (configured in `feeds.yaml`):**
- r/programming — top 5 posts/day
- r/MachineLearning — top 5 posts/day

**GitHub Trending Languages (configured in `feeds.yaml`):**
- Python trending repos
- All-language trending repos
- Time window: `daily`
- Max repos per language: 5

## Authentication

**API Keys:**
- `ANTHROPIC_API_KEY` — only secret required; must be exported in shell before running
- No OAuth tokens, no GitHub PAT, no Reddit API credentials

**No auth required for:**
- All RSS feeds (public)
- Reddit JSON API (public, rate limits apply)
- GitHub trending page (public HTML scrape)

## Configuration & Secrets Management

**Config file:** `feeds.yaml` — controls all data sources, summarization toggle, and output directory. No code changes needed to add/remove feeds, subreddits, or GitHub languages.

**Secrets:** `ANTHROPIC_API_KEY` only. No `.env` file loading is present — must be set in the shell environment before running `python main.py`.

**No secrets file, vault, or secrets manager detected.**

## Third-party Services

**macOS `open` command:**
- Used via `subprocess.Popen(["open", "-a", "Google Chrome", str(html_path)])` in `main.py:100`
- Auto-opens the generated HTML digest in Google Chrome after each run
- macOS-specific: will fail silently on Linux/Windows (subprocess call, not checked)

## Webhooks & Callbacks

**Incoming:** None — no HTTP server; tool is a CLI script

**Outgoing:** None — all communication is outbound API calls during a single run

---

*Integration audit: 2026-05-10*
