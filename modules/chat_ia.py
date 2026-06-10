import streamlit as st
import requests
import json
from datetime import date
from database.queries import (
    get_actividades, get_avances, get_tareas, get_nomina,
    get_materiales, get_asistencia, get_trabajadores, get_proveedores
)
from utils.formatting import fmt_cop

DEEPSEEK_URL = "https://api.deepseek.com/v1/chat/completions"
MODEL = "deepseek-v4-flash"


def _build_contexto(supabase, proyecto) -> str:
    hoy = date.today().isoformat()

    # --- Actividades y avances ---
    df_act = get_actividades(supabase)
    df_av = get_avances(supabase, proyecto)
    ctx_parts = [f"PROYECTO: {proyecto}", f"FECHA ACTUAL: {hoy}", ""]

    if not df_act.empty:
        ctx_parts.append("--- ACTIVIDADES Y AVANCES ---")
        for _, r in df_act.iterrows():
            codigo = r.get("codigo", "")
            desc = r.get("descripcion", "")
            unidad = r.get("unidad", "")
            total = r.get("cantidad_total", 0)
            valor = r.get("valor_total", 0)
            ejec = 0.0
            if not df_av.empty:
                av_item = df_av[df_av["id_item"] == codigo]
                if not av_item.empty:
                    ejec = float(av_item["cantidad"].sum())
            pct = min(round(ejec / total * 100, 1) if float(total) > 0 else 0, 100)
            ctx_parts.append(
                f"  [{codigo}] {desc} | Unidad: {unidad} | Total: {total} {unidad} | "
                f"Ejecutado: {ejec:.1f} ({pct}%) | Presupuesto: {fmt_cop(valor)}"
            )
        total_val = float(df_act["valor_total"].sum())
        total_ejec = float(df_act["valor_total"].sum()) * 0  # placeholder
        ctx_parts.append(f"  TOTAL PRESUPUESTO ACTIVIDADES: {fmt_cop(total_val)}")
        ctx_parts.append("")

    # --- Tareas ---
    df_tar = get_tareas(supabase, proyecto)
    if not df_tar.empty:
        ctx_parts.append("--- TAREAS ---")
        for _, t in df_tar.iterrows():
            tid = t.get("id_tarea", "")
            desc = t.get("descripcion", "")
            estado = t.get("estado", "")
            prioridad = t.get("prioridad", "")
            asignado = t.get("asignado_a", "")
            fecha = t.get("fecha_limite", "")
            ctx_parts.append(
                f"  [{tid}] {desc} | Estado: {estado} | Prioridad: {prioridad} | "
                f"Asignado: {asignado} | Limite: {fecha}"
            )
        pend = int((df_tar["estado"] == "Pendiente").sum()) if "estado" in df_tar.columns else 0
        prog = int((df_tar["estado"] == "En progreso").sum()) if "estado" in df_tar.columns else 0
        comp = int((df_tar["estado"] == "Completada").sum()) if "estado" in df_tar.columns else 0
        ctx_parts.append(f"  RESUMEN: {len(df_tar)} tareas | {pend} pendientes | {prog} en progreso | {comp} completadas")
        ctx_parts.append("")

    # --- Inventario ---
    resp_inv = supabase.table("control_inventario").select("*").eq("proyecto", proyecto).execute()
    if resp_inv.data:
        import pandas as pd
        df_inv = pd.DataFrame(resp_inv.data)
        ctx_parts.append("--- INVENTARIO (ultimos 20 movimientos) ---")
        entradas = len(df_inv[df_inv["tipo_movimiento"] == "Entrada"]) if "tipo_movimiento" in df_inv.columns else 0
        salidas = len(df_inv[df_inv["tipo_movimiento"] == "Salida"]) if "tipo_movimiento" in df_inv.columns else 0
        ctx_parts.append(f"  Total movimientos: {len(df_inv)} | Entradas: {entradas} | Salidas: {salidas}")
        if not df_inv.empty:
            for _, m in df_inv.head(20).iterrows():
                tipo = m.get("tipo_movimiento", "")
                material = m.get("material", "")
                cantidad = m.get("cantidad", 0)
                unidad = m.get("unidad", "")
                fecha = m.get("fecha", "")
                obs = str(m.get("observaciones", "") or "")
                ctx_parts.append(
                    f"  [{tipo}] {material} x{cantidad} {unidad} | {fecha}{' | ' + obs if obs and obs != 'nan' else ''}"
                )
        ctx_parts.append("")

    # --- Maquinas ---
    resp_maq = supabase.table("control_maquinas").select("*").eq("proyecto", proyecto).execute()
    if resp_maq.data:
        import pandas as pd
        df_maq = pd.DataFrame(resp_maq.data)
        ctx_parts.append("--- CONTROL MAQUINAS ---")
        total_h = float(df_maq["horas_trabajadas"].sum()) if "horas_trabajadas" in df_maq.columns else 0
        total_m3 = float(df_maq["volumen_m3"].sum()) if "volumen_m3" in df_maq.columns else 0
        ctx_parts.append(f"  Total registros: {len(df_maq)} | Horas trabajadas: {total_h:.1f}h | Volumen: {total_m3:.1f} m3")
        for _, m in df_maq.tail(5).iterrows():
            ctx_parts.append(
                f"  {m.get('tipo_equipo','')} {m.get('placa','')} | {m.get('fecha','')} | "
                f"{m.get('horas_trabajadas',0)}h | {m.get('operador','')}"
            )
        ctx_parts.append("")

    # --- Nomina ---
    df_nom = get_nomina(supabase, proyecto)
    if not df_nom.empty and "valor" in df_nom.columns:
        ctx_parts.append("--- NOMINA ---")
        total_nom = float(df_nom["valor"].sum()) if "valor" in df_nom.columns else 0
        ctx_parts.append(f"  Total registros: {len(df_nom)} | Total pagado: {fmt_cop(total_nom)}")
        for _, n in df_nom.tail(10).iterrows():
            ctx_parts.append(
                f"  {n.get('trabajador','')} | {n.get('tipo','')} | {fmt_cop(n.get('valor',0))} | {n.get('fecha','')}"
            )
        ctx_parts.append("")

    # --- Materiales ---
    df_mat = get_materiales(supabase, proyecto)
    if not df_mat.empty:
        ctx_parts.append("--- SOLICITUDES DE MATERIALES ---")
        for _, m in df_mat.iterrows():
            ctx_parts.append(
                f"  [{m.get('estado','')}] {m.get('requerimiento','')} | {m.get('fecha','')} | por: {m.get('usuario','')}"
            )
        ctx_parts.append("")

    # --- Proveedores ---
    df_prov = get_proveedores(supabase)
    if not df_prov.empty:
        ctx_parts.append("--- PROVEEDORES ---")
        for _, p in df_prov.iterrows():
            ctx_parts.append(
                f"  {p.get('nombre','')} | NIT: {p.get('nit','')} | {p.get('categoria','')} | "
                f"Contacto: {p.get('contacto','')} | Tel: {p.get('telefono','')}"
            )
        ctx_parts.append("")

    # --- Asistencia (ultimos 3 dias) ---
    dfa = get_asistencia(supabase, proyecto)
    if not dfa.empty and "fecha" in dfa.columns:
        ctx_parts.append("--- ASISTENCIA (ultimos dias) ---")
        ultimas_fechas = sorted(dfa["fecha"].dropna().unique(), reverse=True)[:3]
        for f in ultimas_fechas:
            dia = dfa[dfa["fecha"] == f]
            pres = int((dia["estado"] == "Presente").sum()) if "estado" in dia.columns else 0
            aus = int((dia["estado"] == "Ausente").sum()) if "estado" in dia.columns else 0
            ctx_parts.append(f"  {f}: {pres} presentes, {aus} ausentes")

    return "\n".join(ctx_parts)


