import streamlit as st
import streamlit.components.v1 as components

# main game page
def render():
    st.title("PuzzleForge Chess")
    components.iframe("http://localhost:8000", height=760, scrolling=False)
