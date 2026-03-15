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
) -> tuple[str, str]:
    """Return (uci_move, observation). Retries up to 3x. Falls back to random legal move."""
    legal = board.get_legal_moves()
    prompt = prompts.build_move_prompt(
        board.get_fen(), legal,
        level1.get_context_string(), level2_report, level3_profile,
    )
    for _ in range(3):
        try:
            response = client.call_llm(prompt, "gpt-4o-mini", max_tokens=150)
            return parser.parse_move_response(response, legal)
        except (ParseError, LLMError):
            continue
    return random.choice(legal), "No observation available."
