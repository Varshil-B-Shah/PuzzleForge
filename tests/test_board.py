import pytest
from chessboard.board import ChessBoard


def test_push_legal_move_returns_true():
    assert ChessBoard().push_move("e2e4") is True


def test_push_illegal_move_returns_false():
    assert ChessBoard().push_move("e2e5") is False


def test_push_illegal_does_not_change_board():
    board = ChessBoard()
    fen = board.get_fen()
    board.push_move("e2e5")
    assert board.get_fen() == fen


def test_get_legal_moves_returns_uci():
    moves = ChessBoard().get_legal_moves()
    assert "e2e4" in moves
    assert "g1f3" in moves
    assert all(len(m) in (4, 5) for m in moves)


def test_get_fen_at_start():
    assert ChessBoard().get_fen().startswith("rnbqkbnr/pppppppp")


def test_is_game_over_false_at_start():
    assert ChessBoard().is_game_over() is False


def test_get_result_none_when_not_over():
    assert ChessBoard().get_result() is None


def test_fullmove_number_starts_at_one():
    assert ChessBoard().fullmove_number == 1


def test_fullmove_number_increments_after_black_move():
    board = ChessBoard()
    board.push_move("e2e4")
    board.push_move("e7e5")
    assert board.fullmove_number == 2


def test_get_pgn_after_moves():
    board = ChessBoard()
    board.push_move("e2e4")
    board.push_move("e7e5")
    pgn = board.get_pgn()
    assert "e4" in pgn and "e5" in pgn


def test_parse_san_to_uci():
    assert ChessBoard().parse_san_to_uci("e4") == "e2e4"


def test_parse_san_raises_on_invalid():
    with pytest.raises(ValueError):
        ChessBoard().parse_san_to_uci("Nxz9")
