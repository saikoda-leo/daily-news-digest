from pathlib import Path

_SECTION_COLORS = {
    "rss":    ("linear-gradient(135deg,#667eea,#764ba2)", "#667eea"),
    "github": ("linear-gradient(135deg,#11998e,#38ef7d)", "#11998e"),
    "reddit": ("linear-gradient(135deg,#f7971e,#ffd200)", "#f7971e"),
}
_DEFAULT_COLOR = ("linear-gradient(135deg,#4facfe,#00f2fe)", "#4facfe")

_ICONS = {"rss": "📰", "github": "🐙", "reddit": "🤖"}
_DEFAULT_ICON = "📌"

# One distinct color per source name (cycles through palette)
_SOURCE_PALETTE = [
    "#667eea", "#e53e3e", "#38a169", "#d69e2e", "#3182ce",
    "#805ad5", "#dd6b20", "#319795", "#e91e8c", "#2d3748",
]


def _escape(t: str) -> str:
    return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def _safe_url(url: str) -> str:
    return url if url.startswith(("http://", "https://")) else "#"


def _slug(t: str) -> str:
    return t.lower().replace(" ", "-").replace("/", "-")


# ── CSS ──────────────────────────────────────────────────────────────────────

_CSS = """
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

:root {
  --navy: #1a1a2e;
  --gold: #e8b84b;
  --bg:   #f0f2f5;
  --card: #ffffff;
  --text: #1a202c;
  --sub:  #4a5568;
  --muted:#a0aec0;
  --border:#e2e8f0;
}

html { scroll-behavior: smooth; }
body { font-family: Georgia, "Times New Roman", serif; background: var(--bg); color: var(--text); }

/* ── Masthead ─────────────────────────────────────── */
.masthead {
  background: var(--navy);
  text-align: center;
  padding: 40px 24px 26px;
  border-bottom: 4px solid var(--gold);
}
.masthead-name {
  font-size: clamp(1.8rem, 5vw, 3rem);
  font-weight: 900;
  letter-spacing: .1em;
  text-transform: uppercase;
  color: var(--gold);
  text-shadow: 0 2px 14px rgba(232,184,75,.3);
  margin-bottom: 6px;
}
.masthead-sub {
  font-size: .88rem; color: #a0aec0; font-style: italic; margin-bottom: 14px;
}
.masthead-meta {
  display: flex; justify-content: center; flex-wrap: wrap;
  gap: 6px 20px; font-size: .78rem; color: var(--muted);
  font-family: Arial, sans-serif;
  border-top: 1px solid #2d3748; padding-top: 12px;
}

/* ── Nav pills ────────────────────────────────────── */
.section-nav {
  background: var(--navy);
  padding: 10px 24px 14px;
  display: flex; gap: 8px; flex-wrap: wrap; justify-content: center;
  border-bottom: 2px solid #2d3748;
}
.nav-pill {
  font-family: Arial, sans-serif; font-size: .74rem; font-weight: 600;
  padding: 4px 14px; border-radius: 20px; text-decoration: none;
  color: #a0aec0; border: 1.5px solid #2d3748;
  transition: color .15s, border-color .15s;
  white-space: nowrap;
}
.nav-pill:hover { color: var(--gold); border-color: var(--gold); }

/* ── Page wrapper ─────────────────────────────────── */
.page {
  max-width: 1160px; margin: 0 auto; padding: 36px 24px 64px;
}

/* ── Section divider ──────────────────────────────── */
.divider {
  font-family: Arial, sans-serif; font-size: .68rem; font-weight: 800;
  letter-spacing: .12em; text-transform: uppercase; color: var(--muted);
  display: flex; align-items: center; gap: 12px; margin-bottom: 22px;
}
.divider::before, .divider::after { content: ""; flex: 1; height: 1px; background: var(--border); }

/* ══════════════════════════════════════════════════
   TOP 5 HIGHLIGHTS
   ══════════════════════════════════════════════════ */
.highlights-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  grid-template-rows: auto auto;
  gap: 18px;
  margin-bottom: 42px;
}
/* top-2 cards span extra height visually via padding */
.hl-card-0, .hl-card-1 { grid-column: span 1; }
.hl-card-2, .hl-card-3, .hl-card-4 { grid-column: span 1; }

@media (max-width: 860px) {
  .highlights-grid { grid-template-columns: repeat(2, 1fr); }
}
@media (max-width: 560px) {
  .highlights-grid { grid-template-columns: 1fr; }
}

.hl-card {
  background: var(--card);
  border-radius: 14px;
  overflow: hidden;
  box-shadow: 0 4px 18px rgba(0,0,0,.08);
  display: flex; flex-direction: column;
  transition: transform .18s, box-shadow .18s;
  position: relative;
}
.hl-card:hover { transform: translateY(-4px); box-shadow: 0 10px 32px rgba(0,0,0,.14); }

/* rank badge */
.hl-rank {
  position: absolute; top: 14px; left: 14px;
  width: 28px; height: 28px; border-radius: 50%;
  background: rgba(0,0,0,.18);
  color: #fff; font-family: Arial, sans-serif;
  font-size: .75rem; font-weight: 900;
  display: flex; align-items: center; justify-content: center;
  backdrop-filter: blur(4px);
  z-index: 1;
}

.hl-accent-bar {
  height: 6px; width: 100%;
}

.hl-body { padding: 18px 18px 20px; flex: 1; display: flex; flex-direction: column; gap: 10px; }

.hl-source-badge {
  font-family: Arial, sans-serif; font-size: .68rem; font-weight: 700;
  letter-spacing: .06em; text-transform: uppercase;
  padding: 3px 10px; border-radius: 20px; color: #fff;
  display: inline-block; align-self: flex-start;
}

.hl-title {
  font-size: .97rem; font-weight: 700; line-height: 1.45; color: var(--text);
  text-decoration: none; display: block;
}
.hl-title:hover { color: #553c9a; text-decoration: underline; }

.hl-reason {
  font-size: .82rem; line-height: 1.6; color: var(--sub);
  font-style: italic;
  border-left: 3px solid;
  padding-left: 10px;
}

/* ══════════════════════════════════════════════════
   ALL RSS STORIES
   ══════════════════════════════════════════════════ */
.rss-section {
  background: var(--card);
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 3px 14px rgba(0,0,0,.07);
  margin-bottom: 36px;
}
.rss-section-header {
  padding: 16px 24px;
  display: flex; align-items: center; gap: 10px;
  color: #fff;
}
.rss-section-header .sec-icon { font-size: 1.3rem; }
.rss-section-header .sec-title {
  font-size: 1rem; font-weight: 700; font-family: Arial, sans-serif;
  letter-spacing: .02em; flex: 1;
}
.rss-section-header .sec-count {
  font-family: Arial, sans-serif; font-size: .7rem; font-weight: 600;
  background: rgba(255,255,255,.2); border-radius: 20px; padding: 2px 10px;
}

/* source filter tabs */
.source-tabs {
  display: flex; gap: 0; flex-wrap: wrap;
  border-bottom: 2px solid var(--border);
  padding: 0 16px;
  background: #fafbfc;
}
.source-tab {
  font-family: Arial, sans-serif; font-size: .74rem; font-weight: 600;
  padding: 10px 16px; cursor: pointer; border: none; background: none;
  color: var(--muted); border-bottom: 2px solid transparent;
  margin-bottom: -2px; transition: color .15s, border-color .15s;
  white-space: nowrap;
}
.source-tab:hover { color: var(--text); }
.source-tab.active { color: var(--text); border-bottom-color: #667eea; }

/* article list */
.article-list { list-style: none; }

.article-item {
  display: flex; align-items: flex-start; gap: 14px;
  padding: 14px 24px;
  border-bottom: 1px solid var(--border);
  transition: background .12s;
}
.article-item:last-child { border-bottom: none; }
.article-item:hover { background: #f7f9fc; }
.article-item.highlighted { background: #fffbeb; }
.article-item.hidden { display: none; }

.article-num {
  font-family: Arial, sans-serif; font-size: .72rem; font-weight: 800;
  color: var(--muted); min-width: 22px; padding-top: 2px; text-align: right;
}
.article-content { flex: 1; min-width: 0; }

.article-meta-top {
  display: flex; align-items: center; gap: 8px; margin-bottom: 5px; flex-wrap: wrap;
}
.source-chip {
  font-family: Arial, sans-serif; font-size: .64rem; font-weight: 700;
  text-transform: uppercase; letter-spacing: .06em;
  padding: 2px 9px; border-radius: 20px; color: #fff;
  flex-shrink: 0;
}
.star-badge {
  font-family: Arial, sans-serif; font-size: .7rem;
  color: var(--muted); display: flex; align-items: center; gap: 3px;
}

.article-link {
  font-size: .9rem; font-weight: 600; color: var(--text);
  text-decoration: none; line-height: 1.45; display: block;
}
.article-link:hover { color: #553c9a; text-decoration: underline; }

.highlight-tag {
  display: inline-flex; align-items: center; gap: 4px;
  font-family: Arial, sans-serif; font-size: .68rem; font-weight: 700;
  color: #b7791f; background: #fefcbf; border-radius: 20px; padding: 2px 9px;
}

/* ── Accordion (GitHub / Reddit) ─────────────────── */
.other-sections { display: flex; flex-direction: column; gap: 14px; }

.accordion {
  background: var(--card); border-radius: 14px; overflow: hidden;
  box-shadow: 0 3px 14px rgba(0,0,0,.07);
}
.accordion[open] { box-shadow: 0 6px 26px rgba(0,0,0,.11); }
.accordion > summary {
  list-style: none; cursor: pointer; user-select: none;
  padding: 14px 20px; display: flex; align-items: center; gap: 10px; color: #fff;
}
.accordion > summary::-webkit-details-marker { display: none; }
.acc-chevron { font-style: normal; font-size: .75rem; transition: transform .22s; flex-shrink: 0; }
.accordion[open] > summary .acc-chevron { transform: rotate(180deg); }
.acc-body { padding: 16px 22px 20px; animation: slideDown .2s ease-out; }
@keyframes slideDown {
  from { opacity: 0; transform: translateY(-5px); }
  to   { opacity: 1; transform: translateY(0); }
}

.acc-summary-box {
  font-size: .85rem; line-height: 1.7; color: var(--sub);
  font-style: italic; background: #f7f9fc;
  border-left: 3px solid; border-radius: 0 8px 8px 0;
  padding: 9px 14px; margin-bottom: 14px;
}
.acc-list { list-style: none; }
.acc-item {
  display: flex; align-items: flex-start; gap: 10px;
  padding: 9px 0; border-bottom: 1px solid var(--border);
  font-size: .86rem; font-family: Arial, sans-serif;
}
.acc-item:last-child { border-bottom: none; }
.acc-index {
  font-size: .68rem; font-weight: 700; min-width: 20px; height: 20px;
  border-radius: 50%; display: flex; align-items: center; justify-content: center;
  color: #fff; flex-shrink: 0; margin-top: 2px;
}
.acc-link { color: var(--text); text-decoration: none; font-weight: 600; line-height: 1.45; }
.acc-link:hover { color: #553c9a; text-decoration: underline; }
.acc-meta { font-size: .72rem; color: var(--muted); margin-top: 3px; display: flex; gap: 6px; }
.meta-badge {
  background: #edf2f7; border-radius: 20px; padding: 1px 7px;
  display: inline-flex; align-items: center; gap: 3px;
}

/* ── Per-article dropdown ─────────────────────────── */
.article-details { width: 100%; }
.article-details > summary {
  list-style: none; cursor: pointer; user-select: none;
  display: flex; align-items: center; gap: 8px;
}
.article-details > summary::-webkit-details-marker { display: none; }
.article-title-text {
  flex: 1; font-size: .9rem; font-weight: 600; color: var(--text); line-height: 1.45;
}
.article-details[open] .article-title-text { color: #553c9a; }
.article-toggle-icon {
  font-size: .6rem; color: var(--muted); transition: transform .2s; flex-shrink: 0;
}
.article-details[open] .article-toggle-icon { transform: rotate(180deg); }
.article-ai-summary {
  font-size: .83rem; line-height: 1.65; color: var(--sub);
  background: #f7f9fc; border-left: 3px solid var(--border);
  border-radius: 0 6px 6px 0; padding: 10px 14px; margin-top: 8px;
  animation: slideDown .2s ease-out;
}
.article-read-more {
  display: inline-block; margin-top: 6px;
  font-family: Arial, sans-serif; font-size: .76rem; font-weight: 600;
  color: #553c9a; text-decoration: none;
}
.article-read-more:hover { text-decoration: underline; }

/* acc-item dropdown */
.acc-details { width: 100%; }
.acc-details > summary {
  list-style: none; cursor: pointer; user-select: none;
  display: flex; align-items: center; gap: 6px;
}
.acc-details > summary::-webkit-details-marker { display: none; }
.acc-title-text { flex: 1; font-weight: 600; color: var(--text); line-height: 1.45; }
.acc-details[open] .acc-title-text { color: #553c9a; }
.acc-toggle-icon {
  font-size: .6rem; color: var(--muted); transition: transform .2s; flex-shrink: 0;
}
.acc-details[open] .acc-toggle-icon { transform: rotate(180deg); }
.acc-ai-summary {
  font-size: .8rem; line-height: 1.6; color: var(--sub);
  background: #f7f9fc; border-left: 3px solid var(--border);
  border-radius: 0 6px 6px 0; padding: 8px 12px; margin-top: 7px;
  animation: slideDown .2s ease-out;
}
.acc-read-more {
  display: inline-block; margin-top: 5px;
  font-family: Arial, sans-serif; font-size: .74rem; font-weight: 600;
  color: #553c9a; text-decoration: none;
}
.acc-read-more:hover { text-decoration: underline; }

/* ── Footer ───────────────────────────────────────── */
.footer {
  text-align: center; color: var(--muted); font-size: .74rem;
  font-family: Arial, sans-serif;
  margin-top: 40px; padding-top: 20px; border-top: 1px solid var(--border);
}
"""

