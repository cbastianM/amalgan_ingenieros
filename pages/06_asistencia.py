import streamlit as st
from database.supabase_client import get_supabase
from utils.sidebar import render_sidebar

st.set_page_config(page_title="ALMAGAN | Asistencia", page_icon="👷", layout="wide")

render_sidebar()

if "usuario_actual" not in st.session_state or st.session_state.usuario_actual is None:
    st.switch_page("main.py")

supabase = get_supabase()

from modules.attendance import render_asistencia
render_asistencia(supabase)