import json
from typing import Optional
import anthropic

_client: Optional[anthropic.Anthropic] = None

_SYSTEM_PROMPT = (
    "You are a concise news summarizer for a personal daily digest. "
    "Given a list of articles or posts from one section, write 2-3 sentences on what is notable or trending. "
    "Focus on themes and key takeaways, not a per-item recap. Be direct and informative."
)

_HIGHLIGHT_SYSTEM_PROMPT = (
    "You are an expert news editor curating a personal daily digest. "
    "Your job is to identify the most impactful, interesting, or significant stories of the day."
)


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic()
    return _client


def summarize_section(section_title: str, items: list) -> str:
    if not items:
        return ""

    items_text = "\n".join(
        f"- {item['title']}: {item.get('summary', '')[:300]}"
        for item in items
    )

    response = _get_client().messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=256,
        system=[{"type": "text", "text": _SYSTEM_PROMPT, "cache_control": {"type": "ephemeral"}}],
        messages=[{"role": "user", "content": f"Section: {section_title}\n\nItems:\n{items_text}\n\nSummarize what is notable."}],
    )
    return response.content[0].text


def get_top_highlights(items: list) -> list:
    """Ask Claude to pick the 5 most notable items and explain why each matters.

    Returns a list of dicts: [{index, reason}, ...] where index maps into `items`.
    Falls back to first 5 items on any error.
    """
    if not items:
        return []

    numbered = "\n".join(
        f"[{i}] ({item.get('source', '?')}) {item['title']} — {item.get('summary', '')[:200]}"
        for i, item in enumerate(items)
    )

    prompt = (
        f"Here are today's news items (index, source, title, snippet):\n\n{numbered}\n\n"
        "Pick the 5 most notable or impactful stories. "
        "Return ONLY a JSON array with exactly 5 objects, no markdown:\n"
        '[{"index": 0, "reason": "One or two sentences explaining why this story matters."}, ...]'
    )

    try:
        response = _get_client().messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=512,
            system=[{"type": "text", "text": _HIGHLIGHT_SYSTEM_PROMPT, "cache_control": {"type": "ephemeral"}}],
            messages=[{"role": "user", "content": prompt}],
        )
        raw = response.content[0].text.strip()
        # strip markdown code fences if present
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        highlights = json.loads(raw)
        # validate and clamp indices
        valid = [h for h in highlights if isinstance(h.get("index"), int) and 0 <= h["index"] < len(items)]
        return valid[:5]
    except Exception:
        return [{"index": i, "reason": ""} for i in range(min(5, len(items)))]
