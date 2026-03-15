import pytest
from unittest.mock import patch
from memory import level3
from db import database


SAMPLE_PROFILE = """Style Name: The Aggressive Opener
Style Classification: Aggressive-Tactical
Counter-Personality: Passive-Defensive
"""


def test_should_update_at_5():
    assert level3.should_update(5) is True


def test_should_update_at_10():
    assert level3.should_update(10) is True


def test_should_update_false_at_0():
    assert level3.should_update(0) is False


def test_should_update_false_mid_cycle():
    assert level3.should_update(3) is False
    assert level3.should_update(7) is False


def test_update_profile_saves_to_db():
    with patch("memory.level3.client.call_llm", return_value=SAMPLE_PROFILE):
        level3.update_profile(["Report 1", "Report 2"])
    profile = database.get_level3_profile()
    assert profile is not None
    assert "The Aggressive Opener" in profile["style_name"]


def test_update_profile_uses_gpt4o():
    with patch("memory.level3.client.call_llm") as mock_llm:
        mock_llm.return_value = SAMPLE_PROFILE
        level3.update_profile(["Report 1"])
    assert mock_llm.call_args[0][1] == "gpt-4o"


def test_update_profile_passes_reports_to_prompt():
    with patch("memory.level3.client.call_llm") as mock_llm:
        mock_llm.return_value = SAMPLE_PROFILE
        level3.update_profile(["Player pushes pawns early.", "Loves knights."])
    prompt_sent = mock_llm.call_args[0][0]
    assert "Player pushes pawns early." in prompt_sent
    assert "Loves knights." in prompt_sent


def test_update_profile_insert_or_replace():
    with patch("memory.level3.client.call_llm", return_value=SAMPLE_PROFILE):
        level3.update_profile(["Report 1"])
        level3.update_profile(["Report 2"])
    # Should still be one row (id=1)
    assert database.get_level3_profile() is not None
    with database._conn() as c:
        count = c.execute("SELECT COUNT(*) FROM level3_profile").fetchone()[0]
    assert count == 1


def test_update_profile_passes_previous_profile():
    # Save an initial profile
    with patch("memory.level3.client.call_llm", return_value=SAMPLE_PROFILE):
        level3.update_profile(["First report"])

    with patch("memory.level3.client.call_llm") as mock_llm:
        mock_llm.return_value = SAMPLE_PROFILE
        level3.update_profile(["Second report"])
    prompt_sent = mock_llm.call_args[0][0]
    assert "The Aggressive Opener" in prompt_sent
