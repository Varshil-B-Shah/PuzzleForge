import random
import uuid
import streamlit as st
from chessboard.board import ChessBoard
from db import database
from ai import engine
from memory.level1 import AnnotationList


def _init_game():
    st.session_state.board = ChessBoard()
    st.session_state.game_id = str(uuid.uuid4())
    st.session_state.game_active = True
    st.session_state.move_count = 0
    st.session_state.level1 = AnnotationList()


def render():
    st.title("PuzzleForge Chess")
    if "board" not in st.session_state:
        _init_game()

    board: ChessBoard = st.session_state.board

    # Board display via streamlit-chess
    try:
        from streamlit_chess import chess_board
        result = chess_board(board.get_fen())
        if result and result.get("from") and result.get("to"):
            uci = result["from"] + result["to"] + result.get("promotion", "")
            _handle_player_move(uci, board)
    except ImportError:
        st.info("Enter moves in the box below (e.g. e4, Nf3, O-O).")

    # Text input fallback
    with st.form("move_form", clear_on_submit=True):
        san = st.text_input("Your move:")
        if st.form_submit_button("Move") and san and st.session_state.game_active:
            try:
                _handle_player_move(board.parse_san_to_uci(san.strip()), board)
            except ValueError:
                st.warning("Invalid move notation. Try again.")

    if not st.session_state.game_active:
        st.success(f"Game over! Result: {board.get_result()}")
        if st.button("New Game"):
            _init_game()
            st.rerun()


def _handle_player_move(uci: str, board: ChessBoard):
    if not board.push_move(uci):
        st.warning(f"Illegal move: {uci}")
        return
    if board.is_game_over():
        _end_game(board)
        return

    level1: AnnotationList = st.session_state.level1
    level2_report = _load_level2_report()
    level3_profile = _load_level3_profile()

    with st.spinner("AI is thinking..."):
        ai_uci, observation = engine.get_ai_move(board, level1, level2_report, level3_profile)

    board.push_move(ai_uci)
    level1.add_annotation(board.fullmove_number, uci, ai_uci, observation)
    if level1.should_compress(board.fullmove_number):
        level1.compress()

    st.session_state.move_count += 1
    if board.is_game_over():
        _end_game(board)
        return
    st.rerun()


def _load_level2_report() -> str | None:
    reports = database.get_level2_reports(1)
    return reports[0] if reports else None


def _load_level3_profile() -> str | None:
    profile = database.get_level3_profile()
    return profile["full_profile"] if profile else None


def _end_game(board: ChessBoard):
    from memory import level2, level3

    result = board.get_result() or "draw"
    game_number = database.get_game_count() + 1
    level1: AnnotationList = st.session_state.level1

    try:
        database.save_game(
            st.session_state.game_id, game_number, board.get_pgn(),
            result, st.session_state.move_count, "{}"
        )
    except Exception as e:
        st.warning(f"Failed to save game: {e}")
        st.session_state.game_active = False
        return

    actual_count = database.get_game_count()
    l1_ctx = level1.get_context_string()

    with st.spinner("Updating scouting report..."):
        level2.update_after_game(l1_ctx, result, st.session_state.game_id, actual_count)

    if level3.should_update(actual_count):
        with st.spinner("Updating player profile..."):
            level3.update_profile(database.get_level2_reports(5))

    st.session_state.game_active = False