# ── JavaScript ────────────────────────────────────────────────────────────────

_JS = """
(function () {
  // Source filter tabs
  var tabs = document.querySelectorAll('.source-tab');
  tabs.forEach(function (tab) {
    tab.addEventListener('click', function () {
      var src = tab.dataset.source;
      tabs.forEach(function (t) { t.classList.remove('active'); });
      tab.classList.add('active');
      document.querySelectorAll('.article-item').forEach(function (item) {
        if (src === 'all' || item.dataset.source === src) {
          item.classList.remove('hidden');
        } else {
          item.classList.add('hidden');
        }
      });
    });
  });
})();
"""

# ── HTML template ─────────────────────────────────────────────────────────────

_HTML_TEMPLATE = """\
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>Daily Digest — {date}</title>
  <style>{css}</style>
</head>
<body>

<header class="masthead">
  <div class="masthead-name">&#9733; The Daily Digest &#9733;</div>
  <div class="masthead-sub">Your personal newspaper, curated by AI</div>
  <div class="masthead-meta">
    <span>&#128197; {date}</span>
    <span>&#183;</span>
    <span>&#128279; {item_count} stories</span>
    <span>&#183;</span>
    <span>&#9733; 5 highlights</span>
  </div>
</header>

<nav class="section-nav">{nav_html}</nav>

<div class="page">

  <!-- TOP 5 HIGHLIGHTS -->
  <div class="divider" id="highlights">&#9733; Top 5 Highlights of the Day</div>
  <div class="highlights-grid">{highlights_html}</div>

  <!-- ALL RSS STORIES -->
  <div class="divider" id="top-stories">&#128240; All Stories</div>
  <div class="rss-section">
    <div class="rss-section-header" style="background:linear-gradient(135deg,#667eea,#764ba2)">
      <span class="sec-icon">&#128240;</span>
      <span class="sec-title">RSS News Feed</span>
      <span class="sec-count">{rss_count} stories</span>
    </div>
    <div class="source-tabs">{tabs_html}</div>
    <ul class="article-list">{rss_items_html}</ul>
  </div>

  <!-- OTHER SECTIONS (GitHub, Reddit) -->
  {other_html}

  <div class="footer">
    Generated by daily-info-digest &middot; Summarized with Claude AI
  </div>
</div>

<script>{js}</script>
</body>
</html>
"""


