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


# ===== summarize_items_structured tests =====

def test_summarize_items_structured_empty_returns_empty():
    assert summarizer.summarize_items_structured("Test", []) == []


def test_summarize_items_structured_returns_structured():
    items = [{"title": "A", "summary": "s"}, {"title": "B", "summary": "t"}]
    payload = '{"core_idea": "Idea A", "key_points": ["a1", "a2", "a3", "a4", "a5"]}, {"core_idea": "Idea B", "key_points": ["b1", "b2", "b3", "b4", "b5"]}]'
    mock_client = MagicMock()
    resp = _mock_response(payload)
    resp.stop_reason = "end_turn"
    mock_client.messages.create.return_value = resp
    with patch.object(summarizer, "_get_client", return_value=mock_client):
        result = summarizer.summarize_items_structured("Section", items)
    assert len(result) == 2
    assert result[0]["core_idea"] == "Idea A"
    assert result[0]["key_points"] == ["a1", "a2", "a3", "a4", "a5"]
    assert result[1]["core_idea"] == "Idea B"


def test_summarize_items_structured_uses_assistant_prefill():
    items = [{"title": "A", "summary": "s"}]
    payload = '{"core_idea": "x", "key_points": ["1","2","3","4","5"]}]'
    mock_client = MagicMock()
    resp = _mock_response(payload)
    resp.stop_reason = "end_turn"
    mock_client.messages.create.return_value = resp
    with patch.object(summarizer, "_get_client", return_value=mock_client):
        summarizer.summarize_items_structured("Section", items)
    kwargs = mock_client.messages.create.call_args.kwargs
    assert kwargs["messages"][-1] == {"role": "assistant", "content": "["}


def test_summarize_items_structured_bad_json_falls_back():
    items = [{"title": "A", "summary": ""}, {"title": "B", "summary": ""}]
    mock_client = MagicMock()
    resp = _mock_response("not valid json")
    resp.stop_reason = "end_turn"
    mock_client.messages.create.return_value = resp
    with patch.object(summarizer, "_get_client", return_value=mock_client):
        result = summarizer.summarize_items_structured("Section", items)
    assert len(result) == 2
    assert all(r == {"core_idea": "", "key_points": ["", "", "", "", ""]} for r in result)


def test_summarize_items_structured_clamps_too_many_key_points():
    items = [{"title": "A", "summary": ""}]
    payload = '{"core_idea": "x", "key_points": ["1","2","3","4","5","6","7"]}]'
    mock_client = MagicMock()
    resp = _mock_response(payload)
    resp.stop_reason = "end_turn"
    mock_client.messages.create.return_value = resp
    with patch.object(summarizer, "_get_client", return_value=mock_client):
        result = summarizer.summarize_items_structured("Section", items)
    assert len(result[0]["key_points"]) == 5
    assert result[0]["key_points"] == ["1", "2", "3", "4", "5"]


def test_summarize_items_structured_pads_too_few_key_points():
    items = [{"title": "A", "summary": ""}]
    payload = '{"core_idea": "x", "key_points": ["only one", "and two"]}]'
    mock_client = MagicMock()
    resp = _mock_response(payload)
    resp.stop_reason = "end_turn"
    mock_client.messages.create.return_value = resp
    with patch.object(summarizer, "_get_client", return_value=mock_client):
        result = summarizer.summarize_items_structured("Section", items)
    assert len(result[0]["key_points"]) == 5
    assert result[0]["key_points"] == ["only one", "and two", "", "", ""]


def test_summarize_items_structured_length_mismatch_salvages():
    items = [{"title": "A", "summary": ""}, {"title": "B", "summary": ""}, {"title": "C", "summary": ""}]
    payload = '{"core_idea": "only A", "key_points": ["1","2","3","4","5"]}]'
    mock_client = MagicMock()
    resp = _mock_response(payload)
    resp.stop_reason = "end_turn"
    mock_client.messages.create.return_value = resp
    with patch.object(summarizer, "_get_client", return_value=mock_client):
        result = summarizer.summarize_items_structured("Section", items)
    assert len(result) == 3
    assert result[0]["core_idea"] == "only A"
    assert result[1] == {"core_idea": "", "key_points": ["", "", "", "", ""]}
    assert result[2] == {"core_idea": "", "key_points": ["", "", "", "", ""]}


