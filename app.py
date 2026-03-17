import streamlit as st
from dotenv import load_dotenv
from db import database
from ui import game_page, profile_page, history_page

load_dotenv()
database.init_db()

st.set_page_config(page_title="PuzzleForge Chess", layout="wide")

page = st.sidebar.radio("Navigate", ["Game", "Profile", "History"])
if page == "Game":
    game_page.render()
elif page == "Profile":
    profile_page.render()
elif page == "History":
    history_page.render()
