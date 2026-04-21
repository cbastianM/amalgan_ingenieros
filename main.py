import streamlit as st
import datetime
from database.supabase_client import init_supabase
from database.queries import get_config

st.set_page_config(
    page_title="ALMAGAN INGENIEROS",
    page_icon="build",
    layout="wide",
    initial_sidebar_state="expanded"
)

@st.cache_resource
def get_db():
    return init_supabase()

supabase = get_db()

_defaults = {
    "chat_historial": {}, 
    "nombre_proyecto": None, 
    "usuario_actual": None, 
    "rol_actual": None,
    "datos_proyecto": {},
    "ultima_carga": None,
}
for k, v in _defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

def logueado(): return st.session_state.usuario_actual is not None
def es_director(): return st.session_state.rol_actual == "Director"
def usr_nombre(): return st.session_state.get("nombre_visible", st.session_state.usuario_actual or "Sistema")

def cargar_datos_proyecto():
    try:
        config = get_config(supabase)
        st.session_state.datos_proyecto = config or {}
        st.session_state.nombre_proyecto = config.get("proyecto", "Edificio Colombo Americana") if config else "Edificio Colombo Americana"
        st.session_state.ultima_carga = datetime.datetime.now()
    except Exception:
        st.session_state.nombre_proyecto = "Edificio Colombo Americana"
        st.session_state.datos_proyecto = {}
        st.session_state.ultima_carga = datetime.datetime.now()

if not logueado():
    # Sidebar con login
    st.sidebar.markdown("##")
    st.sidebar.markdown("### ALMAGAN")
    st.sidebar.caption("INGENIEROS")
    st.sidebar.markdown("---")
    
    with st.sidebar.form("login_form"):
        st.markdown("**Iniciar Sesion**")
        
        usuario_input = st.text_input("Usuario", key="lu")
        clave_input = st.text_input("Clave", type="password", key="lp")
        
        submit = st.form_submit_button("Ingresar", type="primary", use_container_width=True)
        
        if submit and usuario_input and clave_input:
            try:
                response = supabase.table("usuarios").select("*").eq("usuario", usuario_input).eq("clave", clave_input).eq("activo", True).execute()
                
                if response.data and len(response.data) > 0:
                    user = response.data[0]
                    st.session_state.usuario_actual = str(user["usuario"]).strip()
                    st.session_state.rol_actual = str(user["rol"]).strip()
                    st.session_state.nombre_visible = str(user.get("nombre_visible", user["usuario"])).strip()
                    
                    cargar_datos_proyecto()
                    st.rerun()
                else:
                    st.sidebar.error("Usuario o clave incorrectos")
                    
            except Exception as e:
                st.sidebar.error(f"Error: {type(e).__name__}")
    
    st.sidebar.markdown("---")
    st.sidebar.caption("Prueba: director1/1234 | residente1/1234")
    
    # Contenido principal
    st.title("ALMAGAN INGENIEROS")
    st.subheader("Sistema de Gestion de Obras")
    st.markdown("---")
    st.write("Selecciona un usuario en el panel lateral para iniciar sesion.")
    
    st.stop()

# ==========================================
# APP PRINCIPAL (LOGUEADO)
# ==========================================
from utils.sidebar import render_sidebar
render_sidebar()

# CSS para tarjetas atractivas
st.markdown("""
<style>
    .welcome-header {
        background: linear-gradient(135deg, #1A1A1A 0%, #2D2D2D 100%);
        padding: 28px 32px;
        border-radius: 14px;
        margin-bottom: 28px;
        border-left: 5px solid #C9A227;
    }
    .welcome-header h1 {
        color: #FFFFFF !important;
        margin: 0;
        font-size: 26px;
    }
    .welcome-header p {
        color: #C9A227 !important;
        margin: 6px 0 0 0;
        font-size: 14px;
    }
    .nav-card {
        background: #FFFFFF;
        border: 2px solid #E8E8E8;
        border-radius: 14px;
        padding: 28px 20px;
        text-align: center;
        transition: all 0.3s ease;
        cursor: pointer;
    }
    .nav-card:hover {
        border-color: #C9A227;
        box-shadow: 0 8px 24px rgba(201, 162, 39, 0.15);
        transform: translateY(-3px);
    }
    .nav-icon {
        font-size: 40px;
        margin-bottom: 12px;
    }
    .nav-title {
        font-size: 16px;
        font-weight: 700;
        color: #1A1A1A;
        margin-bottom: 6px;
    }
    .nav-desc {
        font-size: 12px;
        color: #888888;
    }
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #C9A227 0%, #B08D1C 100%) !important;
        border: none !important;
        border-radius: 10px !important;
        font-weight: 700 !important;
        color: #FFFFFF !important;
    }
</style>
""", unsafe_allow_html=True)

# Header de bienvenida
st.markdown(f"""
<div class="welcome-header">
    <h1>Bienvenido, {usr_nombre()}</h1>
    <p>Sistema de Gestion de Obras - ALMAGAN INGENIEROS</p>
</div>
""", unsafe_allow_html=True)

# Tarjetas de navegacion
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <div class="nav-card">
        <div class="nav-icon">💬</div>
        <div class="nav-title">Chat de Obra</div>
        <div class="nav-desc">Comunicacion en tiempo real con tu equipo</div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Ir al Chat", use_container_width=True, key="btn_chat"):
        st.switch_page("pages/00_chat.py")

with col2:
    st.markdown("""
    <div class="nav-card">
        <div class="nav-icon">📊</div>
        <div class="nav-title">Panel Director</div>
        <div class="nav-desc">Metricas, reportes y vision general</div>
    </div>
    """, unsafe_allow_html=True)
    if es_director():
        if st.button("Ver Panel", use_container_width=True, key="btn_panel"):
            st.switch_page("pages/01_Panel_Director.py")
    else:
        st.button("Ver Panel", use_container_width=True, key="btn_panel", disabled=True)

with col3:
    st.markdown("""
    <div class="nav-card">
        <div class="nav-icon">📋</div>
        <div class="nav-title">Mis Tareas</div>
        <div class="nav-desc">Gestion y seguimiento de actividades</div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Ver Tareas", use_container_width=True, key="btn_tareas"):
        st.switch_page("pages/02_Mis_Tareas.py")