import pytest
from unittest.mock import MagicMock, patch
from src import summarizer


def _mock_response(text):
    msg = MagicMock()
    msg.content = [MagicMock(text=text)]
    return msg


@pytest.fixture(autouse=True)
def reset_client():
    summarizer._client = None
    yield
    summarizer._client = None


def test_summarize_section_empty_returns_empty():
    assert summarizer.summarize_section("Test", []) == ""


def test_summarize_items_empty_returns_empty():
    assert summarizer.summarize_items("Test", []) == []


def test_get_top_highlights_empty_returns_empty():
    assert summarizer.get_top_highlights([]) == []


def test_summarize_items_returns_strings():
    items = [{"title": "A", "summary": "s"}, {"title": "B", "summary": "t"}]
    mock_client = MagicMock()
    mock_client.messages.create.return_value = _mock_response('["Summary A.", "Summary B."]')
    with patch.object(summarizer, "_get_client", return_value=mock_client):
        result = summarizer.summarize_items("Section", items)
    assert result == ["Summary A.", "Summary B."]


def test_summarize_items_length_mismatch_falls_back():
    items = [{"title": "A", "summary": ""}, {"title": "B", "summary": ""}]
    mock_client = MagicMock()
    mock_client.messages.create.return_value = _mock_response('["only one item"]')
    with patch.object(summarizer, "_get_client", return_value=mock_client):
        result = summarizer.summarize_items("Section", items)
    assert result == ["", ""]


def test_get_top_highlights_valid_response():
    items = [{"title": f"Story {i}", "summary": "", "source": "HN"} for i in range(6)]
    payload = '[{"index": 0, "reason": "Top story"}, {"index": 2, "reason": "Big news"}, {"index": 1, "reason": "Interesting"}, {"index": 4, "reason": "Notable"}, {"index": 5, "reason": "Important"}]'
    mock_client = MagicMock()
    mock_client.messages.create.return_value = _mock_response(payload)
    with patch.object(summarizer, "_get_client", return_value=mock_client):
        result = summarizer.get_top_highlights(items)
    assert len(result) == 5
    assert result[0]["index"] == 0
    assert result[0]["reason"] == "Top story"


def test_get_top_highlights_filters_invalid_indices():
    items = [{"title": "Story", "summary": "", "source": "HN"}]
    payload = '[{"index": 99, "reason": "out of range"}, {"index": 0, "reason": "valid"}]'
    mock_client = MagicMock()
    mock_client.messages.create.return_value = _mock_response(payload)
    with patch.object(summarizer, "_get_client", return_value=mock_client):
        result = summarizer.get_top_highlights(items)
    assert len(result) == 1
    assert result[0]["index"] == 0