def _call_deepseek(messages: list) -> str:
    import os
    api_key = os.environ.get("DEEPSEEK_API_KEY", "")
    if not api_key:
        return "⚠️ DEEPSEEK_API_KEY no encontrada. Agregala como variable de entorno en Render (Settings > Environment)."
    if not api_key.startswith("sk-"):
        return f"⚠️ DEEPSEEK_API_KEY no parece valida (debe empezar con sk-...). Valor actual: {api_key[:8]}..."

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": MODEL,
        "messages": messages,
        "temperature": 0.3,
        "max_tokens": 2000
    }
    try:
        resp = requests.post(DEEPSEEK_URL, headers=headers, json=payload, timeout=45)
        if resp.status_code == 200:
            return resp.json()["choices"][0]["message"]["content"]
        elif resp.status_code == 401:
            return "❌ API Key invalida. Verifica tu DEEPSEEK_API_KEY."
        elif resp.status_code == 402:
            return "❌ Sin creditos en DeepSeek. Recarga saldo en platform.deepseek.com."
        else:
            return f"❌ Error {resp.status_code}: {resp.text[:300]}"
    except requests.exceptions.Timeout:
        return "⚠️ La consulta tardo demasiado. Intenta con una pregunta mas corta."
    except Exception as e:
        return f"❌ Error de conexion: {str(e)[:200]}"


