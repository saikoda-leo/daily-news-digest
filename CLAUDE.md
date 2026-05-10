# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Develop a "personal newspaper" that scrapes your favorite RSS feeds, GitHub repos, or subreddits and summarizes the top news about AI, LLM model, job related to AI and affected by AI into a single html or markdown file each morning.

## Setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-...
```

## Run

```bash
python main.py
```

Output is written to `output/YYYY-MM-DD.md`. Configure sources in `feeds.yaml` — no code changes needed to add/remove feeds, subreddits, or GitHub languages.

## Architecture

```
main.py              # orchestrator: scrape → summarize → render
src/
  scrapers/
    rss.py           # feedparser-based; returns [{title, url, summary}]
    github.py        # HTML scrape of github.com/trending (no auth)
    reddit.py        # public Reddit JSON API, no auth, top posts by day
  summarizer.py      # one Claude Haiku call per section; system prompt cached
  renderer.py        # writes markdown file from sections list
feeds.yaml           # all source config lives here
output/              # gitignored; one .md per day
```

Scraper failures are isolated — a single failing source prints a warning to stderr and the rest of the digest continues.

## Coding Guidelines (Karpathy)

### 1. Think Before Coding
- State assumptions explicitly before implementing. If uncertain, ask.
- If multiple interpretations exist, present them — don't pick silently.
- If something is unclear, stop and name what's confusing.

### 2. Simplicity First
- Write the minimum code that solves the problem. Nothing speculative.
- No abstractions for single-use code, no unrequested configurability.
- If 200 lines could be 50, rewrite it.

### 3. Surgical Changes
- Touch only lines directly required by the request.
- Don't improve adjacent code, comments, or formatting.
- Match existing style. Mention unrelated dead code — don't delete it.
- Remove only imports/variables/functions that your own changes made unused.

### 4. Goal-Driven Execution
- Define verifiable success criteria before starting non-trivial tasks.
- For multi-step tasks, state a brief plan with a check per step.
- Loop until criteria are met.

<!-- GSD:project-start source:PROJECT.md -->
## Project

**Daily Info Digest**

A personal daily newspaper that scrapes RSS feeds, GitHub trending repos, and subreddits each morning, summarizes the content with Claude AI, and renders a polished HTML + Markdown digest. It runs automatically via GitHub Actions at 07:00 ICT and opens the result in Chrome on macOS.

**Core Value:** Each morning, every RSS article has a structured AI breakdown — core idea plus 5 key points — so the user can scan the most important insights without reading the full article.

### Constraints

- **Tech stack**: Python 3.9+, `requests` + `BeautifulSoup4` (already in requirements) for fetching/parsing
- **API cost**: Fetching full article text + structured summarization increases Claude API usage; keep calls batched where possible
- **Time budget**: GitHub Actions has a 6-hour job limit; parallel fetching keeps total time reasonable
- **Compatibility**: Must not break existing GitHub/Reddit accordion rendering (they don't use the new structured format)
<!-- GSD:project-end -->

<!-- GSD:stack-start source:codebase/STACK.md -->
## Technology Stack

## Languages
- Python 3.9.12 — all application logic (`main.py`, `src/`)
- HTML/CSS/JavaScript — self-contained inside `src/html_renderer.py` as embedded strings; generates the output HTML report
## Runtime
- CPython 3.9.12 (via Anaconda base at `/Users/huyle-hoang/opt/anaconda3/bin`)
- Virtual environment: `.venv/` (created with `python -m venv .venv`)
- pip (no version pin in repo)
- Lockfile: `requirements.txt` present (lower-bound pins only, e.g., `>=`)
- `package-lock.json` present for the single Node dependency (`chalk ^5.6.2`) — Node is not used at runtime
## Frameworks
- No web framework — `main.py` is a CLI script, run directly with `python main.py`
- Not detected — no test files, no pytest/unittest config
- No build tooling — plain Python, no setup.py / pyproject.toml
## Key Dependencies (with versions)
| Package | Installed Version | Declared Constraint | Purpose |
|---------|------------------|---------------------|---------|
| `anthropic` | 0.100.0 | `>=0.40.0` | Claude API client for AI summarization |
| `feedparser` | 6.0.12 | `>=6.0.0` | RSS/Atom feed parsing (`src/scrapers/rss.py`) |
| `requests` | 2.32.5 | `>=2.31.0` | HTTP calls to GitHub trending and Reddit JSON API |
| `beautifulsoup4` | 4.14.3 | `>=4.12.0` | HTML scraping of `github.com/trending` (`src/scrapers/github.py`) |
| `PyYAML` | 6.0.3 | `>=6.0.0` | Loading `feeds.yaml` config (`main.py`) |
## Dev Dependencies
- None declared — no dev-only dependencies
- `chalk ^5.6.2` in `package.json` is not used by any Python code; appears to be a leftover or unused utility
## Configuration
- `ANTHROPIC_API_KEY` — required env var; read automatically by `anthropic.Anthropic()` client constructor
- No `.env` file loading library (e.g., `python-dotenv`) detected; must be exported in shell
- `feeds.yaml` — runtime configuration for sources, summarization toggle, and output directory
- `requirements.txt` — dependency manifest
- `.venv/` — virtual environment (gitignored)
- `output/` — gitignored output directory; one `.md` and one `.html` per run
## Platform Requirements
- Python 3.9+
- `ANTHROPIC_API_KEY` exported in environment
- macOS assumed (auto-open uses `open -a "Google Chrome"` via `subprocess.Popen` in `main.py:100`)
- No deployment target — designed as a local CLI tool run each morning
- Output files written to `output/YYYY-MM-DD.{md,html}`
<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->
## Conventions

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
| Key | Type | Required | Set by |
|---|---|---|---|
| `title` | `str` | Yes | all scrapers |
| `url` | `str` | Yes | all scrapers |
| `summary` | `str` | Yes (may be empty) | all scrapers |
| `source` | `str` | No — added by `main.py` for RSS items | `main.py` |
| `stars` | `str` | No — GitHub only | `github.py` |
| `score` | `int` | No — Reddit only | `reddit.py` |
| `ai_summary` | `str` | No — added after summarization | `main.py` |
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
<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->
## Architecture

## Pipeline
```
```
## Key Design Decisions
## Data Shape
```python
```
- RSS items gain `"source": feed["name"]` in `main.py`.
- GitHub items include `"stars": str`.
- Reddit items include `"score": int`.
## External Dependencies
| Package        | Purpose                              |
|----------------|--------------------------------------|
| anthropic      | Claude API calls (Haiku model)       |
| feedparser     | RSS/Atom feed parsing                |
| requests       | HTTP for GitHub and Reddit scrapers  |
| beautifulsoup4 | HTML parsing for GitHub trending     |
| pyyaml         | feeds.yaml config loading            |
<!-- GSD:architecture-end -->

<!-- GSD:skills-start source:skills/ -->
## Project Skills

No project skills found. Add skills to any of: `.claude/skills/`, `.agents/skills/`, `.cursor/skills/`, `.github/skills/`, or `.codex/skills/` with a `SKILL.md` index file.
<!-- GSD:skills-end -->

<!-- GSD:workflow-start source:GSD defaults -->
## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:
- `/gsd-quick` for small fixes, doc updates, and ad-hoc tasks
- `/gsd-debug` for investigation and bug fixing
- `/gsd-execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
<!-- GSD:workflow-end -->

<!-- GSD:profile-start -->
## Developer Profile

> Profile not yet configured. Run `/gsd-profile-user` to generate your developer profile.
> This section is managed by `generate-claude-profile` -- do not edit manually.
<!-- GSD:profile-end -->
