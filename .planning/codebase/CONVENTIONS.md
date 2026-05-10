# Conventions

## Language & Runtime

- Python 3.9+ (CPython). All application logic lives in `main.py` and `src/`.
- No build system. Run directly: `python main.py`.
- Virtual environment: `.venv/` (created with `python -m venv .venv`, gitignored).
- Required env var: `ANTHROPIC_API_KEY` exported in shell before running.

## Code Style

- Match the existing style exactly — no autoformatting passes unless the whole file already uses one.
- Indentation: 4 spaces throughout.
- Type annotations: used on public function signatures (e.g., `list[dict]`, `Path`, `str`). Follow suit for new functions.
- Line length: no hard limit enforced, but keep lines readable (roughly ≤100 chars).
- String quoting: double quotes preferred; single quotes acceptable for short inline strings.
- Module-level private constants use a leading underscore (`_HEADERS`, `_CSS`, `_JS`, `_CLIENT`).
- Module-level lazy singleton (e.g., `_client`) initialized to `None` and populated on first use via a `_get_client()` helper.

## Naming

| Thing | Convention | Example |
|---|---|---|
| Functions | `snake_case` | `fetch_rss`, `render_html_digest` |
| Private helpers | `_snake_case` | `_escape`, `_render_highlights` |
| Constants | `_UPPER_SNAKE` | `_SYSTEM_PROMPT`, `_SOURCE_PALETTE` |
| Variables | `snake_case` | `rss_items`, `highlight_indices` |
| Files | `snake_case.py` | `html_renderer.py` |

## Data Model

Scrapers return a flat `list[dict]`. The canonical keys are:

| Key | Type | Required | Set by |
|---|---|---|---|
| `title` | `str` | Yes | all scrapers |
| `url` | `str` | Yes | all scrapers |
| `summary` | `str` | Yes (may be empty) | all scrapers |
| `source` | `str` | No — added by `main.py` for RSS items | `main.py` |
| `stars` | `str` | No — GitHub only | `github.py` |
| `score` | `int` | No — Reddit only | `reddit.py` |
| `ai_summary` | `str` | No — added after summarization | `main.py` |

Sections passed between orchestrator and renderers are dicts with shape:
```python
{
    "title": str,
    "items": list[dict],  # scraper output, possibly with "source" and "ai_summary" added
    "type": "rss" | "github" | "reddit",
    "summary": str,        # optional, added by summarizer
    "highlights": list,    # optional, RSS section only; [{index, reason}, ...]
}
```

## Error Handling

- Scraper failures are isolated in `main.py` via `_scrape()`. A failing source prints a warning to stderr and returns `None`; the rest of the digest continues.
- Summarizer functions catch `Exception` internally and return a safe fallback (empty string or empty list). They never propagate exceptions to the orchestrator.
- Never `sys.exit()` inside a scraper or summarizer — raise naturally and let `_scrape()` or the try/except in `main.py` handle it.

## Claude API Usage

- Model: `claude-haiku-4-5-20251001` (fast, cheap; appropriate for bulk summarization).
- System prompts use `cache_control: {"type": "ephemeral"}` to benefit from prompt caching across repeated calls within the same run.
- Client is a lazy module-level singleton (`_get_client()` in `summarizer.py`); do not instantiate `anthropic.Anthropic()` more than once.
- All Claude calls set an explicit `max_tokens` budget (256, 512, or 1024 depending on expected output size).
- Responses that must be JSON are stripped of markdown fences before parsing (`re.sub` for triple backticks).

## Configuration (feeds.yaml)

All source and output config lives in `feeds.yaml`. No source changes should require editing Python files:

- Add/remove RSS feeds: edit `rss_feeds` list.
- Add/remove GitHub languages: edit `github_trending.languages`.
- Add/remove subreddits: edit `subreddits` list.
- Toggle summarization: set `summarization.enabled` to `true` or `false`.
- Change output directory: set `output.dir`.

## HTML Output

- All CSS and JavaScript are embedded as module-level string constants (`_CSS`, `_JS`) in `html_renderer.py`. No external stylesheets or scripts.
- HTML is assembled via f-strings and a single `_HTML_TEMPLATE` format string. No templating library.
- User content is always run through `_escape()` before insertion into HTML to prevent injection.
- Section type determines color scheme via `_SECTION_COLORS`; source names get colors from `_SOURCE_PALETTE` (cycled by insertion order).
- The HTML renderer is the source of truth for the visual design. The markdown renderer (`renderer.py`) is a simpler fallback.

## Dependencies

- `anthropic` — Claude API client.
- `feedparser` — RSS/Atom parsing.
- `requests` — HTTP for GitHub trending and Reddit JSON API.
- `beautifulsoup4` — HTML scraping for GitHub trending.
- `pyyaml` — `feeds.yaml` loading.
- No dev-only dependencies are declared. Do not add dev extras to `requirements.txt`; use a separate `requirements-dev.txt` if needed.

## Git

- Commit message style: lowercase imperative subject, no period. Examples from history: `feat: per-article AI summary as dropdown in HTML report`, `feat: auto-open digest HTML in Google Chrome after generation`, `digest: 2026-05-10`.
- Digest output files (`output/`) are gitignored; do not commit them.
- Do not commit `.venv/`, `__pycache__/`, or `*.pyc`.
