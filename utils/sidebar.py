# utils/sidebar.py
import streamlit as st
from utils.branding import render_logo_sidebar
from utils.profile import render_profile_photo_block
from database.queries import get_config
from database.supabase_client import get_supabase

def render_sidebar():
    if "usuario_actual" not in st.session_state or st.session_state.usuario_actual is None:
        st.switch_page("main.py")
    
    def es_director():
        return st.session_state.rol_actual == "Director"
    
    def es_residente():
        return st.session_state.rol_actual == "Residente"
    
    def usr_nombre():
        return st.session_state.get("nombre_visible", st.session_state.usuario_actual or "Sistema")
    
    # Logo corporativo
    render_logo_sidebar()
    
    # Foto de perfil
    render_profile_photo_block(st.session_state.usuario_actual, st.session_state.rol_actual, size=55)
    
    # Nombre y rol
    st.sidebar.write(f"**{usr_nombre()}**")
    st.sidebar.caption(st.session_state.rol_actual)
    
    # Info del proyecto
    proyectos = st.session_state.get("proyectos_disponibles", [])
    nombre_actual = st.session_state.get("nombre_proyecto", "")
    if proyectos:
        idx_actual = proyectos.index(nombre_actual) if nombre_actual in proyectos else 0
        proyecto_sel = st.sidebar.selectbox(
            "Proyecto",
            proyectos,
            index=idx_actual,
            key="sidebar_proyecto_sel"
        )
        if proyecto_sel != nombre_actual:
            st.session_state.nombre_proyecto = proyecto_sel
            supabase = get_supabase()
            config = get_config(supabase, proyecto_sel)
            st.session_state.datos_proyecto = config or {}
            st.cache_data.clear()
            st.rerun()
    elif nombre_actual:
        st.sidebar.info(f"Proyecto: {nombre_actual[:40]}")
    
    # Navegacion
    st.sidebar.markdown("---")
    st.sidebar.subheader("Navegacion")
    
    if es_director():
        st.sidebar.page_link("pages/00_chat.py", label="Chat de Obra", icon="💬")
        st.sidebar.page_link("pages/10_Chat_IA.py", label="Asistente IA", icon="🤖")
        st.sidebar.page_link("pages/01_Panel_Director.py", label="Panel Director", icon="📊")
        st.sidebar.page_link("pages/02_Mis_Tareas.py", label="Mis Tareas", icon="📋")
        st.sidebar.page_link("pages/03_Proveedores.py", label="Proveedores", icon="🏢")
        st.sidebar.page_link("pages/04_inventario.py", label="Inventario", icon="📦")
        st.sidebar.page_link("pages/05_maquinas.py", label="Maquinas", icon="🚜")
        st.sidebar.page_link("pages/06_asistencia.py", label="Asistencia", icon="👷")
        st.sidebar.page_link("pages/07_nomina.py", label="Nomina", icon="💵")
        st.sidebar.page_link("pages/08_materiales.py", label="Materiales", icon="🏗️")
        st.sidebar.page_link("pages/06_configuracion.py", label="Mi Perfil", icon="👤")
    elif es_residente():
        st.sidebar.page_link("pages/00_chat.py", label="Chat de Obra", icon="💬")
        st.sidebar.page_link("pages/02_Mis_Tareas.py", label="Mis Tareas", icon="📋")
        st.sidebar.page_link("pages/06_asistencia.py", label="Asistencia", icon="👷")
        st.sidebar.page_link("pages/08_materiales.py", label="Materiales", icon="🏗️")
        st.sidebar.page_link("pages/06_configuracion.py", label="Mi Perfil", icon="👤")
    elif st.session_state.rol_actual == "Almacenista":
        st.sidebar.page_link("pages/04_inventario.py", label="Control Inventario", icon="📦")
        st.sidebar.page_link("pages/08_materiales.py", label="Materiales", icon="🏗️")
        st.sidebar.page_link("pages/06_configuracion.py", label="Mi Perfil", icon="👤")
    elif st.session_state.rol_actual == "Controlador":
        st.sidebar.page_link("pages/05_maquinas.py", label="Control Maquinas", icon="🚜")
        st.sidebar.page_link("pages/06_asistencia.py", label="Asistencia", icon="👷")
        st.sidebar.page_link("pages/06_configuracion.py", label="Mi Perfil", icon="👤")
    
    # Botones de accion
    st.sidebar.markdown("---")
    col1, col2 = st.sidebar.columns(2)
    with col1:
        if st.button("Salir", use_container_width=True, key="btn_logout"):
            for k in ["usuario_actual", "rol_actual", "nombre_visible", "datos_proyecto", "nombre_proyecto", "ultima_carga", "proyectos_disponibles"]:
                st.session_state.pop(k, None)
            st.rerun()
    with col2:
        if st.button("Recargar", use_container_width=True, key="btn_reload"):
            st.cache_data.clear()
            if "ultima_carga" in st.session_state:
                st.session_state.ultima_carga = None
            st.rerun()
    
    st.sidebar.caption("2026 ALMAGAN INGENIEROS | Sistema de Gestion")
