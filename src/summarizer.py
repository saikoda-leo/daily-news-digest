import json
import re
import sys
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
        raw = re.sub(r'^```\w*\s*', '', raw)
        raw = re.sub(r'\s*```$', '', raw).strip()
        highlights = json.loads(raw)
        # validate and clamp indices
        valid = [h for h in highlights if isinstance(h.get("index"), int) and 0 <= h["index"] < len(items)]
        return valid[:5]
    except Exception:
        return [{"index": i, "reason": ""} for i in range(min(5, len(items)))]


def summarize_items(section_title: str, items: list) -> list:
    """Return a 1-2 sentence AI summary for each item in one Claude call."""
    if not items:
        return []

    numbered = "\n".join(
        f"[{i}] {item['title']}\n{item.get('summary', '')[:400]}"
        for i, item in enumerate(items)
    )

    prompt = (
        f"Section: {section_title}\n\n"
        "For each article below, write a concise 1-2 sentence summary capturing the key points. "
        "Be professional and informative.\n\n"
        f"{numbered}\n\n"
        "Return a JSON array with exactly one string per article, in order:\n"
        '["Summary for article 0.", "Summary for article 1.", ...]'
    )

    try:
        response = _get_client().messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1024,
            system=[{"type": "text", "text": _SYSTEM_PROMPT, "cache_control": {"type": "ephemeral"}}],
            messages=[{"role": "user", "content": prompt}],
        )
        raw = response.content[0].text.strip()
        raw = re.sub(r'^```\w*\s*', '', raw)
        raw = re.sub(r'\s*```$', '', raw).strip()
        result = json.loads(raw)
        if isinstance(result, list) and len(result) == len(items):
            return [str(s) for s in result]
    except Exception:
        pass
    return [""] * len(items)


_EMPTY_STRUCTURED = {"core_idea": "", "key_points": ["", "", "", "", ""]}


def _safe_structured(obj: dict) -> dict:
    """Normalize one Claude-returned object: ensure types and exactly-5 key_points."""
    if not isinstance(obj, dict):
        return {"core_idea": "", "key_points": ["", "", "", "", ""]}
    kp_raw = obj.get("key_points", [])
    if isinstance(kp_raw, str):
        kp_raw = [kp_raw]
    if not isinstance(kp_raw, list):
        kp_raw = []
    kp = [str(p) for p in kp_raw[:5]]
    kp = (kp + ["", "", "", "", ""])[:5]
    return {
        "core_idea": str(obj.get("core_idea", "")),
        "key_points": kp,
    }


def summarize_items_structured(section_title: str, items: list) -> list:
    """One Claude call per section. Returns list of {"core_idea": str, "key_points": [5 strings]}.

    Per-item input: full_text[:6000] if available (>= 200 chars), otherwise summary[:1000].
    Always returns exactly len(items) entries; falls back to empty structured dicts on any failure.
    """
    if not items:
        return []

    def _input_text(item: dict) -> str:
        ft = item.get("full_text", "")
        if ft and len(ft) >= 200:
            return ft[:6000]
        return item.get("summary", "")[:1000]

    numbered = "\n\n".join(
        f"[{i}] TITLE: {item['title']}\nTEXT: {_input_text(item)}"
        for i, item in enumerate(items)
    )

    max_tokens = min(4096, len(items) * 120 + 200)

    prompt = (
        f"Section: {section_title}\n\n"
        "For each article, return a JSON array with exactly one object per article.\n"
        "Each object must have:\n"
        '  "core_idea": one sentence capturing the main point\n'
        '  "key_points": exactly 5 short bullet points (strings)\n\n'
        "Example for 2 articles:\n"
        '[{"core_idea": "OpenAI released GPT-5.", "key_points": ["point 1", "point 2", "point 3", "point 4", "point 5"]}, '
        '{"core_idea": "Google cuts 20% of staff.", "key_points": ["p1", "p2", "p3", "p4", "p5"]}]\n\n'
        "Return ONLY the JSON array, no markdown fences.\n\n"
        f"{numbered}"
    )

    try:
        response = _get_client().messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=max_tokens,
            system=[{"type": "text", "text": _SYSTEM_PROMPT, "cache_control": {"type": "ephemeral"}}],
            messages=[
                {"role": "user", "content": prompt},
                {"role": "assistant", "content": "["},
            ],
        )
        raw = "[" + response.content[0].text.strip()
        raw = re.sub(r'^```\w*\s*', '', raw)
        raw = re.sub(r'\s*```$', '', raw).strip()

        if getattr(response, "stop_reason", None) == "max_tokens":
            print(f"[warn] structured summary truncated for section {section_title}", file=sys.stderr)

        result = json.loads(raw)
        if not isinstance(result, list):
            return [{"core_idea": "", "key_points": ["", "", "", "", ""]} for _ in items]

        if len(result) != len(items):
            print(f"[warn] structured summary length mismatch: got {len(result)}, expected {len(items)}", file=sys.stderr)

        out = []
        for i in range(len(items)):
            if i < len(result):
                out.append(_safe_structured(result[i]))
            else:
                out.append({"core_idea": "", "key_points": ["", "", "", "", ""]})
        return out
    except Exception:
        return [{"core_idea": "", "key_points": ["", "", "", "", ""]} for _ in items]
