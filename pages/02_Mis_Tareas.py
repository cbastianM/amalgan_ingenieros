import streamlit as st
from database.supabase_client import get_supabase
from utils.sidebar import render_sidebar

st.set_page_config(page_title="ALMAGAN | Mis Tareas", page_icon="📋", layout="wide")

# Renderizar sidebar PRIMERO
render_sidebar()

# Verificar sesión
if "usuario_actual" not in st.session_state or st.session_state.usuario_actual is None:
    st.switch_page("main.py")

supabase = get_supabase()

from modules.tasks import render_mis_tareas
from modules.profiles import render_profile_selector

# On startup, ensure profile is selected
try:
    from modules.profiles import get_current_profile
    if not get_current_profile():
        render_profile_selector()
except Exception:
    pass
render_mis_tareas(supabase)
