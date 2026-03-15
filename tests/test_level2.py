import pytest
from unittest.mock import patch
from memory import level2
from db import database


def test_update_saves_report_to_db():
    with patch("memory.level2.client.call_llm", return_value="Player likes e4."):
        level2.update_after_game("obs ctx", "win", "game-1", 1)
    reports = database.get_level2_reports(1)
    assert len(reports) == 1
    assert "Player likes e4." in reports[0]


def test_update_uses_gpt4o_not_mini():
    with patch("memory.level2.client.call_llm") as mock_llm:
        mock_llm.return_value = "Some report."
        level2.update_after_game("obs ctx", "loss", "game-2", 1)
    assert mock_llm.call_args[0][1] == "gpt-4o"


def test_update_passes_previous_report_to_prompt():
    # First game creates a report
    with patch("memory.level2.client.call_llm", return_value="First report."):
        level2.update_after_game("ctx 1", "win", "game-1", 1)

    # Second game should receive first report as previous
    with patch("memory.level2.client.call_llm") as mock_llm:
        mock_llm.return_value = "Second report."
        level2.update_after_game("ctx 2", "draw", "game-2", 2)
    prompt_sent = mock_llm.call_args[0][0]
    assert "First report." in prompt_sent


def test_update_includes_result_in_prompt():
    with patch("memory.level2.client.call_llm") as mock_llm:
        mock_llm.return_value = "Report."
        level2.update_after_game("Player played d4.", "win", "game-1", 1)
    prompt_sent = mock_llm.call_args[0][0]
    assert "win" in prompt_sent


def test_update_includes_l1_context_in_prompt():
    with patch("memory.level2.client.call_llm") as mock_llm:
        mock_llm.return_value = "Report."
        level2.update_after_game("1. Move 1: pushes pawns aggressively", "loss", "game-1", 1)
    prompt_sent = mock_llm.call_args[0][0]
    assert "pushes pawns aggressively" in prompt_sent


def test_multiple_games_all_saved():
    with patch("memory.level2.client.call_llm", return_value="Report."):
        level2.update_after_game("ctx", "win", "game-1", 1)
        level2.update_after_game("ctx", "loss", "game-2", 2)
        level2.update_after_game("ctx", "draw", "game-3", 3)
    assert len(database.get_level2_reports(10)) == 3
