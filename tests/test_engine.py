import pytest
from unittest.mock import patch
from chessboard.board import ChessBoard
from memory.level1 import AnnotationList
from ai.engine import get_ai_move
from ai.client import LLMError


def test_returns_legal_move():
    board = ChessBoard()
    with patch("ai.engine.client.call_llm") as mock:
        mock.return_value = "MOVE: e2e4\nOBSERVATION: Aggressive opener."
        uci, obs, _, _ = get_ai_move(board, AnnotationList(), None, None)
    assert uci == "e2e4"
    assert "Aggressive" in obs


def test_uses_gpt4o_mini_for_move_decisions():
    board = ChessBoard()
    with patch("ai.engine.client.call_llm") as mock:
        mock.return_value = "MOVE: e2e4\nOBSERVATION: Opener."
        get_ai_move(board, AnnotationList(), None, None)
    assert mock.call_args[0][1] == "gpt-4o-mini"


def test_retries_on_parse_error():
    board = ChessBoard()
    calls = [0]

    def side_effect(*a, **kw):
        calls[0] += 1
        return "MOVE: e2e4\nOBSERVATION: Done." if calls[0] >= 3 else "garbage"

    with patch("ai.engine.client.call_llm", side_effect=side_effect):
        uci, _, _, _ = get_ai_move(board, AnnotationList(), None, None)
    assert uci == "e2e4"
    assert calls[0] == 3


def test_fallback_to_random_after_3_failures():
    board = ChessBoard()
    legal = board.get_legal_moves()
    with patch("ai.engine.client.call_llm", return_value="garbage"):
        uci, obs, _, _ = get_ai_move(board, AnnotationList(), None, None)
    assert uci in legal
    assert obs == "No observation available."


def test_fallback_on_llm_error():
    board = ChessBoard()
    legal = board.get_legal_moves()
    with patch("ai.engine.client.call_llm", side_effect=LLMError("API down")):
        uci, obs, _, _ = get_ai_move(board, AnnotationList(), None, None)
    assert uci in legal


def test_new_params_accepted():
    """Engine accepts tilt_mode and target_win_rate without error."""
    board = ChessBoard()
    with patch("ai.engine.client.call_llm") as mock:
        mock.return_value = "MOVE: e2e4\nOBSERVATION: Opener.\nTRAP: no\nRECKLESS: no"
        uci, obs, is_trap, is_reckless = get_ai_move(
            board, AnnotationList(), None, None,
            player_last_move="e7e5",
            tilt_mode="exploit",
            target_win_rate=0.50,
        )
    assert uci == "e2e4"
    assert is_trap is False
    assert is_reckless is False


def test_returns_is_trap_true():
    board = ChessBoard()
    with patch("ai.engine.client.call_llm") as mock:
        mock.return_value = "MOVE: e2e4\nOBSERVATION: Subtle.\nTRAP: yes\nRECKLESS: no"
        _, _, is_trap, _ = get_ai_move(board, AnnotationList(), None, None)
    assert is_trap is True


def test_fallback_returns_false_false():
    """Fallback path returns (uci, obs, False, False)."""
    board = ChessBoard()
    legal = board.get_legal_moves()
    with patch("ai.engine.client.call_llm", return_value="garbage"):
        uci, obs, is_trap, is_reckless = get_ai_move(board, AnnotationList(), None, None)
    assert uci in legal
    assert obs == "No observation available."
    assert is_trap is False
    assert is_reckless is False
