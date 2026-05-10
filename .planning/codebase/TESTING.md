# Testing

## Current State

There are no automated tests in this project. The test framework (pytest) is not installed. This document defines the testing strategy to adopt as the project grows.

## Recommended Setup

```bash
pip install pytest pytest-mock responses
```

Add to `requirements-dev.txt` (create if it does not exist):
```
pytest>=8.0.0
pytest-mock>=3.12.0
responses>=0.25.0
```

## Test Layout

Mirror the `src/` tree under `tests/`:

```
tests/
  conftest.py              # shared fixtures (sample items, sample sections)
  scrapers/
    test_rss.py
    test_github.py
    test_reddit.py
  test_summarizer.py
  test_renderer.py
  test_html_renderer.py
```

Run all tests:
```bash
python -m pytest tests/
```

## What to Test

### Scrapers

Scrapers make network calls. Use the `responses` library to mock HTTP at the transport layer so tests are offline and deterministic.

**`src/scrapers/rss.py` — `fetch_rss`**

| Scenario | Expected behaviour |
|---|---|
| Feed with 3 entries, `max_items=5` | Returns list of 3 dicts, each with `title`, `url`, `summary` |
| Feed with 10 entries, `max_items=5` | Returns exactly 5 dicts |
| Entry missing `link` | `url` key is `""` (not absent, not an error) |
| Entry missing `summary` and `description` | `summary` key is `""` |
| feedparser returns empty `entries` | Returns `[]` |

**`src/scrapers/github.py` — `fetch_github_trending`**

| Scenario | Expected behaviour |
|---|---|
| Valid HTML with 5 `article.Box-row` elements | Returns 5 dicts with `title`, `url`, `summary`, `stars` |
| `max_repos=2` with 5 articles in HTML | Returns exactly 2 dicts |
| `language=""` | Requests `https://github.com/trending` (no language suffix) |
| `language="python"` | Requests `https://github.com/trending/python` |
| Article missing `<p>` description | `summary` is `""` |
| Article missing stars link | `stars` is `"?"` |
| HTTP 429 / 503 | `requests.HTTPError` propagates (caller's `_scrape` catches it) |

**`src/scrapers/reddit.py` — `fetch_reddit_posts`**

| Scenario | Expected behaviour |
|---|---|
| Valid JSON with children | Returns dicts with `title`, `url`, `summary`, `score` |
| `max_posts=3` with 5 children | Returns exactly 3 dicts |
| Child missing `title` | Skipped (not included in output) |
| `selftext` longer than 500 chars | `summary` truncated to 500 chars |
| Permalink used when `url` absent | `url` is constructed from `permalink` |
| HTTP error | `requests.HTTPError` propagates |

### Summarizer

The summarizer calls the Claude API. Mock `anthropic.Anthropic` (or patch `_get_client()`) to avoid live API calls.

**`summarize_section`**

| Scenario | Expected behaviour |
|---|---|
| Non-empty items | Returns the string from `response.content[0].text` |
| Empty items list | Returns `""` without calling the API |
| Items with no `summary` key | Treats missing summary as empty string; does not raise |

**`get_top_highlights`**

| Scenario | Expected behaviour |
|---|---|
| API returns valid JSON array of 5 | Returns list of 5 dicts with `index` and `reason` |
| API returns JSON wrapped in markdown fences | Strips fences, still parses correctly |
| `index` out of range | Invalid entries filtered out |
| API raises an exception | Falls back to `[{"index": i, "reason": ""} for i in range(min(5, len(items)))]` |
| Empty items | Returns `[]` without calling the API |

**`summarize_items`**

| Scenario | Expected behaviour |
|---|---|
| API returns correctly-sized JSON array | Returns `list[str]` of same length as input |
| Array length mismatch | Falls back to `[""] * len(items)` |
| API raises an exception | Falls back to `[""] * len(items)` |
| Empty items | Returns `[]` without calling the API |

### Renderers

**`src/renderer.py` — `render_digest`**

Test by calling the function with a temporary `Path` (use `tmp_path` pytest fixture) and asserting on the written file content.

| Scenario | Expected behaviour |
|---|---|
| Section with summary, `with_summary=True` | Blockquote `> ...` appears in output |
| Section with summary, `with_summary=False` | No blockquote in output |
| Item with `stars` | `⭐ N` appears in output |
| Item with `score` | `↑ N` appears in output |
| Item with no `url` | Title rendered as plain text, no `[]()` link |

**`src/html_renderer.py`**

Focus on the pure helper functions; avoid testing the full HTML string (too brittle).

| Function | Scenario | Expected behaviour |
|---|---|---|
| `_escape` | `&`, `<`, `>`, `"` present | All four replaced correctly |
| `_escape` | Already-safe string | Returned unchanged |
| `_slug` | Title with spaces and `/` | Spaces and slashes replaced with `-`, lowercased |
| `_source_color` | Source in list at index 2 | Returns `_SOURCE_PALETTE[2]` |
| `_source_color` | Source not in list | Returns `_SOURCE_PALETTE[0]` |
| `_render_source_tabs` | Two sources | Output contains two `data-source` buttons plus "All" |
| `render_html_digest` (integration) | Valid sections | Written file starts with `<!DOCTYPE html>`, contains the date, contains item count |

## Fixtures (conftest.py)

```python
import pytest

@pytest.fixture
def sample_rss_item():
    return {"title": "Test Article", "url": "https://example.com", "summary": "A summary.", "source": "HN"}

@pytest.fixture
def sample_section(sample_rss_item):
    return {
        "title": "Top Stories",
        "items": [sample_rss_item],
        "type": "rss",
        "summary": "Things happened today.",
        "highlights": [{"index": 0, "reason": "Very important."}],
    }
```

## Running Tests

```bash
# All tests
python -m pytest tests/

# One file
python -m pytest tests/scrapers/test_rss.py

# Verbose
python -m pytest -v tests/

# Stop on first failure
python -m pytest -x tests/
```

## Coverage Gaps

- No tests of any kind currently exist.
- All scrapers make live network calls with no mock layer — a GitHub HTML structure change or Reddit API change is only discovered when the workflow fails.
- The `main()` orchestrator is untested glue code.
- `subprocess.Popen(["open", "-a", "Google Chrome", ...])` is a platform-specific side effect that cannot be easily tested.

## What Not to Test

- The `main()` orchestrator in `main.py` — it is glue code. Integration coverage comes from running the tool manually.
- `subprocess.Popen(["open", "-a", "Google Chrome", ...])` — platform-specific side effect; skip.
- The embedded CSS/JS strings in `html_renderer.py` — visual correctness is verified by opening the output in a browser.
- `load_config()` — it is a one-liner wrapping `yaml.safe_load`; not worth a dedicated test.
