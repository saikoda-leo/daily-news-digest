# Domain Pitfalls: Full-Text Fetching + Structured Claude AI Summarization

**Domain:** News article fetching and structured LLM summarization for a daily digest
**Project:** daily-info-digest
**Researched:** 2026-05-10
**Confidence:** HIGH (grounded in existing codebase + established engineering patterns)

---

## 1. Critical Pitfalls

### Pitfall 1: Paywall and Bot-Detection Returns Poison Content

**What goes wrong:**
Sites like The Verge (Vox Media) and Tinhte.vn serve HTTP 200 with a full HTML page that contains a paywall interstitial, a cookie consent gate, or a bot-challenge (Cloudflare JS challenge, hCaptcha). BeautifulSoup `<p>` extraction on this page returns the wall's body copy — things like "You've reached your article limit", "Please enable JavaScript", or GDPR consent boilerplate. This text is short, coherent-looking, and passes a minimum-length guard unless the guard is specifically tuned. The summarizer then generates a confident-sounding "core idea" from the wall text rather than the article.

**Why it happens:**
- `requests` does not execute JavaScript. Cloudflare's "checking your browser" interstitial is a JS challenge; `requests` receives the challenge HTML and returns 200.
- The Verge uses a metered paywall. After a threshold of fetches from the same IP, it serves a subscription page while still returning 200.
- Vietnamese news sites (VnExpress, Tuổi Trẻ) increasingly show GDPR-style consent dialogs for EU-routed traffic; GitHub Actions runners use IP ranges that may be geo-routed through European AWS regions.

**Consequences:**
- Claude summarizes "Please subscribe to read more articles" as if it were news content. The digest becomes silently wrong.
- No exception is raised; the fallback to RSS summary is never triggered because fetch returned a non-empty body.

**Warning signs:**
- Extracted text is under 200 characters and contains phrases like "subscribe", "log in", "JavaScript", "cookies", "consent".
- Multiple articles from the same source produce identical or near-identical "core idea" text.
- Extracted text contains no newlines or paragraph structure.

**Prevention:**
1. After extracting text, apply a content quality check: reject if `len(text) < 150` OR if any poison phrase is present (`"subscribe"`, `"enable javascript"`, `"cookie"`, `"sign in to read"`, `"consent"`). Fall back to RSS summary on rejection.
2. Check `resp.status_code` — but note this alone is insufficient; the real check is content inspection.
3. Log the detected source domain and rejection reason to stderr so the pattern is visible.

**Component:** Article fetcher (new `src/scrapers/article_fetcher.py`). The quality check belongs inside the fetcher, not in the summarizer — keep the summarizer unaware of fetch failures.

---

### Pitfall 2: Claude Haiku Produces Fewer or More Than 5 Key Points

**What goes wrong:**
The structured breakdown prompt requests exactly 5 key points. Haiku occasionally returns 3-4 (when the article is short or repetitive) or 6-7 (when the article is rich and the model "wants" to be thorough). The existing `summarize_items` code already demonstrates this is the primary JSON reliability failure mode — the length check `len(result) == len(items)` exists precisely because Haiku miscounts batched items. The same failure mode applies to `key_points` arrays.

**Why it happens:**
- Haiku is optimized for speed and cost; it follows count instructions less reliably than Sonnet. The instruction "exactly 5" is followed correctly most of the time, but "exactly" is probabilistic for Haiku.
- Short RSS fallback text (under 200 characters) contains insufficient information for 5 distinct points. Haiku fills in with inferences or collapses points, producing 3-4.
- Very long articles give Haiku more material than fits in 5 points; it sometimes adds a 6th.

**Consequences:**
- The HTML renderer expects exactly 5 `<li>` items. Fewer: the last bullet slots are empty or missing. More: the 6th point appears outside the intended numbered list or causes a rendering assertion.
- Silent failure — no exception is raised if the array has the wrong length.

**Warning signs:**
- `len(key_points) != 5` in the parsed response.
- Any `key_points` element that is empty string or `null`.

