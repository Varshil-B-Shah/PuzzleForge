import re


class ParseError(Exception):
    pass


def parse_move_response(text: str, legal_moves_uci: list[str]) -> tuple[str, str, bool, bool]:
    """Extract MOVE, OBSERVATION, TRAP, RECKLESS from LLM response.

    Returns (uci, observation, is_trap, is_reckless).
    TRAP and RECKLESS default to False if absent.
    Raises ParseError if move not in legal_moves_uci.
    """
    move_match = re.search(r"(?i)move:\s*([a-h][1-8][a-h][1-8][qrbn]?)", text)
    obs_match = re.search(r"(?i)observation:\s*(.+)", text)
    if not move_match:
        raise ParseError(f"No MOVE tag found: {text[:200]}")
    if not obs_match:
        raise ParseError(f"No OBSERVATION tag found: {text[:200]}")
    uci = move_match.group(1).strip().lower()
    if uci not in legal_moves_uci:
        raise ParseError(f"Move '{uci}' not in legal moves")
    is_trap = bool(re.search(r"(?i)trap:\s*yes", text))
    is_reckless = bool(re.search(r"(?i)reckless:\s*yes", text))
    return uci, obs_match.group(1).strip(), is_trap, is_reckless
