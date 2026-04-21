import streamlit as st
from database.supabase_client import get_supabase
from utils.sidebar import render_sidebar

st.set_page_config(page_title="ALMAGAN | Control de Inventario", page_icon="📦", layout="wide")

# Renderizar sidebar PRIMERO
render_sidebar()

# Verificar sesión
if "usuario_actual" not in st.session_state or st.session_state.usuario_actual is None:
    st.switch_page("main.py")

supabase = get_supabase()

from modules.inventory import render_almacenista
render_almacenista(supabase)
