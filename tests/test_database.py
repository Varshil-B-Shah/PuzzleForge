import pytest
import sqlite3
from db import database


def test_init_db_creates_tables():
    conn = sqlite3.connect(database._DB_PATH)
    tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
    conn.close()
    assert {"game_history", "level2_scouting", "level3_profile"} <= tables


def test_get_game_count_empty():
    assert database.get_game_count() == 0


def test_save_game_increments_count():
    database.save_game("g1", 1, "1.e4 e5", "win", 20, "{}")
    assert database.get_game_count() == 1


def test_get_game_history_returns_saved_game():
    database.save_game("g1", 1, "1.e4 e5", "win", 20, "{}")
    history = database.get_game_history()
    assert len(history) == 1
    assert history[0]["game_id"] == "g1"
    assert history[0]["result"] == "win"


def test_save_and_get_level2_report():
    database.save_level2_report("g1", 1, "win", "Player opens e4.")
    assert database.get_latest_level2_report() == "Player opens e4."


def test_get_level2_reports_ordering():
    database.save_level2_report("g1", 1, "win", "Report 1")
    database.save_level2_report("g2", 2, "loss", "Report 2")
    reports = database.get_level2_reports(2)
    assert reports[0] == "Report 2"  # most recent first
    assert reports[1] == "Report 1"


def test_get_level3_profile_returns_none_initially():
    assert database.get_level3_profile() is None


def test_save_level3_profile_creates_row():
    database.save_level3_profile("The Attacker", "Aggressive", "Profile", "Wall", 0.15, 5)
    p = database.get_level3_profile()
    assert p["style_name"] == "The Attacker"


def test_save_level3_profile_replaces_not_accumulates():
    database.save_level3_profile("Name A", "Class A", "A", "A", 0.2, 5)
    database.save_level3_profile("Name B", "Class B", "B", "B", 0.15, 10)
    assert database.get_level3_profile()["style_name"] == "Name B"
    conn = sqlite3.connect(database._DB_PATH)
    count = conn.execute("SELECT COUNT(*) FROM level3_profile").fetchone()[0]
    conn.close()
    assert count == 1


def test_user_settings_table_exists_after_init():
    conn = sqlite3.connect(database._DB_PATH)
    tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
    conn.close()
    assert "user_settings" in tables


def test_get_setting_returns_default_when_absent():
    assert database.get_setting("target_win_rate", "0.40") == "0.40"


def test_save_setting_persists():
    database.save_setting("target_win_rate", "0.55")
    assert database.get_setting("target_win_rate", "0.40") == "0.55"


def test_save_setting_overwrites():
    database.save_setting("target_win_rate", "0.30")
    database.save_setting("target_win_rate", "0.70")
    assert database.get_setting("target_win_rate", "0.40") == "0.70"


def test_reset_db_clears_user_settings():
    database.save_setting("target_win_rate", "0.65")
    database.reset_db()
    assert database.get_setting("target_win_rate", "0.40") == "0.40"
