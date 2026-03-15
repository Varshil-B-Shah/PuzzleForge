import random
import uuid
import streamlit as st
from chessboard.board import ChessBoard
from db import database


def _init_game():
    st.session_state.board = ChessBoard()
    st.session_state.game_id = str(uuid.uuid4())
    st.session_state.game_active = True
    st.session_state.move_count = 0


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
    # Random AI move (replaced in Task 9)
    board.push_move(random.choice(board.get_legal_moves()))
    st.session_state.move_count += 1
    if board.is_game_over():
        _end_game(board)
        return
    st.rerun()


def _end_game(board: ChessBoard):
    result = board.get_result() or "draw"
    game_number = database.get_game_count() + 1
    database.save_game(
        st.session_state.game_id, game_number, board.get_pgn(),
        result, st.session_state.move_count, "{}"
    )
    st.session_state.game_active = False
