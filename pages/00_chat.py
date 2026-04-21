# pages/00_chat.py - ALMAGAN INGENIEROS
import streamlit as st
from database.supabase_client import get_supabase
from utils.sidebar import render_sidebar

st.set_page_config(page_title="ALMAGAN | Chat de Obra", page_icon="💬", layout="wide")

# Verificar sesión
if "usuario_actual" not in st.session_state or st.session_state.usuario_actual is None:
    st.switch_page("main.py")

render_sidebar()

supabase = get_supabase()

from modules.chat import render_chat
render_chat(supabase)
