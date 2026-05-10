import pytest
from unittest.mock import patch, MagicMock
from src.scrapers.rss import fetch_rss


def _make_entry(title="Title", link="https://example.com", summary="Summary"):
    e = MagicMock()
    e.get = lambda k, default="": {"title": title, "link": link, "summary": summary}.get(k, default)
    return e


def _make_feed(entries, bozo=False, bozo_exception=None):
    feed = MagicMock()
    feed.entries = entries
    feed.bozo = bozo
    feed.bozo_exception = bozo_exception or Exception("parse error")
    return feed


def test_returns_items():
    entries = [_make_entry(f"Title {i}", f"https://ex.com/{i}", f"Sum {i}") for i in range(3)]
    with patch("feedparser.parse", return_value=_make_feed(entries)):
        items = fetch_rss("https://ex.com/rss", max_items=5)
    assert len(items) == 3
    assert items[0]["title"] == "Title 0"
    assert items[0]["url"] == "https://ex.com/0"
    assert items[0]["summary"] == "Sum 0"


def test_respects_max_items():
    entries = [_make_entry(f"T{i}") for i in range(10)]
    with patch("feedparser.parse", return_value=_make_feed(entries)):
        items = fetch_rss("https://ex.com/rss", max_items=3)
    assert len(items) == 3


def test_raises_on_bozo_with_no_entries():
    exc = Exception("DNS failure")
    feed = _make_feed([], bozo=True, bozo_exception=exc)
    with patch("feedparser.parse", return_value=feed):
        with pytest.raises(RuntimeError, match="failed to fetch feed"):
            fetch_rss("https://ex.com/rss")


def test_bozo_with_entries_does_not_raise():
    entries = [_make_entry()]
    feed = _make_feed(entries, bozo=True)
    with patch("feedparser.parse", return_value=feed):
        items = fetch_rss("https://ex.com/rss")
    assert len(items) == 1


def test_strip_html_removes_tags_and_decodes_entities():
    entries = [_make_entry(summary="&lt;p&gt;Hello &amp;amp; &lt;b&gt;world&lt;/b&gt;&lt;/p&gt;")]
    with patch("feedparser.parse", return_value=_make_feed(entries)):
        items = fetch_rss("https://ex.com/rss")
    assert items[0]["summary"] == "Hello & world"


def test_strip_html_leaves_plain_text_unchanged():
    entries = [_make_entry(summary="Plain text only")]
    with patch("feedparser.parse", return_value=_make_feed(entries)):
        items = fetch_rss("https://ex.com/rss")
    assert items[0]["summary"] == "Plain text only"


def test_strip_html_handles_empty_summary():
    entries = [_make_entry(summary="")]
    with patch("feedparser.parse", return_value=_make_feed(entries)):
        items = fetch_rss("https://ex.com/rss")
    assert items[0]["summary"] == ""


def test_strip_html_falls_back_to_description():
    e = MagicMock()
    e.get = lambda k, default="": {"title": "T", "link": "https://ex.com", "summary": "", "description": "&lt;b&gt;desc&lt;/b&gt;"}.get(k, default)
    with patch("feedparser.parse", return_value=_make_feed([e])):
        items = fetch_rss("https://ex.com/rss")
    assert items[0]["summary"] == "desc"
