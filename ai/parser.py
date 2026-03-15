import re


class ParseError(Exception):
    pass


def parse_move_response(text: str, legal_moves_uci: list[str]) -> tuple[str, str]:
    """Extract MOVE and OBSERVATION from LLM response. Raises ParseError if invalid."""
    move_match = re.search(r"(?i)move:\s*([a-h][1-8][a-h][1-8][qrbn]?)", text)
    obs_match = re.search(r"(?i)observation:\s*(.+)", text)
    if not move_match:
        raise ParseError(f"No MOVE tag found: {text[:200]}")
    if not obs_match:
        raise ParseError(f"No OBSERVATION tag found: {text[:200]}")
    uci = move_match.group(1).strip().lower()
    if uci not in legal_moves_uci:
        raise ParseError(f"Move '{uci}' not in legal moves")
    return uci, obs_match.group(1).strip()