# ── Helpers ────────────────────────────────────────────────────────────────────

def _source_color(source: str, source_list: list) -> str:
    try:
        idx = source_list.index(source)
    except ValueError:
        idx = 0
    return _SOURCE_PALETTE[idx % len(_SOURCE_PALETTE)]


def _render_highlights(items: list, highlights: list, source_list: list) -> str:
    if not highlights:
        return ""
    out = ""
    for rank, h in enumerate(highlights[:5], 1):
        idx = h.get("index", 0)
        reason = h.get("reason", "")
        if idx >= len(items):
            continue
        item = items[idx]
        source = item.get("source", "")
        color = _source_color(source, source_list)
        title = _escape(item["title"])
        url = _safe_url(item.get("url", ""))
        card_class = f"hl-card hl-card-{rank - 1}"

        out += f"""
  <div class="{card_class}">
    <div class="hl-accent-bar" style="background:{color}"></div>
    <div class="hl-rank">{rank}</div>
    <div class="hl-body">
      <span class="hl-source-badge" style="background:{color}">{_escape(source)}</span>
      <a class="hl-title" href="{_escape(url)}" target="_blank" rel="noopener">{title}</a>
      {"<p class='hl-reason' style='border-color:" + color + "'>" + _escape(reason) + "</p>" if reason else ""}
    </div>
  </div>"""
    return out


