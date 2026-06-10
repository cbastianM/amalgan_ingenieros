import streamlit as st


def get_email_sender_config() -> dict:
    from utils.email_service import get_email_sender_config as _get
    return _get()


def is_email_configured() -> bool:
    from utils.email_service import is_email_configured as _is
    return _is()


def get_user_email(supabase, username: str) -> str:
    resp = supabase.table("usuarios").select("email").eq("usuario", username).execute()
    if resp.data and resp.data[0].get("email"):
        return resp.data[0]["email"]
    return ""


def save_user_email(supabase, username: str, email: str) -> bool:
    try:
        resp = supabase.table("usuarios").update({"email": email}).eq("usuario", username).execute()
        return resp.data is not None
    except Exception:
        return False


def get_trabajador_email(supabase, nombre: str) -> str:
    resp = supabase.table("trabajadores").select("email").eq("nombre", nombre).execute()
    if resp.data and resp.data[0].get("email"):
        return resp.data[0]["email"]
    return ""


def get_project_name() -> str:
    return st.session_state.get("nombre_proyecto", "Edificio Colombo Americana")