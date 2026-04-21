import streamlit as st
from database.supabase_client import get_supabase
from utils.sidebar import render_sidebar

st.set_page_config(page_title="ALMAGAN | Panel Director", page_icon="📊", layout="wide")

# Renderizar sidebar PRIMERO
render_sidebar()

# Verificar sesión
if "usuario_actual" not in st.session_state or st.session_state.usuario_actual is None:
    st.switch_page("main.py")

# Verificar que sea director
if st.session_state.rol_actual != "Director":
    st.error("🚫 Acceso denegado. Solo para Directores.")
    st.stop()

supabase = get_supabase()

from modules.dashboard import render_dashboard
render_dashboard(supabase)