def _render_source_tabs(sources: list) -> str:
    tabs = '<button class="source-tab active" data-source="all">All</button>'
    for src in sources:
        tabs += f'<button class="source-tab" data-source="{_escape(src)}">{_escape(src)}</button>'
    return tabs


def _render_rss_items(items: list, highlight_indices: set, source_list: list) -> str:
    out = ""
    for i, item in enumerate(items):
        source = item.get("source", "")
        color = _source_color(source, source_list)
        title = _escape(item["title"])
        url = _escape(_safe_url(item.get("url", "")))
        ai_summary = item.get("ai_summary", "")
        is_hl = i in highlight_indices
        hl_class = " highlighted" if is_hl else ""
        hl_tag = '<span class="highlight-tag">&#9733; Highlight</span>' if is_hl else ""

        if ai_summary:
            read_more = (
                f'<a class="article-read-more" href="{url}" target="_blank" rel="noopener">Read full article &#8599;</a>'
                if url else ""
            )
            content = f"""<details class="article-details">
          <summary><span class="article-title-text">{title}</span><i class="article-toggle-icon">&#9660;</i></summary>
          <div class="article-ai-summary" style="border-color:{color}">{_escape(ai_summary)}{read_more}</div>
        </details>"""
        elif url:
            content = f'<a class="article-link" href="{url}" target="_blank" rel="noopener">{title}</a>'
        else:
            content = f'<span class="article-link">{title}</span>'

        out += f"""
    <li class="article-item{hl_class}" data-source="{_escape(source)}">
      <span class="article-num">{i + 1}</span>
      <div class="article-content">
        <div class="article-meta-top">
          <span class="source-chip" style="background:{color}">{_escape(source)}</span>
          {hl_tag}
        </div>
        {content}
      </div>
    </li>"""
    return out


