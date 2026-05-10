import pytest
from unittest.mock import patch, MagicMock
from src.scrapers.github import fetch_github_trending

_SAMPLE_HTML = """
<article class="Box-row">
  <h2><a href="/owner/repo"> owner / repo </a></h2>
  <p>A great repository</p>
  <a href="/owner/repo/stargazers">1,234</a>
</article>
"""

_TWO_REPOS_HTML = _SAMPLE_HTML + """
<article class="Box-row">
  <h2><a href="/other/proj"> other / proj </a></h2>
  <p>Another repo</p>
  <a href="/other/proj/stargazers">567</a>
</article>
"""


def _mock_resp(html=_SAMPLE_HTML, status=200):
    r = MagicMock()
    r.text = html
    r.status_code = status
    r.raise_for_status = MagicMock()
    return r


def test_parses_repo_fields():
    with patch("requests.get", return_value=_mock_resp()):
        repos = fetch_github_trending("python", max_repos=5)
    assert len(repos) == 1
    assert "owner" in repos[0]["title"]
    assert repos[0]["url"] == "https://github.com/owner/repo"
    assert repos[0]["summary"] == "A great repository"
    assert repos[0]["stars"] == "1,234"


def test_respects_max_repos():
    with patch("requests.get", return_value=_mock_resp(_TWO_REPOS_HTML)):
        repos = fetch_github_trending(max_repos=1)
    assert len(repos) == 1


def test_canary_warning_on_empty_parse(capsys):
    with patch("requests.get", return_value=_mock_resp(html="<html><body></body></html>")):
        repos = fetch_github_trending()
    assert repos == []
    captured = capsys.readouterr()
    assert "HTML structure may have changed" in captured.err
