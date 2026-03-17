import pytest
from ai.parser import parse_move_response, ParseError

LEGAL = ["e2e4", "d2d4", "g1f3", "b1c3"]


def test_parse_valid_response():
    uci, obs, _, _ = parse_move_response("MOVE: e2e4\nOBSERVATION: Aggressive opening.", LEGAL)
    assert uci == "e2e4"
    assert "Aggressive" in obs


def test_parse_with_extra_whitespace():
    uci, obs, _, _ = parse_move_response("MOVE:  g1f3 \nOBSERVATION: Knight out.", LEGAL)
    assert uci == "g1f3"


def test_parse_raises_when_move_not_legal():
    with pytest.raises(ParseError):
        parse_move_response("MOVE: e2e5\nOBSERVATION: Something.", LEGAL)


def test_parse_raises_when_no_move_tag():
    with pytest.raises(ParseError):
        parse_move_response("I think e4 is best.", LEGAL)


def test_parse_raises_when_no_observation_tag():
    with pytest.raises(ParseError):
        parse_move_response("MOVE: e2e4\nSomething without the tag.", LEGAL)


def test_parse_case_insensitive():
    uci, obs, _, _ = parse_move_response("move: e2e4\nobservation: Player played e4.", LEGAL)
    assert uci == "e2e4"


def test_is_trap_true_when_trap_yes():
    uci, obs, is_trap, _ = parse_move_response(
        "MOVE: e2e4\nOBSERVATION: Obs.\nTRAP: yes", LEGAL
    )
    assert is_trap is True


def test_is_trap_false_when_trap_no():
    uci, obs, is_trap, _ = parse_move_response(
        "MOVE: e2e4\nOBSERVATION: Obs.\nTRAP: no", LEGAL
    )
    assert is_trap is False


def test_is_trap_false_when_absent():
    uci, obs, is_trap, _ = parse_move_response(
        "MOVE: e2e4\nOBSERVATION: Obs.", LEGAL
    )
    assert is_trap is False


def test_is_reckless_true_when_reckless_yes():
    _, _, _, is_reckless = parse_move_response(
        "MOVE: e2e4\nOBSERVATION: Obs.\nRECKLESS: yes", LEGAL
    )
    assert is_reckless is True


def test_is_reckless_false_when_reckless_no():
    _, _, _, is_reckless = parse_move_response(
        "MOVE: e2e4\nOBSERVATION: Obs.\nRECKLESS: no", LEGAL
    )
    assert is_reckless is False


def test_is_reckless_false_when_absent():
    _, _, _, is_reckless = parse_move_response(
        "MOVE: e2e4\nOBSERVATION: Obs.", LEGAL
    )
    assert is_reckless is False
