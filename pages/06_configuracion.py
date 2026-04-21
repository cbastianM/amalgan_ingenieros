# pages/06_configuracion.py - Configuración del Sistema
import streamlit as st
from utils.sidebar import render_sidebar
from utils.branding import render_logo_uploader
from utils.profile import save_profile_photo, delete_profile_photo, get_profile_photo_path, get_default_avatar, profile_photo_exists

st.set_page_config(page_title="ALMAGAN | Mi Perfil", page_icon="👤", layout="wide")

# CSS
st.markdown("""
<style>
    .profile-section {
        background: linear-gradient(135deg, #FFFFFF 0%, #F8F8F8 100%);
        border: 2px solid #E0E0E0;
        border-radius: 12px;
        padding: 25px;
        margin-bottom: 20px;
    }
    .photo-large {
        width: 150px;
        height: 150px;
        border-radius: 50%;
        border: 4px solid #C9A227;
        box-shadow: 0 6px 20px rgba(201, 162, 39, 0.3);
        overflow: hidden;
        display: flex;
        align-items: center;
        justify-content: center;
        background: #F5F5F5;
    }
</style>
""", unsafe_allow_html=True)

# Renderizar sidebar PRIMERO
render_sidebar()

# Verificar sesión
if "usuario_actual" not in st.session_state or st.session_state.usuario_actual is None:
    st.switch_page("main.py")

st.title("👤 Mi Perfil")

# Obtener datos del usuario actual
username = st.session_state.usuario_actual
nombre = st.session_state.get("nombre_visible", username)
rol = st.session_state.rol_actual

# Tabs
tab1, tab2 = st.tabs(["📷 Foto de Perfil", "🎨 Marca Corporativa"])

with tab1:
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown("### Tu Foto Actual")
        
        # Mostrar foto actual o emoji
        photo_path = get_profile_photo_path(username)
        
        if photo_path and profile_photo_exists(username):
            st.image(photo_path, width=150, caption="Tu foto de perfil")
        else:
            default_emoji = get_default_avatar(rol)
            st.markdown(f"""
            <div class="photo-large">
                <span style="font-size:80px">{default_emoji}</span>
            </div>
            <div style="text-align:center;margin-top:10px;color:#666666;font-size:13px">Foto por defecto</div>
            """, unsafe_allow_html=True)
        
        if profile_photo_exists(username):
            if st.button("🗑️ Eliminar Foto", type="secondary"):
                delete_profile_photo(username)
                st.success("✅ Foto eliminada")
                st.rerun()
    
    with col2:
        st.markdown("### Cambiar Foto de Perfil")
        
        st.markdown("""
        **Sube tu foto de perfil**
        
        - Formatos: PNG, JPG, JPEG
        - Tamaño recomendado: 400x400 px
        - La imagen se redimensionará automáticamente
        """)
        
        uploaded_file = st.file_uploader(
            "Selecciona tu foto",
            type=['png', 'jpg', 'jpeg'],
            key="profile_photo_uploader"
        )
        
        if uploaded_file is not None:
            col_a, col_b = st.columns(2)
            
            with col_a:
                st.markdown("**Vista previa:**")
                st.image(uploaded_file, width=150)
            
            with col_b:
                st.markdown("**¿Aplicar?**")
                if st.button("💾 Guardar Foto", type="primary", use_container_width=True):
                    if save_profile_photo(username, uploaded_file):
                        st.success("✅ Foto guardada")
                        st.rerun()
                    else:
                        st.error("❌ Error al guardar")

with tab2:
    render_logo_uploader()

# Información del sistema
with st.expander("ℹ️ Información de tu Cuenta"):
    st.markdown(f"""
    - **Usuario:** {username}
    - **Nombre:** {nombre}
    - **Rol:** {rol}
    - **Proyecto:** {st.session_state.get('nombre_proyecto', 'No asignado')}
    """)