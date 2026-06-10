import streamlit as st
from utils.sidebar import render_sidebar
from database.supabase_client import get_supabase
from modules.chat_ia import render_chat_ia

st.set_page_config(page_title="ALMAGAN | Asistente IA", page_icon="🤖", layout="wide", initial_sidebar_state="collapsed")

render_sidebar()

supabase = get_supabase()
render_chat_ia(supabase)
