# Technology Stack — RSS Article Full-Text Extraction

**Project:** daily-info-digest (milestone: structured AI summarization)
**Researched:** 2026-05-10
**Confidence note:** WebSearch and WebFetch were blocked in this session. All findings come from
training data (knowledge cutoff August 2025) verified against the existing codebase. Confidence
levels are stated per claim. Treat MEDIUM/LOW findings as candidates for quick manual spot-checks
before committing to them.

---

## Research Question

What is the best Python approach for extracting clean article text from arbitrary news URLs,
to replace the current RSS `summary` field with full article body before sending to Claude?

---

## Recommended Stack (Additions to requirements.txt)

### Article Extraction

| Library | Version | Purpose | Confidence |
|---------|---------|---------|------------|
| `trafilatura` | `>=1.12` | Primary article body extractor | HIGH |

No other new library is needed. The existing `requests` and `beautifulsoup4` stay for fallback
and for the HTTP fetch step. `trafilatura` can accept a pre-fetched HTML string, so it slots
cleanly into the existing fetching pattern without adding a second HTTP client.

---

## Library Comparison

### trafilatura (RECOMMENDED)

**Confidence: HIGH** — well-established library, actively maintained as of mid-2025, large
corpus of academic benchmark data available.

- Purpose-built for news article extraction. Implements a content-scoring algorithm (similar to
  Mozilla Readability but in Python) that identifies the main content block by density and
  structural signals.
- Handles encoding detection, boilerplate removal (nav, footer, ads, comment threads), and
  outputs clean UTF-8 text or structured XML.
- Broad site coverage in benchmarks: consistently outperforms newspaper3k and readability-lxml
  on recall (text completeness) while keeping precision high (low boilerplate leakage).
- Python 3.8+ compatible; pure-Python with no C extension build step (unlike lxml, which
  trafilatura uses optionally but ships a pre-built wheel).
- Accepts either a URL (it fetches internally) or a pre-fetched HTML string via
  `trafilatura.extract(html_string)`. The latter is preferred here because it lets us reuse our
  own `requests.Session` with custom headers and timeouts.
- Returns `None` when extraction fails, making fallback logic trivial:
  `text = trafilatura.extract(html) or item["summary"]`
- Memory: lightweight per-call, no persistent model or large in-memory corpus. Safe for
  ThreadPoolExecutor with 10-20 concurrent workers.
- Speed: ~50-200 ms per article on server hardware (CPU-bound parsing, no I/O after fetch).

**What NOT to use instead:**

| Library | Problem | Verdict |
|---------|---------|---------|
| `newspaper3k` | Last meaningful release was 0.2.8 in 2018; Python 3.10+ compatibility issues; depends on lxml and NLTK which add heavy setup; known broken on many modern news sites | DO NOT USE |
| `newspaper4k` | A 2023 fork of newspaper3k fixing Python 3.10+ compat. Active but has much smaller user base and fewer benchmark results than trafilatura. Not worth the switching cost when trafilatura is better. | Skip unless trafilatura fails a specific site |
| `readability-lxml` | Port of Mozilla's Readability; good precision but lower recall (often truncates articles). No active development. Better than raw BS4 but worse than trafilatura. No compelling reason to add it. | Skip |
| `goose3` | Fork of Goose2; decent quality but slower than trafilatura and has fallen behind on maintenance. Adds Pillow as dependency (image processing). Not relevant to this use case. | Skip |
| Raw `requests` + `BeautifulSoup4` `<p>` extraction | Fast to write but produces garbage on sites that use `<div>` soup, React-rendered content, or wrapper paragraphs in nav/footer. Unacceptable recall on modern news sites. | Use only as last-resort fallback, not primary |

---

## JavaScript-Rendered Pages (SPAs)

**Confidence: HIGH** — this is a clear architectural constraint.

Most major news sources (NYT, The Verge, Wired, TechCrunch, Reuters, BBC) serve their article
body in server-side HTML. The JavaScript they load is for interactivity, not for the article
content itself. `trafilatura` (and `requests`) handles these fine.

A minority of sites use client-side rendering (CSR) where article text is loaded by JS after
page load (e.g., some Substack configurations, some newsletter platforms). These sites will
return near-empty HTML to a plain HTTP GET.

**Recommendation: skip JS-heavy sites gracefully, do not add a headless browser.**

Rationale:
1. Adding Playwright or Selenium adds 150-300 MB of binary dependencies, complicates the GitHub
   Actions environment, and adds 3-10 seconds per article.
2. The fallback to `item["summary"]` from the RSS feed already provides a usable short text for
   these sites. Claude can produce a useful structured breakdown from RSS summary alone.
3. The PROJECT.md explicitly lists "Paywall bypass" as Out of Scope, and JS-heavy-site handling
   has the same cost/benefit profile.

Detection heuristic (implement in the fetcher):

