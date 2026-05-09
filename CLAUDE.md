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