**Prevention:**
1. After parsing the JSON response, enforce: `key_points = (key_points + [""] * 5)[:5]` — pad to 5 with empty strings if short, truncate to 5 if long.
2. Strip empty strings from the padded list before rendering; render only present points.
3. In the prompt, add a concrete example showing exactly 5 points, not just the count instruction. Concrete examples outperform count-only instructions for Haiku.
4. Set `max_tokens` high enough that a 5-point response is never truncated (512 tokens per article is sufficient for "core idea" + 5 short bullet points).

**Component:** Structured summarizer (new function in `src/summarizer.py`). The clamping/padding logic belongs immediately after `json.loads()`.

---

### Pitfall 3: Markdown-Wrapped JSON from Haiku

**What goes wrong:**
Haiku wraps JSON in triple-backtick code fences (` ```json ... ``` `) despite explicit "no markdown" instructions. `json.loads()` then raises `JSONDecodeError` on the backtick prefix.

**Why it happens:**
Haiku was fine-tuned on many examples where structured output is shown in code fences. The instruction "return ONLY JSON, no markdown" reduces but does not eliminate this behavior.

**Consequences:**
The entire structured summarization call fails and all articles in the section fall back to empty `core_idea`/`key_points`. This is the same failure mode already seen in `get_top_highlights` and `summarize_items` — both already apply `re.sub(r'^```\w*\s*', '', raw)` as a fix.

