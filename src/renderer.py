from pathlib import Path


def render_digest(sections: list[dict], output_path: Path, today: str, with_summary: bool) -> None:
    lines = [f"# Daily Digest — {today}\n"]

    for section in sections:
        lines.append(f"## {section['title']}\n")

        if with_summary and section.get("summary"):
            lines.append(f"> {section['summary']}\n")

        for item in section["items"]:
            title = item["title"]
            url = item.get("url", "")
            link = f"[{title}]({url})" if url else title

            meta_parts = []
            if "stars" in item:
                meta_parts.append(f"⭐ {item['stars']}")
            if "score" in item:
                meta_parts.append(f"↑ {item['score']}")

            meta = f" — {', '.join(meta_parts)}" if meta_parts else ""
            lines.append(f"- {link}{meta}")

        lines.append("")

    output_path.write_text("\n".join(lines), encoding="utf-8")
