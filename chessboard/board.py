import chess
import chess.pgn
import io


class ChessBoard:
    def __init__(self):
        self._board = chess.Board()

    def push_move(self, uci: str) -> bool:
        try:
            move = chess.Move.from_uci(uci)
            if move not in self._board.legal_moves:
                return False
            self._board.push(move)
            return True
        except (ValueError, AssertionError):
            return False

    def get_legal_moves(self) -> list[str]:
        return [m.uci() for m in self._board.legal_moves]

    def get_fen(self) -> str:
        return self._board.fen()

    def is_game_over(self) -> bool:
        return self._board.is_game_over()

    def get_result(self) -> str | None:
        if not self._board.is_game_over():
            return None
        r = self._board.result()
        return "win" if r == "1-0" else ("loss" if r == "0-1" else "draw")

    def get_pgn(self) -> str:
        game = chess.pgn.Game.from_board(self._board)
        exporter = chess.pgn.StringExporter(headers=False, variations=False, comments=False)
        return game.accept(exporter)

    def parse_san_to_uci(self, san: str) -> str:
        """Convert SAN (e.g. 'Nf3') to UCI (e.g. 'g1f3'). Raises ValueError on bad input."""
        return self._board.parse_san(san).uci()

    @property
    def fullmove_number(self) -> int:
        return self._board.fullmove_number