**Warning signs:**
- `JSONDecodeError` on the first character of the response.
- The raw response starts with `` ` `` or `json`.

**Prevention:**
The project already has the regex strip in `get_top_highlights` and `summarize_items`. The new structured summarizer must inherit the same pattern:
```python
raw = re.sub(r'^```(?:json)?\s*', '', raw, flags=re.IGNORECASE)
raw = re.sub(r'\s*```$', '', raw).strip()
```
Additionally, use Anthropic's `prefill` feature: send `{"` as the start of the assistant's turn to force Haiku to begin directly with JSON. This nearly eliminates markdown wrapping.

**Component:** Structured summarizer, `src/summarizer.py`. This fix is already partially implemented — extend it to the new function.

---

## 2. Moderate Pitfalls

### Pitfall 4: BeautifulSoup `<p>` Extraction Returns Navigation/Footer Garbage

**What goes wrong:**
`<p>` tags appear throughout a news page: in navigation menus, cookie banners, sidebars, related-article teasers, footer legal text, and newsletter signup prompts. A naive `soup.find_all('p')` concatenation includes all of this. For a 1000-word article, the extracted text may be 60% boilerplate from sidebar and footer `<p>` elements.

**Why it happens:**
Modern news sites use `<p>` tags semantically inconsistently. The Verge and Vietnamese news sites (VnExpress, Tuổi Trẻ) wrap navigation labels and sidebar teasers in `<p>`. Without targeting the article container (`<article>`, `<main>`, `[itemprop="articleBody"]`), extraction is unreliable.

**Consequences:**
The summarizer receives a text blob that includes phrases like "Read more", "Subscribe to our newsletter", other article titles, and footer copyright notices. The "core idea" may describe a linked sidebar story rather than the actual article.

**Warning signs:**
- Extracted text contains "Read more" or "Subscribe" multiple times.
- Text length is very high (5000+ characters) but contains many short, disconnected sentences.
- Key points reference topics unrelated to the article title.

**Prevention:**
1. Target article containers before falling back to `<p>` extraction: try `article`, `main`, `[itemprop="articleBody"]`, `[class*="article-body"]`, `[class*="post-content"]` in that priority order.
2. Filter individual `<p>` elements by minimum length (`len(p.get_text(strip=True)) > 40`) to skip nav labels and captions.
3. Truncate extracted text to 3000 characters before passing to Claude — this bounds token cost and prevents the long-boilerplate problem.

**Component:** Article fetcher (`src/scrapers/article_fetcher.py`). The container targeting and length filtering belong in the fetcher; the 3000-char truncation belongs at the boundary between fetcher and summarizer.

---

### Pitfall 5: Encoding and Charset Errors on Vietnamese News Sites

**What goes wrong:**
VnExpress and Tuổi Trẻ serve content in UTF-8 but `requests` may misdetect the charset as `ISO-8859-1` (the HTTP/1.1 default when no charset is declared in the Content-Type header). `resp.text` then contains mojibake — Vietnamese diacritical characters (ắ, ổ, ề, etc.) are decoded as Latin-1 garbage. BeautifulSoup receives the garbled string and returns garbled `<p>` text. Claude receives Vietnamese content that looks like random symbol sequences and generates nonsense summaries.

**Why it happens:**
`requests` uses `chardet` for encoding detection only if the `charset` is absent from the Content-Type header. Vietnamese sites sometimes serve `Content-Type: text/html` without `;charset=utf-8`. `requests.apparent_encoding` may correctly detect UTF-8, but `resp.text` uses `resp.encoding` (which defaults to `ISO-8859-1` per RFC 2616 when no charset is declared).

**Warning signs:**
- Extracted text contains sequences like `Ä`, `â€`, `Ã`, `Â` — typical UTF-8 decoded as Latin-1.
- `resp.encoding` is `ISO-8859-1` despite the page being Vietnamese.
- Summary contains garbled characters or unintelligible phrases.

**Prevention:**
```python
resp = requests.get(url, ...)
# Force encoding detection before accessing .text
if resp.encoding and resp.encoding.lower() in ('iso-8859-1', 'latin-1'):
    resp.encoding = resp.apparent_encoding or 'utf-8'
text = resp.text
```
Apply this unconditionally in the article fetcher. It costs nothing and prevents the problem entirely.

**Component:** Article fetcher (`src/scrapers/article_fetcher.py`). One 3-line guard at the top of the fetch function.

---

### Pitfall 6: Timeout Configuration Too Generous Causes Slow Runs

**What goes wrong:**
With 25 RSS articles (5 feeds × 5 items), parallel fetching via `ThreadPoolExecutor` spawns 25 concurrent `requests.get()` calls. If even 3-4 articles have a slow server (connection established, data draining slowly), the entire batch waits for the slowest. A `timeout=10` means the batch can stall for 10 seconds per slow article, but since they're parallel, the actual wall-clock wait is `max(all_individual_timeouts)` = 10 seconds. However, if `timeout` is a single value, `requests` applies it to both connection and read phases independently — a site that connects in 1 second but streams data slowly can hold the thread for 10 seconds on the read phase alone.

**Why it happens:**
`requests.get(url, timeout=10)` sets a 10-second timeout for each phase (connect and read) independently. A server that accepts the connection but responds slowly can consume 20 seconds total (10s connect + 10s read). With 25 parallel threads, this inflates total runtime if multiple servers are slow.

**Consequences:**
- In GitHub Actions (6-hour limit, not a practical concern), slow fetches add unnecessary runtime.
- More importantly: ThreadPoolExecutor with 25 threads all blocked on slow I/O consumes thread resources and can starve other operations.

**Warning signs:**
- Total fetching phase takes more than 15 seconds wall time.
- A specific domain consistently appears in per-article timeout warnings.

**Prevention:**
1. Use `timeout=(3.05, 8)` — 3 seconds for connection establishment, 8 seconds for read. This is the `requests` tuple form.
2. Cap the ThreadPoolExecutor thread count: `ThreadPoolExecutor(max_workers=10)` rather than the default (which is `min(32, cpu_count + 4)` — could be 25+ on GitHub Actions runners).
3. Log per-article fetch time at DEBUG level to identify consistently slow domains.

**Component:** Article fetcher and the parallel fetch orchestration in `main.py`.

---

### Pitfall 7: Hacker News URLs Point to External Sites, Not HN

**What goes wrong:**
Hacker News RSS items have `link` pointing to the _submitted URL_ (e.g., a GitHub repo, a PDF, a YouTube video, a PDF research paper), not to the HN discussion. The project already stores this as `item["url"]`. Fetching this URL to extract article text will:
- Return a GitHub repo page (no article text, just README + code)
- Return a PDF (binary content, not parseable as HTML)
- Return a YouTube watch page (no article text, just player embed)
- Return a blog post (correct — this is the intended case)

There is no content-type check before attempting BeautifulSoup extraction.

**Why it happens:**
HN aggregates links of all types. Roughly 30-40% of HN front page links on any given day point to PDFs, GitHub repos, or video content rather than text articles.

**Consequences:**
- PDF: `requests` downloads binary content; `resp.text` decodes it with wrong encoding; BeautifulSoup extracts nothing meaningful; the fallback to RSS summary activates (correct behavior, but wastes the HTTP call).
- GitHub repo: HTML is returned but `<p>` extraction yields README fragments and "Watch", "Star", "Fork" button labels.
- Large files: A PDF or video download can be large; without `stream=True` and a content-length guard, the fetcher downloads the entire file into memory.

**Warning signs:**
- URL contains `.pdf`, `/watch?v=`, `github.com/` path patterns.
- `Content-Type` response header is `application/pdf`, `video/*`, or `text/plain`.

**Prevention:**
1. Before fetching, check URL for known non-article patterns:
   ```python
   SKIP_PATTERNS = ('.pdf', 'youtube.com/watch', 'youtu.be/', 'github.com/')
   if any(p in url for p in SKIP_PATTERNS): return None  # fall back to RSS summary
   ```
2. After fetching, check `resp.headers.get('Content-Type', '')` — if not `text/html`, skip extraction.
3. Use `stream=True` with a content-length guard for all fetches to avoid downloading large binaries.

**Component:** Article fetcher (`src/scrapers/article_fetcher.py`). URL pre-check before any HTTP call; Content-Type post-check before BeautifulSoup.

---

### Pitfall 8: Truncated Claude Response When max_tokens Is Too Low

**What goes wrong:**
The structured breakdown prompt asks for `{"core_idea": "...", "key_points": ["...", "...", "...", "...", "..."]}` per article. If the section has 25 articles and the call is batched (one call for all articles in the section), `max_tokens=1024` (current value in `summarize_items`) is insufficient. At roughly 80 tokens per article (20 for core_idea + 12×5 for key_points), 25 articles need ~2000 tokens. A truncated response produces invalid JSON — `json.loads()` fails, and all 25 articles fall back to empty breakdowns.

**Why it happens:**
The current `summarize_items` sets `max_tokens=1024` and batches all items in a section into one call. The new structured format produces 3-4× more output per item than the old 1-2 sentence format.

**Consequences:**
Silent failure: all items in the section get `core_idea=""`, `key_points=[]`. No error is visible unless stderr is monitored.

**Warning signs:**
- `JSONDecodeError` on a response that ends mid-string (e.g., `"key_points": ["point one", "point tw`).
- `response.stop_reason == "max_tokens"` (Anthropic API provides this field).

**Prevention:**
1. Check `response.stop_reason` before parsing: if `"max_tokens"`, log a warning and either retry with higher `max_tokens` or fall back gracefully.
2. Calculate required `max_tokens` based on item count: `max_tokens = min(4096, len(items) * 120 + 200)`.
3. Consider per-article calls rather than batched section calls for the structured breakdown. One call per article costs more API calls but eliminates the token-truncation risk and simplifies retry logic. With 25 articles in parallel threads, per-article calls are feasible.

**Component:** Structured summarizer in `src/summarizer.py`.

---

## 3. Minor Pitfalls

### Pitfall 9: GitHub Actions IP Ranges Get Rate-Limited by News Sites

**What goes wrong:**
GitHub Actions runners use well-known AWS `us-east-1` IP ranges that are included in public IP blocklists maintained by Cloudflare, Akamai, and major news publishers. Sites like The Verge (Vox Media CDN via Fastly) and tech blogs on Cloudflare may return 403 or 429 specifically for these IP ranges, or serve a JS challenge page that a headless `requests` client cannot solve.

**Why it happens:**
News publishers actively block datacenter IP ranges to reduce scraping and comply with paywall licensing requirements. AWS IP ranges are well-documented and trivially blocked.

**Consequences:**
- The Verge articles all return 403 or a challenge page. After the content quality check (Pitfall 1), these fall back to RSS summary. This is acceptable behavior.
- The risk is if the fallback is not robust: 403 raises an `HTTPError` via `resp.raise_for_status()`, which must be caught and handled as a fallback trigger.

**Warning signs:**
- `requests.exceptions.HTTPError: 403` or `429` from specific domains consistently in CI logs.
- GitHub Actions runs produce different article quality than local runs.

**Prevention:**
1. Treat 403, 429, and 451 (legal block) response codes as fallback triggers, not fatal errors.
2. Add a realistic `User-Agent` header that matches a browser. The current `github.py` uses `"Mozilla/5.0 (compatible; daily-info-digest/1.0)"` — the `(compatible; ...)` form is recognized as a bot by many CDNs. Use a full browser UA string instead.
3. Do not retry on 403 — it will not resolve. Retry only on 429 (with backoff) and 5xx.

**Component:** Article fetcher.

---

### Pitfall 10: RSS `summary` Field Contains HTML, Not Plain Text

**What goes wrong:**
The fallback for failed article fetches uses `item.get("summary", "")` from the RSS entry. For some feeds (VnExpress, Tinhte.vn), the RSS `summary` field contains raw HTML including `<img>`, `<a>`, and `<p>` tags. When this is passed to Claude as the fallback text, Claude receives markup rather than prose. Claude handles this gracefully most of the time, but the structured output may include HTML fragments as key points.

**Why it happens:**
`feedparser` returns `entry.summary` as-is. Some RSS feeds use `<description>` with embedded HTML. The current `rss.py` already stores this raw: `"summary": entry.get("summary", "") or entry.get("description", "")`.

**Warning signs:**
- `summary` field contains `<p>`, `<img src=`, or `<a href=` substrings.
- Key points contain raw HTML tags.

**Prevention:**
Strip HTML from the fallback summary before passing to the summarizer:
```python
from html.parser import HTMLParser
import html

class _Stripper(HTMLParser):
    def __init__(self):
        super().__init__()
        self._parts = []
    def handle_data(self, d):
        self._parts.append(d)
    def get_text(self):
        return html.unescape(" ".join(self._parts))

def strip_html(text: str) -> str:
    s = _Stripper()
    s.feed(text)
    return s.get_text().strip()
```
Apply in `rss.py` at item construction time, or in the article fetcher's fallback path. No external dependency needed — `html.parser` is stdlib.

**Component:** `src/scrapers/rss.py` (at item build time) or article fetcher fallback path.

---

### Pitfall 11: Redirect Chains Land on Tracking/AMP Pages

**What goes wrong:**
Some RSS feed URLs are tracking redirect URLs (e.g., `feedproxy.google.com/~r/...`) or Google AMP URLs (`amp.theverge.com/...`). `requests` follows redirects by default, but the final destination may be an AMP page with a stripped-down HTML structure that BeautifulSoup extracts poorly. AMP pages often have `<p>` content inside `<amp-accordion>` or other custom elements that BeautifulSoup does not natively handle.

**Why it happens:**
Feed proxy services (FeedBurner was common; now Cloudflare's feed proxy, publisher redirect URLs) wrap original URLs in redirect chains. Google AMP strips standard HTML structure in favor of AMP-specific tags.

**Warning signs:**
- `resp.url` (the final URL after redirects) contains `amp`, `feedproxy`, or `cdn.ampproject.org`.
- Extracted text is very short despite the article appearing substantive.

**Prevention:**
1. After fetching, check `resp.url` (final URL after redirects). If it contains `amp`, strip `?amp=1` or replace `amp.` prefix and refetch the canonical URL.
2. Alternatively, use the RSS `link` field which is usually the canonical URL, not the AMP URL.

**Component:** Article fetcher.

---

### Pitfall 12: Claude Haiku Hallucinates Key Points Not in the Article

**What goes wrong:**
When the fetched article text is very short (under 300 characters, post-cleanup) and the summarizer uses it rather than the RSS fallback, Haiku lacks sufficient material for 5 key points and fills in with plausible-sounding but invented content. This is worse than falling back to the RSS summary, because the hallucinated content appears authoritative.

**Why it happens:**
Haiku will always attempt to complete the requested structure. With insufficient input text, it draws on its training data about the topic rather than the article content.

**Warning signs:**
- Input text is under 300 characters.
- Key points mention specific numbers, dates, or proper nouns not present in the input text.

**Prevention:**
Enforce a minimum content length threshold before using fetched text for structured summarization. If `len(cleaned_text) < 300`, fall back to RSS summary for the Claude call. The fallback is less structured but more accurate.

**Component:** Article fetcher or the boundary between fetcher and structured summarizer.

---

## Phase-Specific Warnings

| Phase Topic | Likely Pitfall | Mitigation |
|-------------|----------------|------------|
| Article fetcher implementation | HTTP 200 with poison content (paywall/bot wall) | Content quality check: reject `len < 150` or poison phrases |
| Article fetcher implementation | Non-article URLs from HN (PDFs, GitHub, video) | URL pre-check + Content-Type post-check |
| Article fetcher implementation | Vietnamese site encoding (VnExpress, Tuổi Trẻ) | Force `resp.encoding = resp.apparent_encoding` when Latin-1 detected |
| Parallel fetch orchestration | Thread exhaustion / slow servers | `timeout=(3.05, 8)`, cap workers at 10 |
| Structured summarizer | Wrong `key_points` count from Haiku | Clamp/pad to exactly 5 after parse |
| Structured summarizer | Markdown-wrapped JSON | Extend existing regex strip + use JSON prefill |
| Structured summarizer | `max_tokens` truncation on large sections | Calculate tokens by item count; check `stop_reason` |
| GitHub Actions CI | News site IP blocks on AWS ranges | Treat 403/429 as fallback trigger, not fatal error |
| RSS summary fallback | HTML markup in `summary` field | Strip HTML before passing to Claude |
| Any fetch | Redirect to AMP page | Check `resp.url` for `amp` after redirect |
| Short article text | Haiku hallucination on thin content | Minimum 300-character threshold before structured summarization |

---

## Confidence Assessment

| Area | Confidence | Basis |
|------|------------|-------|
| Paywall/bot detection | HIGH | Well-documented pattern; The Verge specifically known to block datacenter IPs; verified against existing codebase User-Agent patterns |
| BeautifulSoup extraction failures | HIGH | Established behavior; directly observable by running the fetcher against the configured feeds |
| Encoding issues on Vietnamese sites | HIGH | `requests` charset detection behavior is documented; VnExpress/Tuổi Trẻ serve Vietnamese UTF-8 content |
| Claude Haiku JSON reliability | HIGH | Pattern already demonstrated in existing `summarize_items` and `get_top_highlights` code which already includes the markdown-strip workaround |
| Timeout / performance | HIGH | `requests` timeout tuple behavior is documented; ThreadPoolExecutor behavior is standard |
| RSS-specific pitfalls (PDF, video, AMP) | HIGH | HN feed behavior well-established; AMP redirect pattern is common |
| GitHub Actions IP blocks | MEDIUM | Known pattern for datacenter IPs; specific behavior against the configured feeds not verified without running the workflow |

---

## Sources

- Existing codebase: `src/summarizer.py` (lines 67-81 demonstrate the markdown-strip pattern already in production)
- Existing codebase: `src/scrapers/github.py` (User-Agent header pattern)
- Existing codebase: `feeds.yaml` (specific sites: The Verge, VnExpress, Tuổi Trẻ, Tinhte.vn, Hacker News)
- Existing codebase: `.planning/codebase/CONCERNS.md` (R4: no retry logic; S3: Reddit User-Agent; R3: silent length mismatch)
- `requests` documentation: timeout tuple form `(connect_timeout, read_timeout)`
- `requests` documentation: `resp.encoding` vs `resp.apparent_encoding` charset detection
- Anthropic API: `stop_reason` field on message responses