def _render_accordion(section: dict, open_first: bool) -> str:
    stype = section.get("type", "rss")
    gradient, accent = _SECTION_COLORS.get(stype, _DEFAULT_COLOR)
    icon = _ICONS.get(stype, _DEFAULT_ICON)
    slug = _slug(section["title"])
    count = len(section["items"])
    open_attr = " open" if open_first else ""

    summary_html = ""
    if section.get("summary"):
        summary_html = (
            f'<div class="acc-summary-box" style="border-color:{accent}">'
            f'{_escape(section["summary"])}</div>'
        )

    items_html = ""
    for i, item in enumerate(section["items"], 1):
        title = _escape(item["title"])
        url = _escape(_safe_url(item.get("url", "")))
        ai_summary = item.get("ai_summary", "")
        badges = []
        if "stars" in item:
            badges.append(f'<span class="meta-badge">&#11088; {_escape(str(item["stars"]))}</span>')
        if "score" in item:
            badges.append(f'<span class="meta-badge">&#8679; {item["score"]}</span>')
        meta_html = f'<div class="acc-meta">{"".join(badges)}</div>' if badges else ""

        if ai_summary:
            read_more = (
                f'<a class="acc-read-more" href="{url}" target="_blank" rel="noopener">Read full article &#8599;</a>'
                if url else ""
            )
            inner = f"""<details class="acc-details">
            <summary><span class="acc-title-text">{title}</span><i class="acc-toggle-icon">&#9660;</i></summary>
            <div class="acc-ai-summary" style="border-color:{accent}">{_escape(ai_summary)}{read_more}</div>
          </details>{meta_html}"""
        elif url:
            inner = f'<a class="acc-link" href="{url}" target="_blank" rel="noopener">{title}</a>{meta_html}'
        else:
            inner = f'<span class="acc-link">{title}</span>{meta_html}'

        items_html += f"""
      <li class="acc-item">
        <div class="acc-index" style="background:{accent}">{i}</div>
        <div style="flex:1">{inner}</div>
      </li>"""

    return f"""
  <details class="accordion"{open_attr} id="{slug}">
    <summary style="background:{gradient}">
      <span class="sec-icon">{icon}</span>
      <span class="sec-title">{_escape(section["title"])}</span>
      <span class="sec-count">{count} stories</span>
      <i class="acc-chevron">&#9660;</i>
    </summary>
    <div class="acc-body">
      {summary_html}
      <ul class="acc-list">{items_html}
      </ul>
    </div>
  </details>"""


