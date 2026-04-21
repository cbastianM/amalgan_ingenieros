import streamlit as st
from database.supabase_client import get_supabase
from utils.sidebar import render_sidebar

st.set_page_config(page_title="ALMAGAN | Nómina", page_icon="💵", layout="wide")

render_sidebar()

if "usuario_actual" not in st.session_state or st.session_state.usuario_actual is None:
    st.switch_page("main.py")

if st.session_state.rol_actual != "Director":
    st.error("🚫 Acceso denegado. Solo para Directores.")
    st.stop()

supabase = get_supabase()

from modules.payroll import render_nomina
render_nomina(supabase)