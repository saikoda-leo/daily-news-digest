#!/usr/bin/env python3
import subprocess
import sys
from datetime import date
from pathlib import Path

import yaml

from src.scrapers.rss import fetch_rss
from src.scrapers.github import fetch_github_trending
from src.scrapers.reddit import fetch_reddit_posts
from src.summarizer import summarize_section, get_top_highlights, summarize_items
from src.renderer import render_digest
from src.html_renderer import render_html_digest


def load_config(path: str = "feeds.yaml") -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def _scrape(label: str, fn, *args, **kwargs) -> "list[dict] | None":
    try:
        return fn(*args, **kwargs)
    except Exception as e:
        print(f"[warn] {label}: {e}", file=sys.stderr)
        return None


def main() -> None:
    config = load_config()
    sections = []

    all_rss_items = []
    for feed in config.get("rss_feeds", []):
        items = _scrape(feed["name"], fetch_rss, feed["url"], feed.get("max_items", 5))
        if items:
            for item in items:
                item["source"] = feed["name"]
            all_rss_items.extend(items)
    if all_rss_items:
        sections.append({"title": "Top Stories", "items": all_rss_items, "type": "rss"})

    gh = config.get("github_trending", {})
    for lang in gh.get("languages", [""]):
        items = _scrape(
            f"GitHub trending ({lang or 'all'})",
            fetch_github_trending,
            lang,
            gh.get("since", "daily"),
            gh.get("max_repos", 5),
        )
        if items:
            label = f"GitHub Trending — {lang}" if lang else "GitHub Trending"
            sections.append({"title": label, "items": items, "type": "github"})

    for sub in config.get("subreddits", []):
        items = _scrape(f"r/{sub['name']}", fetch_reddit_posts, sub["name"], sub.get("max_posts", 5))
        if items:
            sections.append({"title": f"r/{sub['name']}", "items": items, "type": "reddit"})

    summarize = config.get("summarization", {}).get("enabled", True)
    if summarize:
        # Pick top 5 highlights across all RSS items first
        rss_section = next((s for s in sections if s["type"] == "rss"), None)
        if rss_section:
            print("Picking top 5 highlights …", flush=True)
            try:
                rss_section["highlights"] = get_top_highlights(rss_section["items"])
            except Exception as e:
                print(f"[warn] highlights failed: {e}", file=sys.stderr)

        for section in sections:
            print(f"Summarizing: {section['title']} …", flush=True)
            try:
                section["summary"] = summarize_section(section["title"], section["items"])
            except Exception as e:
                print(f"[warn] summarization failed for {section['title']}: {e}", file=sys.stderr)

            print(f"Summarizing articles in: {section['title']} …", flush=True)
            try:
                per_item = summarize_items(section["title"], section["items"])
                for item, ai_sum in zip(section["items"], per_item):
                    item["ai_summary"] = ai_sum
            except Exception as e:
                print(f"[warn] item summary failed for {section['title']}: {e}", file=sys.stderr)

    output_dir = Path(config.get("output", {}).get("dir", "output"))
    output_dir.mkdir(exist_ok=True)
    today = date.today().isoformat()

    md_path = output_dir / f"{today}.md"
    render_digest(sections, md_path, today, summarize)
    print(f"\nDigest written → {md_path}")

    html_path = output_dir / f"{today}.html"
    render_html_digest(sections, html_path, today)
    print(f"Digest written → {html_path}")

    subprocess.Popen(["open", "-a", "Google Chrome", str(html_path)])


if __name__ == "__main__":
    main()