def render_chat_ia(supabase):
    PA = st.session_state.nombre_proyecto
    usuario = st.session_state.usuario_actual
    es_dir = st.session_state.rol_actual == "Director"

    st.markdown(f'''
    <div style="background:linear-gradient(135deg, #1A1A1A 0%, #2D2D2D 100%);padding:18px 24px;border-radius:14px;margin-bottom:20px;border-left:5px solid #C9A227;display:flex;align-items:center;gap:16px">
        <div style="background:linear-gradient(135deg, #C9A227 0%, #B08D1C 100%);border-radius:50%;width:48px;height:48px;display:flex;align-items:center;justify-content:center;font-size:24px;flex-shrink:0">🤖</div>
        <div>
            <div style="color:#FFFFFF;font-size:18px;font-weight:700;font-family:Inter,sans-serif">Asistente IA — DeepSeek</div>
            <div style="color:#C9A227;font-size:12px;font-family:Inter,sans-serif">{PA} — Consultas inteligentes sobre tu proyecto</div>
        </div>
    </div>
    ''', unsafe_allow_html=True)

    if not es_dir:
        st.warning("Solo el Director tiene acceso al Asistente IA.")
        return

    if "chat_ia_historial" not in st.session_state:
        st.session_state.chat_ia_historial = {}
    if PA not in st.session_state.chat_ia_historial:
        st.session_state.chat_ia_historial[PA] = [
            {"role": "assistant", "content": f"🤖 Hola **{usuario}**, soy tu asistente IA. Preguntame sobre avances, tareas, inventario, nomina, maquinas, materiales o cualquier aspecto del proyecto **{PA}**."}
        ]

    with st.expander("ℹ️ Como usar el Asistente IA", expanded=False):
        st.markdown("""
        Puedes preguntar cosas como:
        - *"Cual es el avance general del proyecto?"*
        - *"Cuantas tareas pendientes hay y quien las tiene?"*
        - *"Cuanto se ha gastado en nomina este mes?"*
        - *"Que materiales estan pendientes por entregar?"*
        - *"Cual es la actividad con menos avance?"*
        - *"Resume el estado del inventario"*
        - *"Que proveedores tenemos de concreto?"*
        """)

    # Mostrar historial
    for msg in st.session_state.chat_ia_historial[PA]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Input del usuario
    if prompt := st.chat_input("Pregunta sobre tu proyecto...", key="chat_ia_input"):
        st.session_state.chat_ia_historial[PA].append({"role": "user", "content": prompt})

        with st.spinner("🧠 Analizando datos del proyecto..."):
            contexto = _build_contexto(supabase, PA)

        with st.spinner("🤖 Consultando a DeepSeek..."):
            system_msg = (
                "Eres un asistente experto en gestion de proyectos de construccion para ALMAGAN INGENIEROS. "
                "Responde de forma concisa, profesional y en espanol. "
                "Usa la informacion del contexto proporcionado para dar respuestas precisas con datos reales. "
                "Si te preguntan algo que no esta en el contexto, dilo claramente. "
                "Formatea cifras grandes con separadores de miles para mejor lectura. "
                "Cuando menciones valores en COP, usa formato como $1.500.000."
            )
            messages = [
                {"role": "system", "content": f"{system_msg}\n\nCONTEXTO DEL PROYECTO:\n{contexto}"},
                {"role": "user", "content": prompt}
            ]
            respuesta = _call_deepseek(messages)

        st.session_state.chat_ia_historial[PA].append({"role": "assistant", "content": respuesta})
        st.rerun()
