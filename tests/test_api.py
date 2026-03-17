import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient

from api import app
from db import database

# Six opening UCI pairs (player, ai) to make a game feel natural
_OPENING = [
    ("e2e4", "e7e5"),
    ("g1f3", "b8c6"),
    ("f1c4", "g8f6"),
    ("b1c3", "f8c5"),
    ("d2d3", "d7d6"),
    ("c1e3", "c5e3"),
]

# Three extra moves to use when we need 9 total (cooling-down tests)
_EXTRA = [
    ("f2e3", "d8d7"),
    ("d1d2", "e8g8"),
    ("e1g1", "f8e8"),
]

def _ai_response(move="e7e5", trap=False, reckless=False):
    trap_str = "yes" if trap else "no"
    reckless_str = "yes" if reckless else "no"
    return f"MOVE: {move}\nOBSERVATION: Test obs.\nTRAP: {trap_str}\nRECKLESS: {reckless_str}"


@pytest.fixture
def tc():
    db_path = database._DB_PATH  # save temp path set by conftest.py's isolated_db
    with TestClient(app) as client:
        database.init_db(db_path)  # restore after lifespan overrides it
        yield client
    database._DB_PATH = db_path  # restore after context exits


def _start(tc):
    r = tc.post("/api/game/start")
    assert r.status_code == 200
    return r.json()["game_id"]


def _move(tc, game_id, player_uci, ai_response_text):
    with patch("ai.engine.client.call_llm", return_value=ai_response_text):
        r = tc.post("/api/game/move", json={"game_id": game_id, "uci": player_uci})
    assert r.status_code == 200
    return r.json()


# ── Tilt state machine tests ──────────────────────────────────────────────────

def test_tilt_mode_none_initially(tc):
    gid = _start(tc)
    data = _move(tc, gid, "e2e4", _ai_response("e7e5", reckless=False))
    assert data["tilt_mode"] is None


def test_tilt_enters_exploit_after_3_reckless(tc):
    gid = _start(tc)
    # First 2 reckless moves — should still be None
    for p, a in _OPENING[:2]:
        data = _move(tc, gid, p, _ai_response(a, reckless=True))
    assert data["tilt_mode"] is None
    # 3rd reckless — should enter exploit
    p3, a3 = _OPENING[2]
    data = _move(tc, gid, p3, _ai_response(a3, reckless=True))
    assert data["tilt_mode"] == "exploit"


def test_tilt_stays_exploit_with_more_reckless(tc):
    gid = _start(tc)
    for p, a in _OPENING[:3]:
        data = _move(tc, gid, p, _ai_response(a, reckless=True))
    assert data["tilt_mode"] == "exploit"
    # Another reckless — should still be exploit
    p4, a4 = _OPENING[3]
    data = _move(tc, gid, p4, _ai_response(a4, reckless=True))
    assert data["tilt_mode"] == "exploit"


def test_tilt_transitions_to_cooling_after_3_calm_in_exploit(tc):
    gid = _start(tc)
    # Enter exploit
    for p, a in _OPENING[:3]:
        _move(tc, gid, p, _ai_response(a, reckless=True))
    # 3 calm moves → cooling
    for p, a in _OPENING[3:6]:
        data = _move(tc, gid, p, _ai_response(a, reckless=False))
    assert data["tilt_mode"] == "cooling"


def test_tilt_exits_to_none_after_3_calm_in_cooling(tc):
    gid = _start(tc)
    # Enter exploit
    for p, a in _OPENING[:3]:
        _move(tc, gid, p, _ai_response(a, reckless=True))
    # Enter cooling
    for p, a in _OPENING[3:6]:
        _move(tc, gid, p, _ai_response(a, reckless=False))
    # 3 more calm → None
    for p, a in _EXTRA:
        data = _move(tc, gid, p, _ai_response(a, reckless=False))
    assert data["tilt_mode"] is None


def test_reckless_resets_calm_streak(tc):
    """2 calm + 1 reckless: calm_streak resets, does NOT exit exploit to cooling on next calm."""
    gid = _start(tc)
    # Enter exploit
    for p, a in _OPENING[:3]:
        _move(tc, gid, p, _ai_response(a, reckless=True))
    # 2 calm
    _move(tc, gid, _OPENING[3][0], _ai_response(_OPENING[3][1], reckless=False))
    _move(tc, gid, _OPENING[4][0], _ai_response(_OPENING[4][1], reckless=False))
    # 1 reckless resets calm_streak
    _move(tc, gid, _OPENING[5][0], _ai_response(_OPENING[5][1], reckless=True))
    # 1 more calm — still exploit (calm_streak=1, not 3)
    data = _move(tc, gid, _EXTRA[0][0], _ai_response(_EXTRA[0][1], reckless=False))
    assert data["tilt_mode"] == "exploit"


# ── Trap tests ────────────────────────────────────────────────────────────────

def test_is_trap_false_by_default(tc):
    gid = _start(tc)
    data = _move(tc, gid, "e2e4", _ai_response("e7e5", trap=False))
    assert data["is_trap"] is False


def test_is_trap_true_when_ai_sets_trap(tc):
    gid = _start(tc)
    data = _move(tc, gid, "e2e4", _ai_response("e7e5", trap=True))
    assert data["is_trap"] is True


def test_move_log_stores_is_trap(tc):
    gid = _start(tc)
    _move(tc, gid, "e2e4", _ai_response("e7e5", trap=True))
    data = _move(tc, gid, "g1f3", _ai_response("g8f6", trap=False))
    log = data["move_log"]
    assert log[0]["is_trap"] is True
    assert log[1]["is_trap"] is False


# ── Debrief tests ─────────────────────────────────────────────────────────────

def test_debrief_returns_200_with_fallback_when_game_not_in_db(tc):
    r = tc.post("/api/game/debrief", json={"game_id": "nonexistent-id"})
    assert r.status_code == 200
    assert r.json()["analysis"] == "Analysis unavailable for this game."


def test_debrief_returns_analysis_when_game_exists(tc):
    # We need a game saved to game_history. Save one manually.
    database.save_game("test-game-123", 1, "1.e4 e5", "win", 10, "{}")
    with patch("api.ai_client.call_llm", return_value="Great game. You played well. Next time try X."):
        r = tc.post("/api/game/debrief", json={"game_id": "test-game-123"})
    assert r.status_code == 200
    assert "Great game" in r.json()["analysis"]


def test_debrief_returns_fallback_when_llm_fails(tc):
    database.save_game("test-game-456", 1, "1.e4 e5", "loss", 10, "{}")
    with patch("api.ai_client.call_llm", side_effect=Exception("LLM down")):
        r = tc.post("/api/game/debrief", json={"game_id": "test-game-456"})
    assert r.status_code == 200
    assert r.json()["analysis"] == "Analysis unavailable for this game."