```python
MIN_CONTENT_CHARS = 200

def fetch_article_text(url: str, rss_summary: str) -> str:
    try:
        resp = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        resp.raise_for_status()
        text = trafilatura.extract(resp.text, include_comments=False, include_tables=False)
        if text and len(text) >= MIN_CONTENT_CHARS:
            return text
    except Exception:
        pass
    return rss_summary  # fallback
```

If `trafilatura.extract()` returns `None` or fewer than 200 characters, the page is either
JS-rendered, paywalled, or bot-blocked. Fall back to RSS summary silently — no error needed.

---

## Paywall and Bot-Blocking Detection

**Confidence: HIGH** — this is standard HTTP behavior, no special library needed.

Common signals that content is inaccessible:

| Signal | What happens | How to detect |
|--------|-------------|---------------|
| Soft paywall | Page loads, article text is truncated or replaced with subscription CTA | `trafilatura` extracts CTA text; short character count triggers fallback |
| Hard paywall | HTTP 403 or redirect to `/subscribe` | `requests` raises `HTTPError` or text is very short |
| Bot detection (Cloudflare, etc.) | HTTP 403, 429, or HTML contains "Please verify you are human" | HTTPError or short extracted text |
| Login wall | Redirect to `/login` | Extracted text < threshold |

The `MIN_CONTENT_CHARS = 200` check handles all of these uniformly. No special paywall-detection
library is needed. Do NOT attempt to bypass paywalls — it is Out of Scope per PROJECT.md.

---

## Text Truncation Before Sending to Claude

**Confidence: HIGH** — based on Claude Haiku context window and the structured prompt format.

Claude Haiku (claude-haiku-4-5) has a 200K token context window, but sending full articles
is wasteful for a digest. Practical constraints:

- Average news article: 500-1500 words (~700-2000 tokens)
- With 5-10 articles per section, a batched section call stays well under 10K tokens even
  without truncation
- Truncation is still important as a safety net against unusually long articles (long-form
  journalism, technical deep-dives)

**Recommended strategy: truncate to first 1500 tokens (~1100 words / ~6000 characters).**

Implementation:

```python
MAX_CHARS = 6000

def truncate(text: str) -> str:
    return text[:MAX_CHARS] if len(text) > MAX_CHARS else text
```

Character-based truncation is simpler than token-based (avoids adding `tiktoken` as a
dependency) and is conservative enough. At roughly 4 characters per token, 6000 chars maps
to ~1500 tokens. The first 1500 tokens of an article reliably contain the lede, the core
claim, and the main supporting evidence — exactly what Claude needs for a structured summary.

Do NOT use sentence-aware truncation (e.g., cutting at the last period before the limit).
It adds complexity for marginal quality gain. Claude handles mid-sentence truncation gracefully.

---

## Final Stack Decision

```
# Add to requirements.txt
trafilatura==1.12.2   # or latest stable >=1.12

# No new additions needed:
# - requests==2.32.5 (already present, used for HTTP fetch)
# - beautifulsoup4==4.14.3 (already present, available as BS4 fallback if needed)
```

The fetcher function fits in the existing `src/scrapers/rss.py` or a new
`src/scrapers/article_fetcher.py` (preferred for separation of concerns). It takes a URL and
RSS summary string, returns a text string, and never raises — all errors fall back silently.

---

## What NOT to Add

| Library | Reason to exclude |
|---------|------------------|
| `playwright` / `selenium` | JS rendering overkill; heavy binary dependency; Out of Scope |
| `newspaper3k` | Unmaintained, broken on Python 3.10+ |
| `goose3` | Worse than trafilatura, adds Pillow dependency |
| `readability-lxml` | Lower recall than trafilatura, no active development |
| `tiktoken` | Token counting is overkill; char-based truncation is sufficient |
| `httpx` | requests is already present; no benefit for synchronous ThreadPoolExecutor use |

---

## Confidence Assessment

| Area | Level | Reason |
|------|-------|--------|
| trafilatura recommendation | HIGH | Consistent benchmark winner across multiple independent studies through 2025; actively maintained |
| newspaper3k deprecation | HIGH | Last release 2018, Python 3.10+ incompatibility is well-documented |
| JS-page fallback strategy | HIGH | Standard HTTP behavior; architectural reasoning is sound regardless of specific library |
| Paywall handling via char threshold | HIGH | Simple heuristic; confirmed effective pattern in similar digest tools |
| trafilatura exact version `1.12.2` | MEDIUM | Training data suggests 1.12.x series is current; verify exact version via `pip index versions trafilatura` before pinning |
| Character-to-token ratio (~4 chars/token) | MEDIUM | Standard approximation for English prose; actual ratio varies by content |

---

## Sources

- trafilatura GitHub repository and documentation (training data, confirmed active through August 2025)
- newspaper3k PyPI page (last release 0.2.8, 2018)
- Empirical benchmarks from Barbaresi (2021) "Trafilatura: A Web Scraping Library and
  Command-Line Tool for Text Discovery and Extraction" — establishes recall/precision superiority
- PROJECT.md constraints: Python 3.9+, requests + BS4 already in stack, paywall bypass Out of Scope
