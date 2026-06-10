import smtplib
import streamlit as st
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional, Dict


def get_smtp_for_email(email: str) -> Dict:
    email_lower = (email or "").lower().strip()
    providers = {
        "gmail.com": {"smtp_server": "smtp.gmail.com", "smtp_port": 587},
        "outlook.com": {"smtp_server": "smtp-mail.outlook.com", "smtp_port": 587},
        "hotmail.com": {"smtp_server": "smtp-mail.outlook.com", "smtp_port": 587},
        "live.com": {"smtp_server": "smtp-mail.outlook.com", "smtp_port": 587},
        "yahoo.com": {"smtp_server": "smtp.mail.yahoo.com", "smtp_port": 587},
        "icloud.com": {"smtp_server": "smtp.mail.me.com", "smtp_port": 587},
    }
    domain = email_lower.split("@")[-1] if "@" in email_lower else ""
    if domain in providers:
        return providers[domain]
    return {"smtp_server": "smtp.gmail.com", "smtp_port": 587}


def get_email_sender_config() -> dict:
    cfg = st.session_state.get("email_sender_config", {})
    if cfg and cfg.get("sender_email") and cfg.get("sender_password"):
        return cfg
    try:
        secrets = st.secrets.get("email", {})
        if secrets.get("SENDER_EMAIL") and secrets.get("SENDER_PASSWORD"):
            smtp = get_smtp_for_email(secrets["SENDER_EMAIL"])
            return {
                "smtp_server": smtp["smtp_server"],
                "smtp_port": smtp["smtp_port"],
                "sender_email": secrets["SENDER_EMAIL"],
                "sender_password": secrets["SENDER_PASSWORD"],
                "sender_name": secrets.get("SENDER_NAME", "ALMAGAN INGENIEROS"),
            }
    except Exception:
        pass
    try:
        import os
        email = os.environ.get("EMAIL_SENDER", "")
        password = os.environ.get("EMAIL_PASSWORD", "")
        if email and password:
            smtp = get_smtp_for_email(email)
            return {
                "smtp_server": os.environ.get("EMAIL_SMTP_SERVER", smtp["smtp_server"]),
                "smtp_port": int(os.environ.get("EMAIL_SMTP_PORT", smtp["smtp_port"])),
                "sender_email": email,
                "sender_password": password,
                "sender_name": os.environ.get("EMAIL_SENDER_NAME", "ALMAGAN INGENIEROS"),
            }
    except Exception:
        pass
    return {}


def save_email_sender_config(email: str, password: str, name: str = "ALMAGAN INGENIEROS"):
    smtp = get_smtp_for_email(email)
    cfg = {
        "smtp_server": smtp["smtp_server"],
        "smtp_port": smtp["smtp_port"],
        "sender_email": email.strip(),
        "sender_password": password.strip(),
        "sender_name": name,
    }
    st.session_state["email_sender_config"] = cfg
    return cfg


def is_email_configured() -> bool:
    cfg = get_email_sender_config()
    return bool(cfg and cfg.get("sender_email") and cfg.get("sender_password"))


def test_email_connection(email: str, password: str) -> Dict:
    smtp = get_smtp_for_email(email)
    try:
        server = smtplib.SMTP(smtp["smtp_server"], smtp["smtp_port"], timeout=10)
        server.starttls()
        server.login(email.strip(), password.strip())
        server.quit()
        return {"ok": True, "msg": f"Conexión exitosa con {smtp['smtp_server']}"}
    except smtplib.SMTPAuthenticationError:
        return {"ok": False, "msg": "Correo o contraseña incorrectos. Si es Gmail, use una Contraseña de Aplicación."}
    except Exception as e:
        return {"ok": False, "msg": str(e)}


def resolve_email(supabase, nombre: str) -> Optional[str]:
    resp = supabase.table("trabajadores").select("email").eq("nombre", nombre).execute()
    if resp.data and resp.data[0].get("email"):
        return resp.data[0]["email"]
    resp = supabase.table("usuarios").select("email,nombre_visible,usuario").eq("nombre_visible", nombre).execute()
    if resp.data and resp.data[0].get("email"):
        return resp.data[0]["email"]
    resp2 = supabase.table("usuarios").select("email,nombre_visible,usuario").eq("usuario", nombre).execute()
    if resp2.data and resp2.data[0].get("email"):
        return resp2.data[0]["email"]
    return None


