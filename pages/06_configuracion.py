# pages/06_configuracion.py - Configuracion del Sistema
import streamlit as st
from utils.sidebar import render_sidebar
from utils.branding import render_logo_uploader
from utils.profile import save_profile_photo, delete_profile_photo, get_profile_photo_path, get_default_avatar, profile_photo_exists
from config.settings import get_user_email, save_user_email, is_email_configured
from utils.email_service import test_email_connection, get_email_sender_config
from database.supabase_client import get_supabase

st.set_page_config(page_title="ALMAGAN | Mi Perfil", page_icon="👤", layout="wide", initial_sidebar_state="collapsed")

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
    .email-card {
        background: linear-gradient(135deg, #FFFFFF 0%, #F8F8F8 100%);
        border: 2px solid #E0E0E0;
        border-radius: 12px;
        padding: 28px;
        margin-bottom: 18px;
    }
</style>
""", unsafe_allow_html=True)

render_sidebar()

if "usuario_actual" not in st.session_state or st.session_state.usuario_actual is None:
    st.switch_page("main.py")

supabase = get_supabase()
username = st.session_state.usuario_actual
nombre = st.session_state.get("nombre_visible", username)
rol = st.session_state.rol_actual

tab1, tab2, tab3 = st.tabs(["📷 Foto de Perfil", "🎨 Marca Corporativa", "📧 Correo"])

with tab1:
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown("### Tu Foto Actual")
        
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

with tab3:
    correo_actual = get_user_email(supabase, username)

    if rol == "Director":
        if is_email_configured():
            st.success("✉️ Notificaciones activas — se enviarán cuando se asignen tareas.")
            if st.button("🔍 Probar Conexión", use_container_width=True):
                saved_cfg = get_email_sender_config()
                with st.spinner("Probando conexión..."):
                    result = test_email_connection(saved_cfg["sender_email"], saved_cfg["sender_password"])
                if result["ok"]:
                    st.success(f"✅ {result['msg']}")
                else:
                    st.error(f"❌ {result['msg']}")
        else:
            st.warning("⚠️ Sin configurar — contacte al administrador para activar las notificaciones.")

    else:
        # ── OTROS ROLES: Solo ven estado ──
        if is_email_configured():
            st.success("✅ Las notificaciones por correo están activas")
        else:
            st.warning("⚠️ Las notificaciones por correo aún no están activas")

    # ── TU CORREO PERSONAL (todos los roles) ──
    st.markdown("### 📬 Tu Correo de Notificaciones")
    st.caption("Cuando te asignen una tarea, llega un correo aquí.")

    st.markdown(f"""
    <div class="email-card">
        <div style="display:flex;align-items:center;gap:12px;margin-bottom:8px">
            <span style="font-size:28px">👤</span>
            <div>
                <div style="font-size:15px;font-weight:600;color:#1A1A1A">{nombre}</div>
                <div style="font-size:12px;color:#888">{rol}</div>
            </div>
        </div>
        <div style="border-top:1px solid #eee;padding-top:8px;margin-top:4px">
            <span style="font-size:12px;color:#888">Correo actual:</span>
            <div style="font-size:16px;font-weight:600;color:#1A1A1A;margin-top:2px">
                {('📬 ' + correo_actual) if correo_actual else '❌ Sin correo'}
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    with st.form("email_form"):
        nuevo_correo = st.text_input(
            "Tu correo electrónico",
            value=correo_actual or "",
            placeholder="ejemplo@correo.com",
            key="email_input_notif"
        )
        submitted = st.form_submit_button("💾 Guardar Correo", type="primary", use_container_width=True)

    if submitted:
        if nuevo_correo and "@" not in nuevo_correo:
            st.error("❌ Ingrese un correo electrónico válido")
        elif nuevo_correo.strip() == "" and correo_actual:
            if save_user_email(supabase, username, ""):
                st.success("✅ Correo eliminado. No recibirá notificaciones.")
                st.rerun()
            else:
                st.error("❌ Error al actualizar")
        elif nuevo_correo.strip():
            if save_user_email(supabase, username, nuevo_correo.strip()):
                st.success(f"✅ Correo guardado: {nuevo_correo.strip()}")
                st.rerun()
            else:
                st.error("❌ Error al guardar el correo")
        else:
            st.warning("⚠️ Ingrese un correo electrónico")

    if rol == "Director":
        with st.expander("📋 Correos del equipo"):
            resp = supabase.table("trabajadores").select("nombre,cargo,email").eq("activo", True).execute()
            if resp.data:
                import pandas as pd
                df_trab = pd.DataFrame(resp.data)
                if "email" not in df_trab.columns:
                    df_trab["email"] = ""
                for _, row in df_trab.iterrows():
                    email_txt = row["email"] if row["email"] else "Sin correo"
                    icon = "✅" if row["email"] else "❌"
                    st.markdown(f"{icon} **{row['nombre']}** — {row['cargo']} — {email_txt}")

with st.expander("ℹ️ Información de tu Cuenta"):
    st.markdown(f"""
    - **Usuario:** {username}
    - **Nombre:** {nombre}
    - **Rol:** {rol}
    - **Proyecto:** {st.session_state.get('nombre_proyecto', 'No asignado')}
    - **Correo:** {correo_actual or 'No configurado'}
    """)