def build_move_prompt(fen, legal_moves_uci, level1_ctx, level2_report, level3_profile, player_last_move=None,
                      tilt_mode=None, target_win_rate=0.40):
    profile = level3_profile or "No profile yet. Play solid intermediate chess with occasional natural mistakes."
    scouting = level2_report or "No scouting data yet."
    l1 = level1_ctx or "No annotations yet — game just started."
    moves_str = ", ".join(legal_moves_uci)
    strategy = (
        "Execute the counter-strategy described in your player profile."
        if level3_profile else
        "Play balanced intermediate chess."
    )
    personality = (
        "Embody the counter-personality described in your player profile."
        if level3_profile else
        "Balanced."
    )

    last_move_line = f"\nPLAYER'S LAST MOVE: {player_last_move}" if player_last_move else ""

    return f"""PLAYER PROFILE:
{profile}

SCOUTING REPORT:
{scouting}

THIS GAME SO FAR:
{l1}{last_move_line}

CURRENT BOARD (FEN):
{fen}

LEGAL MOVES (UCI format):
{moves_str}

YOUR STRATEGIC GOAL:
{strategy}

YOUR PERSONALITY:
{personality}

Choose exactly ONE move from the legal moves list above (UCI format).
Write one specific observation about what the player's last move (UCI: {player_last_move or "unknown"}) reveals about their playing style or tendencies.

Respond in this EXACT format — no other text:
MOVE: [uci]
OBSERVATION: [one sentence]"""


def build_level1_compression_prompt(annotations: list[str]) -> str:
    text = "\n".join(annotations)
    return f"""Analyze this chess player's behavior from the last {len(annotations)} moves:

{text}

Write a concise 3-4 sentence tactical summary of what this player is doing right now.
Focus on patterns, tendencies, and any exploitable behaviors. Be specific."""


def build_level2_update_prompt(l1_context, previous_report, result):
    prev = previous_report or "No previous scouting data."
    return f"""Update a scouting report on a chess player after their latest game (result: {result}).

PREVIOUS SCOUTING REPORT:
{prev}

LATEST GAME OBSERVATIONS:
{l1_context}

Produce an updated scouting report integrating new observations with previous ones.
Cover: opening preferences, middlegame tendencies, endgame weaknesses, psychological patterns,
exploits attempted, blind spots, recommended counter-strategy.
Keep under 500 tokens. Be specific and actionable."""


def build_level3_update_prompt(l2_reports, previous_profile):
    reports_text = "\n\n---\n\n".join(f"Report {i+1}:\n{r}" for i, r in enumerate(l2_reports))
    prev = previous_profile or "No previous profile."
    return f"""Build a deep psychological and strategic profile of a chess player.

PREVIOUS PROFILE:
{prev}

RECENT SCOUTING REPORTS:
{reports_text}

Produce an updated player profile including:
- Style Classification (Aggressive-Tactical / Passive-Positional / Chaotic / Balanced)
- Style Name (e.g. "The Impatient Attacker")
- Learning Rate, Emotional Pattern, Strategic Evolution
- Persistent Habits, Primary Weakness
- Difficulty Calibration (current win rate, target)
- Counter-Personality (how the AI should play against them)

Keep under 600 tokens."""
