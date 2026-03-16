from pathlib import Path
import streamlit.components.v1 as components

_chess_board = components.declare_component(
    "chess_board",
    path=str(Path(__file__).parent / "chess_frontend" / "build"),
)


def chess_board(fen: str, last_move: str = "", status: str = "", key: str = "chess_board"):
    """Drag-and-drop chess board (React/react-chessboard).
    Returns the UCI move string when the player drops a piece, else None.
    """
    return _chess_board(fen=fen, last_move=last_move, status=status, key=key)
