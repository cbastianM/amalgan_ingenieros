# utils/branding.py - Gestion de logo y marca corporativa
import os
import streamlit as st
from PIL import Image
import base64

LOGO_DIR = "assets/images"
LOGO_PATHS = [os.path.join(LOGO_DIR, f"logo.{ext}") for ext in ['png', 'jpg', 'jpeg', 'svg']]

def get_logo_path():
    for path in LOGO_PATHS:
        if os.path.exists(path):
            return path
    return None

def render_logo_sidebar():
    """Muestra el logo de la empresa en la barra lateral usando st.image (sin HTML)."""
    logo_path = get_logo_path()
    if logo_path and os.path.exists(logo_path):
        st.sidebar.image(logo_path, use_container_width=True)
    else:
        st.sidebar.markdown("**ALMAGAN**")
        st.sidebar.caption("INGENIEROS")

def render_logo_main():
    """Muestra el logo de la empresa en el area principal usando st.image (sin HTML)."""
    logo_path = get_logo_path()
    if logo_path and os.path.exists(logo_path):
        st.image(logo_path, width=240)
    else:
        st.markdown("**ALMAGAN INGENIEROS**")

def render_logo_login():
    """Muestra el logo de la empresa en el login usando st.image (sin HTML)."""
    logo_path = get_logo_path()
    if logo_path and os.path.exists(logo_path):
        st.image(logo_path, width=200)
    else:
        st.markdown("**ALMAGAN INGENIEROS**")

def save_uploaded_logo(uploaded_file):
    if uploaded_file is not None:
        for path in LOGO_PATHS:
            if os.path.exists(path):
                os.remove(path)
        
        file_ext = uploaded_file.name.split('.')[-1].lower()
        new_path = os.path.join(LOGO_DIR, f"logo.{file_ext}")
        
        with open(new_path, "wb") as f:
            f.write(uploaded_file.getvalue())
        
        if file_ext in ['png', 'jpg', 'jpeg']:
            try:
                img = Image.open(new_path)
                max_size = (800, 800)
                img.thumbnail(max_size, Image.Resampling.LANCZOS)
                img.save(new_path, optimize=True, quality=90)
            except:
                pass
        
        return True
    return False

def render_logo_uploader():
    st.subheader("Configuracion de Marca")
    
    current_logo = get_logo_path()
    
    if current_logo:
        st.success("Logo actual configurado")
        try:
            st.image(current_logo, width=200, caption="Logo actual")
        except:
            st.info("Logo cargado")
    else:
        st.info("No hay logo personalizado. Se usa el logo por defecto.")
    
    st.divider()
    
    st.markdown("""
    **Sube tu logo corporativo**
    
    Formatos: PNG, JPG, JPEG, SVG
    
    Recomendaciones:
    - Fondo transparente (PNG/SVG)
    - Resolucion minima: 400x400 px
    """)
    
    uploaded_file = st.file_uploader(
        "Selecciona tu logo",
        type=['png', 'jpg', 'jpeg', 'svg'],
        key="logo_uploader"
    )
    
    if uploaded_file is not None:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Vista previa:**")
            st.image(uploaded_file, width=200)
        
        with col2:
            st.markdown("**Aplicar cambios?**")
            if st.button("Guardar Logo", type="primary", use_container_width=True):
                if save_uploaded_logo(uploaded_file):
                    st.success("Logo guardado correctamente")
                    st.rerun()
                else:
                    st.error("Error al guardar el logo")
    
    if current_logo:
        st.divider()
        if st.button("Eliminar logo personalizado", type="secondary"):
            try:
                os.remove(current_logo)
                st.success("Logo eliminado")
                st.rerun()
            except Exception as e:
                st.error(f"Error al eliminar: {e}")