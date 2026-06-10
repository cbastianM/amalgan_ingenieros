import streamlit as st
import datetime
import os
from database.supabase_client import init_supabase
from database.queries import get_config, get_proyectos
from utils.branding import get_logo_path

st.set_page_config(
    page_title="ALMAGAN INGENIEROS",
    page_icon="build",
    layout="wide",
    initial_sidebar_state="collapsed"
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
    "proyectos_disponibles": [],
}
for k, v in _defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

def logueado(): return st.session_state.usuario_actual is not None
def es_director(): return st.session_state.rol_actual == "Director"
def usr_nombre(): return st.session_state.get("nombre_visible", st.session_state.usuario_actual or "Sistema")

def cargar_datos_proyecto(proyecto=None):
    try:
        config = get_config(supabase, proyecto) if proyecto else get_config(supabase)
        st.session_state.datos_proyecto = config or {}
        if not proyecto:
            st.session_state.nombre_proyecto = config.get("proyecto", "Edificio Colombo Americana") if config else "Edificio Colombo Americana"
        else:
            st.session_state.nombre_proyecto = proyecto
        proyectos = get_proyectos(supabase)
        st.session_state.proyectos_disponibles = proyectos
        st.session_state.ultima_carga = datetime.datetime.now()
    except Exception:
        st.session_state.nombre_proyecto = proyecto or "Edificio Colombo Americana"
        st.session_state.datos_proyecto = {}
        st.session_state.ultima_carga = datetime.datetime.now()

if not logueado():
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

        .stApp { background: #FFFFFF !important; }
        [data-testid="stSidebar"] { display: none !important; }
        header[data-testid="stHeader"] { display: none !important; }
        #MainMenu { visibility: hidden !important; }
        footer { visibility: hidden !important; }

        .main .block-container {
            padding: 2rem 1rem !important;
            max-width: 960px !important;
        }

        .stButton > button {
            background: #FFFFFF !important;
            color: #1A1A1A !important;
            border: 1.5px solid #E0E0E0 !important;
            border-radius: 10px !important;
            font-weight: 600 !important;
            font-size: 13px !important;
            padding: 10px 8px !important;
            transition: all 0.2s ease !important;
        }
        .stButton > button:hover {
            background: #FFFDF5 !important;
            border-color: #C9A227 !important;
            color: #C9A227 !important;
            box-shadow: 0 2px 12px rgba(201,162,39,0.12) !important;
        }

        @media (max-width: 768px) {
            .main .block-container { padding: 1.2rem 0.8rem !important; }
        }

        [data-testid="stImage"] { text-align: center !important; }
        [data-testid="stImage"] img { margin: 0 auto !important; display: block !important; }
    </style>
    """, unsafe_allow_html=True)

    col_brand, col_access = st.columns([2, 3])

    with col_brand:
        logo_path = get_logo_path()
        logo_src = ""
        if logo_path and os.path.exists(logo_path):
            import base64, mimetypes
            mime = mimetypes.guess_type(logo_path)[0] or "image/png"
            with open(logo_path, "rb") as f:
                logo_src = f"data:{mime};base64,{base64.b64encode(f.read()).decode()}"

        st.markdown(f"""
        <div style="text-align:center">
            <img src="{logo_src}" style="width:120px;margin:0 auto 16px auto;display:block" />
            <h1 style="color:#1A1A1A;margin:0;font-size:26px;font-weight:800;letter-spacing:2px;font-family:Inter,sans-serif">ALMAGAN</h1>
            <div style="width:36px;height:2px;background:#C9A227;margin:14px auto;border-radius:1px"></div>
            <p style="color:#C9A227;margin:0;font-size:11px;letter-spacing:4px;text-transform:uppercase;font-weight:600;font-family:Inter,sans-serif">Ingenieros</p>
            <p style="color:#888;margin:20px 0 0;font-size:11px;font-family:Inter,sans-serif">Gestión de Obras</p>
        </div>
        """, unsafe_allow_html=True)

    with col_access:
        st.markdown("""
        <div style="text-align:center;padding-bottom:8px">
            <p style="color:#999;font-size:10px;letter-spacing:3px;text-transform:uppercase;font-weight:600;margin:0;font-family:Inter,sans-serif">
                Seleccione su perfil
            </p>
        </div>
        """, unsafe_allow_html=True)

        PROFILES = [
            ("director1", "1234", "Director", "Carlos Mendoza", "👔"),
            ("residente1", "1234", "Residente", "Ana López", "👷"),
            ("almacenista1", "1234", "Almacenista", "Pedro Gómez", "📦"),
            ("controlador1", "1234", "Controlador", "Luis Ramírez", "🚜"),
        ]

        for pair in [PROFILES[i:i+2] for i in range(0, len(PROFILES), 2)]:
            c1, c2 = st.columns(2)
            for col, (usuario, clave, rol, nombre, emoji) in zip([c1, c2], pair):
                with col:
                    st.markdown(f"""
                    <div style="text-align:center;padding:4px 0">
                        <div style="font-size:28px;line-height:1">{emoji}</div>
                        <div style="font-family:Inter,sans-serif;font-weight:700;font-size:13px;color:#1A1A1A;margin-top:3px">{nombre.split()[0]}</div>
                        <div style="font-family:Inter,sans-serif;font-size:10px;color:#C9A227;text-transform:uppercase;letter-spacing:1px;font-weight:500">{rol}</div>
                    </div>
                    """, unsafe_allow_html=True)
                    if st.button("Ingresar", use_container_width=True, key=f"quick_{usuario}"):
                        try:
                            response = supabase.table("usuarios").select("*").eq("usuario", usuario).eq("clave", clave).eq("activo", True).execute()
                            if response.data and len(response.data) > 0:
                                user = response.data[0]
                                st.session_state.usuario_actual = str(user["usuario"]).strip()
                                st.session_state.rol_actual = str(user["rol"]).strip()
                                st.session_state.nombre_visible = str(user.get("nombre_visible", user["usuario"])).strip()
                                cargar_datos_proyecto()
                                st.rerun()
                        except Exception:
                            st.error("Error al iniciar sesión")

    st.stop()

# ==========================================
# APP PRINCIPAL (LOGUEADO)
# ==========================================
from utils.sidebar import render_sidebar
render_sidebar()

st.markdown("""
<style>
    .stApp { background: linear-gradient(135deg, #F5F5F5 0%, #FFFFFF 100%) !important; }
    [data-testid="stSidebar"] { display: flex !important; }
    header[data-testid="stHeader"] { display: flex !important; }
    #MainMenu { visibility: visible !important; }
    footer { visibility: visible !important; }
</style>
""", unsafe_allow_html=True)

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
col1, col2 = st.columns(2)

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

col1, col2 = st.columns(2)
with col1:
    st.markdown("""
    <div class="nav-card">
        <div class="nav-icon">📋</div>
        <div class="nav-title">Mis Tareas</div>
        <div class="nav-desc">Gestion y seguimiento de actividades</div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Ver Tareas", use_container_width=True, key="btn_tareas"):
        st.switch_page("pages/02_Mis_Tareas.py")

with col2:
    st.markdown("""
    <div class="nav-card">
        <div class="nav-icon">🤖</div>
        <div class="nav-title">Asistente IA</div>
        <div class="nav-desc">Consultas inteligentes con DeepSeek</div>
    </div>
    """, unsafe_allow_html=True)
    if es_director():
        if st.button("Preguntar a la IA", use_container_width=True, key="btn_ia"):
            st.switch_page("pages/10_Chat_IA.py")
    else:
        st.button("Preguntar a la IA", use_container_width=True, key="btn_ia", disabled=True)