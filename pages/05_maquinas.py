# pages/05_maquinas.py - ALMAGAN INGENIEROS
import streamlit as st
from database.supabase_client import get_supabase
from utils.sidebar import render_sidebar

st.set_page_config(page_title="ALMAGAN | Control de Máquinas", page_icon="🚜", layout="wide")

# Verificar sesión activa
if "usuario_actual" not in st.session_state or st.session_state.usuario_actual is None:
    st.switch_page("main.py")

# Renderizar barra lateral primero
render_sidebar()

# Cargar módulo de maquinaria
supabase = get_supabase()
from modules.machines import render_controlador
render_controlador(supabase)
