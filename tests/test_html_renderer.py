from src.html_renderer import _escape, _safe_url, _slug


def test_escape_ampersand():
    assert _escape("a & b") == "a &amp; b"


def test_escape_tags():
    assert _escape("<script>alert(1)</script>") == "&lt;script&gt;alert(1)&lt;/script&gt;"


def test_escape_quotes():
    assert _escape('"hello"') == "&quot;hello&quot;"


def test_escape_safe_string_unchanged():
    assert _escape("plain text") == "plain text"


def test_safe_url_allows_https():
    assert _safe_url("https://example.com/path?q=1") == "https://example.com/path?q=1"


def test_safe_url_allows_http():
    assert _safe_url("http://example.com") == "http://example.com"


def test_safe_url_blocks_javascript():
    assert _safe_url("javascript:alert(1)") == "#"


def test_safe_url_blocks_data_uri():
    assert _safe_url("data:text/html,<h1>xss</h1>") == "#"


def test_safe_url_blocks_ftp():
    assert _safe_url("ftp://example.com") == "#"


def test_safe_url_blocks_empty():
    assert _safe_url("") == "#"


def test_slug_spaces():
    assert _slug("GitHub Trending") == "github-trending"


def test_slug_slash():
    assert _slug("r/MachineLearning") == "r-machinelearning"
