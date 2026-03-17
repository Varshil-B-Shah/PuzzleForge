import random
from chessboard.board import ChessBoard
from memory.level1 import AnnotationList
from ai import client, prompts, parser
from ai.client import LLMError
from ai.parser import ParseError


def get_ai_move(
    board: ChessBoard,
    level1: AnnotationList,
    level2_report: str | None,
    level3_profile: str | None,
    player_last_move: str | None = None,
    tilt_mode: str | None = None,
    target_win_rate: float = 0.40,
) -> tuple[str, str, bool, bool]:
    """Returns (uci_move, observation, is_trap, is_reckless). Retries up to 3x. Falls back to random."""
    legal = board.get_legal_moves()
    prompt = prompts.build_move_prompt(
        board.get_fen(), legal,
        level1.get_context_string(), level2_report, level3_profile,
        player_last_move=player_last_move,
        tilt_mode=tilt_mode,
        target_win_rate=target_win_rate,
    )
    for _ in range(3):
        try:
            response = client.call_llm(prompt, "gpt-4o-mini", max_tokens=200)
            return parser.parse_move_response(response, legal)
        except (ParseError, LLMError):
            continue
    return random.choice(legal), "No observation available.", False, False