def test_summarize_items_structured_truncates_to_6000():
    big = "x" * 10000
    items = [{"title": "A", "summary": "fallback", "full_text": big}]
    payload = '{"core_idea": "x", "key_points": ["1","2","3","4","5"]}]'
    mock_client = MagicMock()
    resp = _mock_response(payload)
    resp.stop_reason = "end_turn"
    mock_client.messages.create.return_value = resp
    with patch.object(summarizer, "_get_client", return_value=mock_client):
        summarizer.summarize_items_structured("Section", items)
    sent_prompt = mock_client.messages.create.call_args.kwargs["messages"][0]["content"]
    # The xs in the prompt should be capped at 6000, not 10000
    assert sent_prompt.count("x") == 6000


def test_summarize_items_structured_uses_summary_when_no_full_text():
    items = [{"title": "A", "summary": "y" * 500, "full_text": ""}]
    payload = '{"core_idea": "x", "key_points": ["1","2","3","4","5"]}]'
    mock_client = MagicMock()
    resp = _mock_response(payload)
    resp.stop_reason = "end_turn"
    mock_client.messages.create.return_value = resp
    with patch.object(summarizer, "_get_client", return_value=mock_client):
        summarizer.summarize_items_structured("Section", items)
    sent_prompt = mock_client.messages.create.call_args.kwargs["messages"][0]["content"]
    assert sent_prompt.count("y") == 500  # used summary fallback


def test_summarize_items_structured_uses_summary_when_full_text_short():
    items = [{"title": "A", "summary": "y" * 500, "full_text": "tiny"}]
    payload = '{"core_idea": "x", "key_points": ["1","2","3","4","5"]}]'
    mock_client = MagicMock()
    resp = _mock_response(payload)
    resp.stop_reason = "end_turn"
    mock_client.messages.create.return_value = resp
    with patch.object(summarizer, "_get_client", return_value=mock_client):
        summarizer.summarize_items_structured("Section", items)
    sent_prompt = mock_client.messages.create.call_args.kwargs["messages"][0]["content"]
    assert "tiny" not in sent_prompt
    assert sent_prompt.count("y") == 500


def test_summarize_items_structured_max_tokens_formula():
    items = [{"title": f"T{i}", "summary": ""} for i in range(5)]
    payload = ", ".join(['{"core_idea": "x", "key_points": ["1","2","3","4","5"]}'] * 5) + "]"
    mock_client = MagicMock()
    resp = _mock_response(payload)
    resp.stop_reason = "end_turn"
    mock_client.messages.create.return_value = resp
    with patch.object(summarizer, "_get_client", return_value=mock_client):
        summarizer.summarize_items_structured("Section", items)
    assert mock_client.messages.create.call_args.kwargs["max_tokens"] == 800  # 5*120+200


def test_summarize_items_structured_max_tokens_capped():
    items = [{"title": f"T{i}", "summary": ""} for i in range(100)]
    mock_client = MagicMock()
    resp = _mock_response("garbage")
    resp.stop_reason = "end_turn"
    mock_client.messages.create.return_value = resp
    with patch.object(summarizer, "_get_client", return_value=mock_client):
        summarizer.summarize_items_structured("Section", items)
    assert mock_client.messages.create.call_args.kwargs["max_tokens"] == 4096


def test_summarize_items_structured_one_call_per_section():
    items = [{"title": f"T{i}", "summary": ""} for i in range(5)]
    mock_client = MagicMock()
    resp = _mock_response("garbage")
    resp.stop_reason = "end_turn"
    mock_client.messages.create.return_value = resp
    with patch.object(summarizer, "_get_client", return_value=mock_client):
        summarizer.summarize_items_structured("Section", items)
    assert mock_client.messages.create.call_count == 1


def test_summarize_items_structured_handles_string_key_points():
    items = [{"title": "A", "summary": ""}]
    payload = '{"core_idea": "x", "key_points": "single string instead of list"}]'
    mock_client = MagicMock()
    resp = _mock_response(payload)
    resp.stop_reason = "end_turn"
    mock_client.messages.create.return_value = resp
    with patch.object(summarizer, "_get_client", return_value=mock_client):
        result = summarizer.summarize_items_structured("Section", items)
    assert result[0]["key_points"][0] == "single string instead of list"
    assert result[0]["key_points"][1:] == ["", "", "", ""]
