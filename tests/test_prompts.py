from ai.prompts import (
    build_move_prompt,
    build_level1_compression_prompt,
    build_level2_update_prompt,
    build_level3_update_prompt,
)


def test_build_move_prompt_includes_fen():
    fen = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"
    assert fen in build_move_prompt(fen, ["e7e5"], None, None, None)


def test_build_move_prompt_includes_legal_moves():
    p = build_move_prompt("fen", ["e2e4", "d2d4"], None, None, None)
    assert "e2e4" in p and "d2d4" in p


def test_build_move_prompt_uci_label():
    p = build_move_prompt("fen", ["e2e4"], None, None, None)
    assert "UCI" in p or "uci" in p.lower()


def test_build_move_prompt_no_memory_generic_fallback():
    p = build_move_prompt("fen", ["e2e4"], None, None, None)
    assert "solid intermediate" in p.lower() or "No profile" in p


def test_build_move_prompt_includes_all_memory():
    p = build_move_prompt(
        "fen", ["e2e4"],
        "Move 1: Player played e4",
        "Player opens aggressively",
        "Style: The Attacker",
    )
    assert "Move 1: Player played e4" in p
    assert "Player opens aggressively" in p
    assert "Style: The Attacker" in p


def test_build_move_prompt_response_format():
    p = build_move_prompt("fen", ["e2e4"], None, None, None)
    assert "MOVE:" in p and "OBSERVATION:" in p


def test_build_level1_compression_prompt():
    p = build_level1_compression_prompt(["Move 1: obs", "Move 2: obs"])
    assert "Move 1" in p and "Move 2" in p


def test_build_level2_update_prompt():
    p = build_level2_update_prompt("Player pushed h-pawn", "Player opens e4", "win")
    assert "Player pushed h-pawn" in p and "win" in p


def test_build_level3_update_prompt():
    p = build_level3_update_prompt(["Report 1", "Report 2"], "Old profile")
    assert "Report 1" in p and "Report 2" in p and "Old profile" in p
