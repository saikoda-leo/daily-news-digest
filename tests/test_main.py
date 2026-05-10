import pytest
from unittest.mock import patch, MagicMock
import main


@pytest.fixture(autouse=True)
def silence_print(capsys):
    yield
    capsys.readouterr()


def test_summarize_one_rss_calls_structured():
    section = {
        "title": "Top Stories",
        "type": "rss",
        "items": [
            {"title": "A", "summary": "s", "url": "https://ex.com/a", "full_text": "x" * 300},
            {"title": "B", "summary": "s", "url": "https://ex.com/b", "full_text": ""},
        ],
    }
    structured_payload = [
        {"core_idea": "Idea A", "key_points": ["a1", "a2", "a3", "a4", "a5"]},
        {"core_idea": "Idea B", "key_points": ["b1", "b2", "b3", "b4", "b5"]},
    ]
    with patch.object(main, "summarize_section", return_value="section summary"):
        with patch.object(main, "summarize_items_structured", return_value=structured_payload) as struct_mock:
            with patch.object(main, "summarize_items") as items_mock:
                main._summarize_one(section)
    struct_mock.assert_called_once_with("Top Stories", section["items"])
    items_mock.assert_not_called()
    assert section["items"][0]["core_idea"] == "Idea A"
    assert section["items"][0]["key_points"] == ["a1", "a2", "a3", "a4", "a5"]
    assert section["items"][1]["core_idea"] == "Idea B"
    assert "ai_summary" not in section["items"][0]
    assert "ai_summary" not in section["items"][1]


def test_summarize_one_github_calls_summarize_items():
    section = {
        "title": "GitHub Trending",
        "type": "github",
        "items": [{"title": "repo1", "summary": "desc"}, {"title": "repo2", "summary": "desc"}],
    }
    with patch.object(main, "summarize_section", return_value="ok"):
        with patch.object(main, "summarize_items", return_value=["sum1", "sum2"]) as items_mock:
            with patch.object(main, "summarize_items_structured") as struct_mock:
                main._summarize_one(section)
    items_mock.assert_called_once()
    struct_mock.assert_not_called()
    assert section["items"][0]["ai_summary"] == "sum1"
    assert section["items"][1]["ai_summary"] == "sum2"
    assert "core_idea" not in section["items"][0]
    assert "key_points" not in section["items"][0]


def test_summarize_one_reddit_calls_summarize_items():
    section = {
        "title": "r/python",
        "type": "reddit",
        "items": [{"title": "post1", "summary": "desc"}],
    }
    with patch.object(main, "summarize_section", return_value="ok"):
        with patch.object(main, "summarize_items", return_value=["redditsum"]) as items_mock:
            with patch.object(main, "summarize_items_structured") as struct_mock:
                main._summarize_one(section)
    items_mock.assert_called_once()
    struct_mock.assert_not_called()
    assert section["items"][0]["ai_summary"] == "redditsum"


def test_summarize_one_no_type_defaults_to_summarize_items():
    section = {
        "title": "Other",
        "items": [{"title": "x", "summary": "y"}],
    }
    with patch.object(main, "summarize_section", return_value="ok"):
        with patch.object(main, "summarize_items", return_value=["fallback"]) as items_mock:
            with patch.object(main, "summarize_items_structured") as struct_mock:
                main._summarize_one(section)
    items_mock.assert_called_once()
    struct_mock.assert_not_called()
    assert section["items"][0]["ai_summary"] == "fallback"


def test_summarize_one_continues_on_summarize_section_failure():
    section = {
        "title": "Top Stories",
        "type": "rss",
        "items": [{"title": "A", "summary": "s", "full_text": ""}],
    }
    structured_payload = [{"core_idea": "x", "key_points": ["1", "2", "3", "4", "5"]}]
    with patch.object(main, "summarize_section", side_effect=RuntimeError("boom")):
        with patch.object(main, "summarize_items_structured", return_value=structured_payload) as struct_mock:
            main._summarize_one(section)
    struct_mock.assert_called_once()
    assert section["items"][0]["core_idea"] == "x"
    assert section["items"][0]["key_points"] == ["1", "2", "3", "4", "5"]


def test_imports_resolve():
    # Smoke test: the new symbols exist on the main module
    assert hasattr(main, "fetch_article_texts")
    assert hasattr(main, "summarize_items_structured")
    assert hasattr(main, "summarize_items")
