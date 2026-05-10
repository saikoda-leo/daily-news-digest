# Technology Stack

**Analysis Date:** 2026-05-10

## Languages

**Primary:**
- Python 3.9.12 — all application logic (`main.py`, `src/`)

**Secondary:**
- HTML/CSS/JavaScript — self-contained inside `src/html_renderer.py` as embedded strings; generates the output HTML report

## Runtime

**Environment:**
- CPython 3.9.12 (via Anaconda base at `/Users/huyle-hoang/opt/anaconda3/bin`)
- Virtual environment: `.venv/` (created with `python -m venv .venv`)

**Package Manager:**
- pip (no version pin in repo)
- Lockfile: `requirements.txt` present (lower-bound pins only, e.g., `>=`)
- `package-lock.json` present for the single Node dependency (`chalk ^5.6.2`) — Node is not used at runtime

## Frameworks

**Core:**
- No web framework — `main.py` is a CLI script, run directly with `python main.py`

**Testing:**
- Not detected — no test files, no pytest/unittest config

**Build/Dev:**
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

**Environment:**
- `ANTHROPIC_API_KEY` — required env var; read automatically by `anthropic.Anthropic()` client constructor
- No `.env` file loading library (e.g., `python-dotenv`) detected; must be exported in shell

**Build:**
- `feeds.yaml` — runtime configuration for sources, summarization toggle, and output directory
- `requirements.txt` — dependency manifest
- `.venv/` — virtual environment (gitignored)
- `output/` — gitignored output directory; one `.md` and one `.html` per run

## Platform Requirements

**Development:**
- Python 3.9+
- `ANTHROPIC_API_KEY` exported in environment
- macOS assumed (auto-open uses `open -a "Google Chrome"` via `subprocess.Popen` in `main.py:100`)

**Production:**
- No deployment target — designed as a local CLI tool run each morning
- Output files written to `output/YYYY-MM-DD.{md,html}`

---

*Stack analysis: 2026-05-10*
