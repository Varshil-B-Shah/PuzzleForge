def build_move_prompt(
    fen, legal_moves_uci, level1_ctx, level2_report, level3_profile,
    player_last_move=None, tilt_mode=None, target_win_rate=0.40,
):
    profile = level3_profile or "No profile yet. Play solid intermediate chess with occasional natural mistakes."
    scouting = level2_report or "No scouting data yet."
    l1 = level1_ctx or "No annotations yet — game just started."
    moves_str = ", ".join(legal_moves_uci)
    strategy = "Execute the counter-strategy described in your player profile." if level3_profile else "Play balanced intermediate chess."
    personality = "Embody the counter-personality described in your player profile." if level3_profile else "Balanced."

    trap_section = ""
    if level2_report:
        trap_section = """
TRAP OPPORTUNITY:
The scouting report identifies exploitable patterns in this player's style.
You may occasionally set a trap — play a move that invites their favourite line
but has a prepared refutation. If setting a trap, write a subtly inviting
OBSERVATION (hint without revealing the trap) and respond with TRAP: yes.
Otherwise respond with TRAP: no.
"""

    tilt_section = f"""
TILT MODE: {tilt_mode or "none"}
- exploit: player is tilting — play sharply, increase pressure, exploit impatience
- cooling: player has steadied — return to your normal counter-strategy
- none: play normally
"""

    difficulty_section = f"""
DIFFICULTY: Your target is to win ~{int((1 - target_win_rate) * 100)}% of games.
Calibrate naturally — make human-like mistakes if needed to stay near this target.
"""

    reckless_section = """
After choosing your move, classify the player's last move:
RECKLESS: yes — if the move was impulsive, a blunder, tactically unsound, or emotionally driven
RECKLESS: no  — if the move was solid, positional, or strategically sound
"""

    return f"""PLAYER PROFILE:
{profile}

SCOUTING REPORT:
{scouting}

THIS GAME SO FAR:
{l1}

CURRENT BOARD (FEN):
{fen}

LEGAL MOVES (UCI format):
{moves_str}

YOUR STRATEGIC GOAL:
{strategy}

YOUR PERSONALITY:
{personality}
{trap_section}{tilt_section}{difficulty_section}
Choose exactly ONE move from the legal moves list above (UCI format).
Write one observation about what the player's last move reveals about their style.
{reckless_section}
Respond in this EXACT format — no other text:
MOVE: [uci]
OBSERVATION: [one sentence]
TRAP: yes/no
RECKLESS: yes/no"""


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


def build_debrief_prompt(pgn: str, result: str, l2_report: str | None) -> str:
    scouting = l2_report or "No prior scouting data."
    return f"""Analyse this chess game and write a post-game debrief for the player.

GAME RESULT: {result}
PGN: {pgn}
SCOUTING CONTEXT: {scouting}

Write exactly 2-3 sentences. Cover: what decided the game, and one concrete improvement for next time.
Address the player directly ("You..."). No headers, no lists — plain sentences only. Max 60 words."""