# ── Public entry point ────────────────────────────────────────────────────────

def render_html_digest(sections: list, output_path: Path, today: str) -> None:
    rss_section    = next((s for s in sections if s.get("type") == "rss"), None)
    other_sections = [s for s in sections if s.get("type") != "rss"]

    rss_items = rss_section["items"] if rss_section else []
    highlights = rss_section.get("highlights", []) if rss_section else []
    highlight_indices = {h["index"] for h in highlights}

    # ordered unique sources
    seen: list = []
    for item in rss_items:
        src = item.get("source", "")
        if src and src not in seen:
            seen.append(src)
    source_list = seen

    # nav pills
    nav_html = '<a class="nav-pill" href="#highlights">&#9733; Highlights</a>'
    nav_html += '<a class="nav-pill" href="#top-stories">&#128240; All Stories</a>'
    for s in other_sections:
        nav_html += f'<a class="nav-pill" href="#{_slug(s["title"])}">{_ICONS.get(s.get("type"), _DEFAULT_ICON)} {_escape(s["title"])}</a>'

    highlights_html = _render_highlights(rss_items, highlights, source_list)
    tabs_html       = _render_source_tabs(source_list)
    rss_items_html  = _render_rss_items(rss_items, highlight_indices, source_list)

    other_label = ""
    other_cards = ""
    if other_sections:
        other_label = '<div class="divider">&#128279; More Sources</div>'
        other_cards = '<div class="other-sections">' + "".join(
            _render_accordion(s, i == 0) for i, s in enumerate(other_sections)
        ) + "</div>"
    other_html = other_label + other_cards

    item_count = sum(len(s["items"]) for s in sections)

    html = _HTML_TEMPLATE.format(
        date=today,
        css=_CSS,
        js=_JS,
        item_count=item_count,
        rss_count=len(rss_items),
        nav_html=nav_html,
        highlights_html=highlights_html,
        tabs_html=tabs_html,
        rss_items_html=rss_items_html,
        other_html=other_html,
    )
    output_path.write_text(html, encoding="utf-8")
