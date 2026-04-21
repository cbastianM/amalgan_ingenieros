import streamlit as st
import base64

# Utility: avatar as data URL from emoji
def avatar_data_url(emoji: str = "👷") -> str:
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="128" height="128"><rect width="128" height="128" fill="#f5f5f5"/><text x="50%" y="50%" text-anchor="middle" dominant-baseline="middle" font-family="Segoe UI Emoji" font-size="72">{emoji}</text></svg>'
    b64 = base64.b64encode(svg.encode("utf-8")).decode("ascii")
    return f"data:image/svg+xml;base64,{b64}"

# Prefijos de perfiles precargados por rol
PREDEFINED_PROFILES = {
    "Director": [{"name": "Carlos Mendoza", "rol": "Director", "asignado_default": "Carlos Ramírez", "avatar": avatar_data_url("👔")}],
    "Residente": [{"name": "Ana López", "rol": "Residente", "asignado_default": "Diego Morales", "avatar": avatar_data_url("🧑🏻‍💼")}],
    "Almacenista": [{"name": "Pedro Gómez", "rol": "Almacenista", "asignado_default": "Pedro Gómez", "avatar": avatar_data_url("🔧")}],
    "Controlador": [{"name": "Luis Ramírez", "rol": "Controlador", "asignado_default": "Javier Castillo", "avatar": avatar_data_url("🛠")}],
}

def _avatar_tag(avatar_url, name):
    return f"<img src='{avatar_url}' alt='{name}' style='width:64px;height:64px;border-radius:8px;object-fit:cover;border:1px solid #ddd'/>"

def render_profile_selector():
    st.markdown("### ¿Quién eres? Elige tu perfil")
    # Mostrar perfiles como tarjetas
    for rol, profiles in PREDEFINED_PROFILES.items():
        with st.container():
            cols = st.columns(len(profiles))
            for i, p in enumerate(profiles):
                with cols[i]:
                    avatar_html = _avatar_tag(p.get("avatar", avatar_data_url("👷")), p["name"])
                    # Use markdown to render avatar image cleanly, allow click via selectbox as workaround
                    st.markdown(avatar_html, unsafe_allow_html=True)
                    if st.button(f"Seleccionar {p['name']}", key=f"select_{p['name']}"):
                        st.session_state.current_profile = {
                            "name": p["name"],
                            "rol": rol,
                            "asignado_default": p.get("asignado_default"),
                            "avatar": p.get("avatar", avatar_data_url("👷"))
                        }
                        st.success("Perfil activo guardado")
                        st.experimental_rerun()

    st.markdown("---")
    st.button("Administrar Perfiles", key="admin_profiles_btn")

def get_current_profile():
    return st.session_state.get("current_profile", None)
