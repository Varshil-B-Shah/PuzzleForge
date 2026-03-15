import pytest
from ai.parser import parse_move_response, ParseError

LEGAL = ["e2e4", "d2d4", "g1f3", "b1c3"]


def test_parse_valid_response():
    uci, obs = parse_move_response("MOVE: e2e4\nOBSERVATION: Aggressive opening.", LEGAL)
    assert uci == "e2e4"
    assert "Aggressive" in obs


def test_parse_with_extra_whitespace():
    uci, obs = parse_move_response("MOVE:  g1f3 \nOBSERVATION: Knight out.", LEGAL)
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
    uci, obs = parse_move_response("move: e2e4\nobservation: Player played e4.", LEGAL)
    assert uci == "e2e4"
