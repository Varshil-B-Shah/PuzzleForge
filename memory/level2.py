from ai import client
from ai.prompts import build_level2_update_prompt
from db import database


def update_after_game(l1_context: str, result: str, game_id: str, game_number: int) -> None:
    """Build an updated scouting report and persist it after each game."""
    previous_report = database.get_latest_level2_report()
    prompt = build_level2_update_prompt(l1_context, previous_report, result)
    report_text = client.call_llm(prompt, "gpt-4o", max_tokens=500)
    database.save_level2_report(game_id, game_number, result, report_text)
