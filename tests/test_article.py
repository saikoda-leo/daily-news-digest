import pytest
import requests
from unittest.mock import patch, MagicMock, call
from src.scrapers.article import fetch_article_texts, _fetch_one, SKIP_URL_PATTERNS, MIN_CONTENT_CHARS


def _make_resp(text="<html><body>article</body></html>", status=200, content_type="text/html", encoding="utf-8", apparent_encoding="utf-8"):
    r = MagicMock()
    r.text = text
    r.status_code = status
    r.encoding = encoding
    r.apparent_encoding = apparent_encoding
    r.headers = {"Content-Type": content_type}
    r.raise_for_status = MagicMock()
    return r


def test_successful_fetch_sets_full_text():
    item = {"url": "https://example.com/article", "summary": "fallback"}
    long_text = "article body " * 30  # > 200 chars
    with patch("src.scrapers.article.requests.get", return_value=_make_resp()) as mg:
        with patch("src.scrapers.article.trafilatura.extract", return_value=long_text):
            _fetch_one(item)
    assert item["full_text"] == long_text
    mg.assert_called_once()
    args, kwargs = mg.call_args
    assert args[0] == "https://example.com/article"
    assert kwargs["timeout"] == (3.05, 8)
    assert "User-Agent" in kwargs["headers"]


def test_timeout_falls_back_to_empty():
    item = {"url": "https://example.com/article", "summary": "fallback"}
    with patch("src.scrapers.article.requests.get", side_effect=requests.exceptions.Timeout("slow")):
        _fetch_one(item)
    assert item["full_text"] == ""


def test_short_extracted_text_is_empty():
    item = {"url": "https://example.com/article", "summary": "fallback"}
    with patch("src.scrapers.article.requests.get", return_value=_make_resp()):
        with patch("src.scrapers.article.trafilatura.extract", return_value="too short"):
            _fetch_one(item)
    assert item["full_text"] == ""


def test_trafilatura_returns_none_is_empty():
    item = {"url": "https://example.com/article", "summary": "fallback"}
    with patch("src.scrapers.article.requests.get", return_value=_make_resp()):
        with patch("src.scrapers.article.trafilatura.extract", return_value=None):
            _fetch_one(item)
    assert item["full_text"] == ""


def test_pdf_url_skipped_no_http_call():
    item = {"url": "https://example.com/paper.pdf", "summary": "fallback"}
    with patch("src.scrapers.article.requests.get") as mg:
        _fetch_one(item)
    assert item["full_text"] == ""
    mg.assert_not_called()


def test_youtube_watch_url_skipped():
    item = {"url": "https://www.youtube.com/watch?v=abc", "summary": "fallback"}
    with patch("src.scrapers.article.requests.get") as mg:
        _fetch_one(item)
    assert item["full_text"] == ""
    mg.assert_not_called()


def test_youtu_be_url_skipped():
    item = {"url": "https://youtu.be/abc", "summary": "fallback"}
    with patch("src.scrapers.article.requests.get") as mg:
        _fetch_one(item)
    assert item["full_text"] == ""
    mg.assert_not_called()


def test_github_url_skipped():
    item = {"url": "https://github.com/user/repo", "summary": "fallback"}
    with patch("src.scrapers.article.requests.get") as mg:
        _fetch_one(item)
    assert item["full_text"] == ""
    mg.assert_not_called()


def test_empty_url_is_empty():
    item = {"url": "", "summary": "fallback"}
    with patch("src.scrapers.article.requests.get") as mg:
        _fetch_one(item)
    assert item["full_text"] == ""
    mg.assert_not_called()


def test_non_html_content_type_is_empty():
    item = {"url": "https://example.com/file", "summary": "fallback"}
    with patch("src.scrapers.article.requests.get", return_value=_make_resp(content_type="application/pdf")):
        with patch("src.scrapers.article.trafilatura.extract") as mext:
            _fetch_one(item)
    assert item["full_text"] == ""
    mext.assert_not_called()


def test_iso_encoding_gets_corrected():
    item = {"url": "https://example.com/article", "summary": "fallback"}
    resp = _make_resp(encoding="ISO-8859-1", apparent_encoding="utf-8")
    long_text = "x" * 250
    with patch("src.scrapers.article.requests.get", return_value=resp):
        with patch("src.scrapers.article.trafilatura.extract", return_value=long_text):
            _fetch_one(item)
    assert resp.encoding == "utf-8"  # mutated to apparent_encoding
    assert item["full_text"] == long_text


def test_fetch_article_texts_mutates_all_items():
    items = [
        {"url": "https://example.com/a", "summary": "s"},
        {"url": "https://example.com/b", "summary": "s"},
        {"url": "https://example.com/c", "summary": "s"},
    ]
    long_text = "x" * 250
    with patch("src.scrapers.article.requests.get", return_value=_make_resp()):
        with patch("src.scrapers.article.trafilatura.extract", return_value=long_text):
            result = fetch_article_texts(items)
    assert result is None
    for it in items:
        assert it["full_text"] == long_text


def test_fetch_article_texts_uses_thread_pool_with_10_workers():
    items = [{"url": "", "summary": ""}]
    with patch("src.scrapers.article.ThreadPoolExecutor") as MTPE:
        instance = MagicMock()
        instance.__enter__ = MagicMock(return_value=instance)
        instance.__exit__ = MagicMock(return_value=False)
        instance.map = MagicMock(return_value=iter([None]))
        MTPE.return_value = instance
        fetch_article_texts(items)
    MTPE.assert_called_once_with(max_workers=10)


def test_skip_patterns_constant():
    assert ".pdf" in SKIP_URL_PATTERNS
    assert "youtube.com/watch" in SKIP_URL_PATTERNS
    assert "youtu.be/" in SKIP_URL_PATTERNS
    assert "github.com/" in SKIP_URL_PATTERNS
    assert MIN_CONTENT_CHARS == 200
