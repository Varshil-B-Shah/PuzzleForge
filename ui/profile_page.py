import streamlit as st
from db import database


def render():
    st.title("Player Profile")

    profile = database.get_level3_profile()
    history = database.get_game_history()
    game_count = len(history)

    # ── Top-level stats ───────────────────────────────────────────────────────
    col1, col2, col3 = st.columns(3)
    wins = sum(1 for g in history if g["result"] == "1-0")
    losses = sum(1 for g in history if g["result"] == "0-1")
    draws = game_count - wins - losses
    col1.metric("Games Played", game_count)
    col2.metric("Win Rate", f"{wins/game_count*100:.0f}%" if game_count else "—")
    col3.metric("W / L / D", f"{wins} / {losses} / {draws}")

    # ── Win rate trend (Plotly, 5-game buckets) ───────────────────────────────
    if game_count >= 5:
        _render_win_rate_chart(history)

    # ── Player profile card ───────────────────────────────────────────────────
    if profile:
        st.subheader("Your Style")
        col_a, col_b = st.columns(2)
        col_a.markdown(f"**Style Name**  \n{profile['style_name']}")
        col_b.markdown(f"**Classification**  \n{profile['style_class']}")

        st.subheader("Full Profile")
        st.text_area("", value=profile["full_profile"], height=300, disabled=True)

        st.subheader("AI Counter-Strategy")
        st.info(profile["counter_strategy"] or "Not yet determined.")
    else:
        st.info("Play at least 5 games to generate your player profile.")

    # ── Latest scouting report ────────────────────────────────────────────────
    reports = database.get_level2_reports(1)
    if reports:
        with st.expander("Latest Post-Game Scouting Report"):
            st.write(reports[0])

    # ── Danger zone ───────────────────────────────────────────────────────────
    st.divider()
    with st.expander("Danger Zone"):
        st.warning("This will permanently delete all games, scouting reports, and your player profile.")
        if st.button("Reset All Data", type="primary"):
            _do_reset()


def _do_reset():
    database.reset_db()
    for key in ["board", "game_id", "game_active", "move_count", "level1"]:
        st.session_state.pop(key, None)
    st.success("All data reset. Starting fresh!")
    st.rerun()


def _render_win_rate_chart(history: list[dict]):
    import plotly.graph_objects as go

    bucket_size = 5
    buckets, rates = [], []
    for i in range(0, len(history) - bucket_size + 1, bucket_size):
        chunk = history[i : i + bucket_size]
        wins = sum(1 for g in chunk if g["result"] == "1-0")
        buckets.append(f"Games {i+1}–{i+bucket_size}")
        rates.append(wins / bucket_size * 100)

    fig = go.Figure(go.Scatter(
        x=buckets, y=rates,
        mode="lines+markers",
        line=dict(color="#ef4444", width=2),
        marker=dict(size=8),
    ))
    fig.update_layout(
        title="Win Rate by 5-Game Bucket",
        yaxis=dict(title="Win %", range=[0, 100]),
        xaxis=dict(title="Games"),
        height=300,
        margin=dict(l=40, r=20, t=40, b=40),
    )
    st.plotly_chart(fig, use_container_width=True)
