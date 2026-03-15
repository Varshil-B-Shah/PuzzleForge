import re
from ai import client
from ai.prompts import build_level3_update_prompt
from db import database


def should_update(completed_game_count: int) -> bool:
    return completed_game_count > 0 and completed_game_count % 5 == 0


def update_profile(l2_reports: list[str]) -> None:
    """Build a deep player profile from recent scouting reports and persist it (INSERT OR REPLACE id=1)."""
    existing = database.get_level3_profile()
    previous_profile = existing["full_profile"] if existing else None

    prompt = build_level3_update_prompt(l2_reports, previous_profile)
    profile_text = client.call_llm(prompt, "gpt-4o", max_tokens=600)

    style_name = _extract(profile_text, r"Style Name:\s*(.+)") or "Unknown"
    style_class = _extract(profile_text, r"Style Classification:\s*(.+)") or "Unknown"
    counter_strategy = _extract(profile_text, r"Counter-Personality:\s*(.+)") or ""

    database.save_level3_profile(
        style_name=style_name,
        style_class=style_class,
        full_profile=profile_text,
        counter_strategy=counter_strategy,
        target_win_rate=0.15,
        games_analyzed=len(l2_reports),
    )


def _extract(text: str, pattern: str) -> str | None:
    m = re.search(pattern, text)
    return m.group(1).strip() if m else None