def _build_task_email_body(tarea: Dict, nombre_asignado: str, proyecto: str) -> str:
    prioridad_emoji = {"Alta": "🔴", "Media": "🟡", "Baja": "🟢"}.get(tarea.get("prioridad", "Media"), "⚪")
    fecha_limite = tarea.get("fecha_limite", "Sin fecha limite")
    estado = tarea.get("estado", "Pendiente")
    notas = tarea.get("notas", "")
    creado_por = tarea.get("creado_por", "")

    html = f"""
    <html>
    <body style="font-family: 'Segoe UI', Arial, sans-serif; margin: 0; padding: 0; background-color: #f5f5f5;">
        <div style="max-width: 600px; margin: 20px auto; background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 20px rgba(0,0,0,0.1);">
            <div style="background: linear-gradient(135deg, #1A1A1A 0%, #333333 100%); padding: 28px 32px; text-align: center;">
                <h1 style="color: #FFFFFF; margin: 0; font-size: 24px;">ALMAGAN INGENIEROS</h1>
                <p style="color: #C9A227; margin: 6px 0 0 0; font-size: 14px;">Nueva Tarea Asignada</p>
            </div>
            <div style="padding: 28px 32px;">
                <p style="font-size: 16px; color: #333333;">Hola <strong>{nombre_asignado}</strong>,</p>
                <p style="font-size: 15px; color: #555555;">Se te ha asignado una nueva tarea en el proyecto <strong>{proyecto}</strong>:</p>
                <div style="background: #F8F8F8; border-left: 4px solid #C9A227; border-radius: 8px; padding: 18px 22px; margin: 20px 0;">
                    <table style="width: 100%; font-size: 14px; color: #333;">
                        <tr>
                            <td style="padding: 6px 0; width: 130px; color: #888;"><strong>ID Tarea:</strong></td>
                            <td style="padding: 6px 0;">{tarea.get('id_tarea', 'N/A')}</td>
                        </tr>
                        <tr>
                            <td style="padding: 6px 0; color: #888;"><strong>Descripcion:</strong></td>
                            <td style="padding: 6px 0;">{tarea.get('descripcion', '')}</td>
                        </tr>
                        <tr>
                            <td style="padding: 6px 0; color: #888;"><strong>Prioridad:</strong></td>
                            <td style="padding: 6px 0;">{prioridad_emoji} {tarea.get('prioridad', 'Media')}</td>
                        </tr>
                        <tr>
                            <td style="padding: 6px 0; color: #888;"><strong>Estado:</strong></td>
                            <td style="padding: 6px 0;">{estado}</td>
                        </tr>
                        <tr>
                            <td style="padding: 6px 0; color: #888;"><strong>Fecha Limite:</strong></td>
                            <td style="padding: 6px 0;">{fecha_limite}</td>
                        </tr>
                        {"<tr><td style='padding: 6px 0; color: #888;'><strong>Notas:</strong></td><td style='padding: 6px 0;'>{0}</td></tr>".format(notas) if notas else ""}
                        {"<tr><td style='padding: 6px 0; color: #888;'><strong>Creado por:</strong></td><td style='padding: 6px 0;'>{0}</td></tr>".format(creado_por) if creado_por else ""}
                    </table>
                </div>
                <p style="font-size: 13px; color: #888; margin-top: 24px;">Ingresa al sistema para ver mas detalles y actualizar el estado de la tarea.</p>
            </div>
            <div style="background-color: #1A1A1A; padding: 16px 32px; text-align: center;">
                <p style="color: #888; font-size: 12px; margin: 0;">2026 ALMAGAN INGENIEROS &mdash; Sistema de Gestion de Obras</p>
            </div>
        </div>
    </body>
    </html>
    """
    return html


def _build_task_email_plain(tarea: Dict, nombre_asignado: str, proyecto: str) -> str:
    fecha_limite = tarea.get("fecha_limite", "Sin fecha limite")
    notas = tarea.get("notas", "")
    creado_por = tarea.get("creado_por", "")
    text = (
        f"ALMAGAN INGENIEROS - Nueva Tarea Asignada\n\n"
        f"Hola {nombre_asignado},\n\n"
        f"Se te ha asignado una nueva tarea en el proyecto {proyecto}:\n\n"
        f"ID: {tarea.get('id_tarea', 'N/A')}\n"
        f"Descripcion: {tarea.get('descripcion', '')}\n"
        f"Prioridad: {tarea.get('prioridad', 'Media')}\n"
        f"Estado: {tarea.get('estado', 'Pendiente')}\n"
        f"Fecha Limite: {fecha_limite}\n"
    )
    if notas:
        text += f"Notas: {notas}\n"
    if creado_por:
        text += f"Creado por: {creado_por}\n"
    text += "\nIngresa al sistema para ver mas detalles."
    return text


def send_task_notification(supabase, tarea: Dict, proyecto: str) -> Dict:
    if not is_email_configured():
        return {"ok": False, "msg": "Correo no configurado"}
    asignado_a = tarea.get("asignado_a", "")
    email = resolve_email(supabase, asignado_a)
    if not email:
        return {"ok": False, "msg": f"No se encontro correo para '{asignado_a}'"}
    cfg = get_email_sender_config()
    html = _build_task_email_body(tarea, asignado_a, proyecto)
    plain = _build_task_email_plain(tarea, asignado_a, proyecto)
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"[ALMAGAN] Nueva tarea asignada: {tarea.get('id_tarea', '')}"
    msg["From"] = f"{cfg['sender_name']} <{cfg['sender_email']}>"
    msg["To"] = email
    msg.attach(MIMEText(plain, "plain", "utf-8"))
    msg.attach(MIMEText(html, "html", "utf-8"))
    try:
        with smtplib.SMTP(cfg["smtp_server"], cfg["smtp_port"], timeout=15) as server:
            server.starttls()
            server.login(cfg["sender_email"], cfg["sender_password"])
            server.sendmail(cfg["sender_email"], email, msg.as_string())
        return {"ok": True, "msg": f"Correo enviado a {email}", "email": email}
    except Exception as e:
        return {"ok": False, "msg": str(e)}


def send_task_notifications_bulk(supabase, tareas: List[Dict], proyecto: str) -> List[Dict]:
    results = []
    for tarea in tareas:
        result = send_task_notification(supabase, tarea, proyecto)
        results.append(result)
    return results