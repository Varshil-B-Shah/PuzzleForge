import streamlit as st
from db import database


def render():
    st.title("Game History")
    history = database.get_game_history()

    if not history:
        st.info("No games yet — play your first game to see history here.")
        return

    # Build display rows
    rows = []
    for i, g in enumerate(history, start=1):
        result_emoji = {"win": "✅ Win", "loss": "❌ Loss"}.get(g["result"], "— Draw")
        rows.append({
            "#": i,
            "Date": g.get("played_at", "")[:10] if g.get("played_at") else "",
            "Result": result_emoji,
            "Moves": g.get("duration_moves", 0),
        })

    st.dataframe(rows, use_container_width=True)

    # PGN viewer
    options = [f"Game {r['#']} — {r['Result']} ({r['Date']})" for r in rows]
    selected_idx = st.selectbox("Select a game to review PGN:", range(len(options)), format_func=lambda i: options[i])
    selected_game = history[selected_idx]
    pgn = selected_game.get("pgn") or "(No PGN recorded)"
    st.text_area("PGN", value=pgn, height=300, disabled=True)
