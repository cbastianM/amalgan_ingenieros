import streamlit as st
from database.queries import get_tareas, update_tarea_estado, insert_tarea, generar_id_tarea, delete_record, update_record
import pandas as pd
from datetime import datetime, date, timedelta
from utils.email_service import send_task_notification, send_task_notifications_bulk
from config.settings import is_email_configured
from .profiles import get_current_profile

ESTILOS_TARJETAS = """
<style>
.task-card {
    background: #FFFFFF;
    border: 2px solid #E8E8E8;
    border-radius: 12px;
    padding: 14px 16px;
    margin-bottom: 10px;
    transition: all 0.2s ease;
}
.task-card:hover {
    border-color: #C9A227;
    box-shadow: 0 2px 8px rgba(201,162,39,0.15);
}
.task-card.pendiente { border-left: 5px solid #FF9800; }
.task-card.en_progreso { border-left: 5px solid #2196F3; }
.task-card.completada { border-left: 5px solid #4CAF50; }
.task-title { font-size:15px; font-weight:600; color:#1A1A1A; margin-bottom:4px; }
.task-meta { font-size:12px; color:#888; }
.task-badge {
    display:inline-block; padding:2px 8px; border-radius:10px;
    font-size:11px; font-weight:600; margin-right:4px;
}
.badge-alta { background:#FFEBEE; color:#C62828; }
.badge-media { background:#FFF8E1; color:#F57F17; }
.badge-baja { background:#E8F5E9; color:#2E7D32; }
.badge-pendiente { background:#FFF3E0; color:#E65100; }
.badge-progreso { background:#E3F2FD; color:#1565C0; }
.badge-completada { background:#E8F5E9; color:#2E7D32; }
</style>
"""


def _get_trabajadores(supabase, proyecto: str):
    resp = supabase.table("asistencia").select("trabajador,cargo").eq("proyecto", proyecto).execute()
    if resp.data:
        df = pd.DataFrame(resp.data).drop_duplicates(subset=["trabajador"]).reset_index(drop=True)
        return df["trabajador"].tolist()
    return [
        "Carlos Ramírez", "José Martínez", "Miguel Torres", "Pedro Gómez",
        "Luis Hernández", "Andrés López", "Roberto Díaz", "Fernando Vargas",
        "Diego Morales", "Javier Castillo", "Raúl Peña", "Sandra Muñoz"
    ]


def _estado_css(estado):
    e = (estado or "").lower().replace(" ", "_")
    return {"pendiente": "pendiente", "en_progreso": "en_progreso", "completada": "completada"}.get(e, "")


def _prio_badge(prioridad):
    p = (prioridad or "Media")
    cls = {"Alta": "badge-alta", "Media": "badge-media", "Baja": "badge-baja"}.get(p, "badge-media")
    return f'<span class="task-badge {cls}">{p}</span>'


def _estado_badge(estado):
    e = (estado or "Pendiente")
    cls_map = {"Pendiente": "badge-pendiente", "En progreso": "badge-progreso", "Completada": "badge-completada"}
    cls = cls_map.get(e, "badge-pendiente")
    return f'<span class="task-badge {cls}">{e}</span>'


def render_mis_tareas(supabase):
    PA = st.session_state.nombre_proyecto
    un = st.session_state.usuario_actual
    es_dir = st.session_state.rol_actual == "Director"

    st.markdown(ESTILOS_TARJETAS, unsafe_allow_html=True)

    st.markdown(f'''
    <div style="background:#1b5e20;padding:14px 18px;border-radius:12px;margin-bottom:14px;display:flex;align-items:center;gap:12px">
        <span style="font-size:28px">📋</span>
        <div>
            <div style="color:#fff;font-size:18px;font-weight:700">Gestión de Tareas</div>
            <div style="color:#a5d6a7;font-size:12px">{PA} — {un}</div>
        </div>
    </div>
    ''', unsafe_allow_html=True)

    trabajadores = _get_trabajadores(supabase, PA)
    current_profile = get_current_profile() or {}
    default_asignado = current_profile.get("asignado_default") if current_profile else None
    if default_asignado and default_asignado not in trabajadores:
        trabajadores.append(default_asignado)
    df_tareas = get_tareas(supabase, PA)

    tab_names = ["📋 Tareas"]
    if es_dir:
        tab_names.append("➕ Nueva Tarea")
    tabs = st.tabs(tab_names)

    # ═══════════════════════════════════════════
    # TAB 1: VER / EDITAR TAREAS
    # ═══════════════════════════════════════════
    with tabs[0]:
        if df_tareas.empty:
            st.info("📭 No hay tareas registradas.")
            return

        if not es_dir and "asignado_a" in df_tareas.columns:
            df_tareas = df_tareas[df_tareas["asignado_a"] == un]

        if df_tareas.empty:
            st.info("📭 No tienes tareas asignadas.")
            return

        with st.expander("🔍 Filtros", expanded=False):
            col_f1, col_f2 = st.columns(2)
            with col_f1:
                filtro_estado = st.selectbox("Filtrar por estado:", ["Todos", "Pendiente", "En progreso", "Completada"],
                                             index=["Todos", "Pendiente", "En progreso", "Completada"].index(
                                                 st.session_state.get("tar_filtro_est", "Todos")),
                                             key="tar_filtro_est")
            with col_f2:
                filtro_prioridad = st.selectbox("Filtrar por prioridad:", ["Todas", "Alta", "Media", "Baja"],
                                                index=["Todas", "Alta", "Media", "Baja"].index(
                                                    st.session_state.get("tar_filtro_pri", "Todas")),
                                                key="tar_filtro_pri")

            if filtro_estado != "Todos" or filtro_prioridad != "Todas":
                if st.button("🔄 Quitar filtros", use_container_width=True, key="btn_clear_filt"):
                    st.session_state.tar_filtro_est = "Todos"
                    st.session_state.tar_filtro_pri = "Todas"
                    st.rerun()

        df_f = df_tareas.copy()
        if filtro_estado != "Todos" and "estado" in df_f.columns:
            df_f = df_f[df_f["estado"] == filtro_estado]
        if filtro_prioridad != "Todas" and "prioridad" in df_f.columns:
            df_f = df_f[df_f["prioridad"] == filtro_prioridad]

        # Resumen rapido
        pendientes = len(df_f[df_f["estado"] == "Pendiente"]) if "estado" in df_f.columns and not df_f.empty else 0
        progreso = len(df_f[df_f["estado"] == "En progreso"]) if "estado" in df_f.columns and not df_f.empty else 0
        completadas = len(df_f[df_f["estado"] == "Completada"]) if "estado" in df_f.columns and not df_f.empty else 0
        k1, k2 = st.columns(2)
        k1.metric("⏳ Pendientes", pendientes)
        k2.metric("🔄 En Progreso", progreso)
        k1, k2 = st.columns(2)
        k1.metric("✅ Completadas", completadas)

        st.markdown("---")

        if df_f.empty:
            st.info("📭 No hay tareas con esos filtros.")
        else:
            # Ordenar: Pendiente primero, luego En progreso, luego Completada
            orden_estado = {"Pendiente": 0, "En progreso": 1, "Completada": 2}
            orden_prio = {"Alta": 0, "Media": 1, "Baja": 2}
            df_f = df_f.copy()
            if "estado" in df_f.columns:
                df_f["_orden_est"] = df_f["estado"].map(orden_estado).fillna(3)
            if "prioridad" in df_f.columns:
                df_f["_orden_pri"] = df_f["prioridad"].map(orden_prio).fillna(3)
            sort_cols = [c for c in ["_orden_est", "_orden_pri"] if c in df_f.columns]
            if sort_cols:
                df_f = df_f.sort_values(sort_cols).reset_index(drop=True)
            for c in ["_orden_est", "_orden_pri"]:
                df_f.drop(columns=[c], errors="ignore", inplace=True)

            card_key = 0
            rows = [df_f.iloc[i:i+2] for i in range(0, len(df_f), 2)]
            for row_pair in rows:
                left_col, right_col = st.columns(2)
                for col_idx, (idx, row) in enumerate(row_pair.iterrows()):
                    current_col = left_col if col_idx == 0 else right_col
                    tid = row.get("id_tarea", "")
                    desc = row.get("descripcion", "")
                    asignado = row.get("asignado_a", "")
                    prioridad = row.get("prioridad", "Media")
                    estado = row.get("estado", "Pendiente")
                    fecha = row.get("fecha_limite", "")
                    notas = row.get("notas", "")
                    creado = row.get("creado_por", "")

                    try:
                        if pd.notna(fecha) and str(fecha).strip():
                            fecha_str = pd.to_datetime(str(fecha)).strftime("%d/%m/%Y")
                        else:
                            fecha_str = "Sin fecha"
                    except Exception:
                        fecha_str = str(fecha) if pd.notna(fecha) else "Sin fecha"

                    header = f"{_prio_badge(prioridad)} {_estado_badge(estado)}"
                    preview = f"{tid} — {desc[:40]}{'...' if len(str(desc)) > 40 else ''}"

                    with current_col:
                        with st.expander(f"{preview}", expanded=False):
                            st.markdown(header, unsafe_allow_html=True)
                            st.caption(f"👤 {asignado}  |  📅 {fecha_str}")
                            if not es_dir:
                                st.markdown(f"**Descripción:** {desc}")
                                c1, c2 = st.columns(2)
                                with c1:
                                    st.markdown(f"**Asignado a:** {asignado}")
                                    st.markdown(f"**Estado:** {estado}")
                                with c2:
                                    st.markdown(f"**Prioridad:** {prioridad}")
                                    if creado:
                                        st.markdown(f"**Creado por:** {creado}")
                                if notas and str(notas).strip():
                                    st.caption(f"📝 {notas}")
                            else:
                                new_desc = st.text_area("Descripción*", value=str(desc) if pd.notna(desc) else "",
                                                        key=f"tar_desc_{card_key}", height=70)
                                c1, c2 = st.columns(2)
                                with c1:
                                    new_asignado = st.selectbox("Asignar a*", trabajadores,
                                                                index=trabajadores.index(asignado) if asignado in trabajadores else 0,
                                                                key=f"tar_asig_{card_key}")
                                    new_estado = st.selectbox("Estado", ["Pendiente", "En progreso", "Completada"],
                                                              index=["Pendiente", "En progreso", "Completada"].index(estado) if estado in ["Pendiente", "En progreso", "Completada"] else 0,
                                                              key=f"tar_est_{card_key}")
                                with c2:
                                    new_prioridad = st.selectbox("Prioridad", ["Alta", "Media", "Baja"],
                                                                 index=["Alta", "Media", "Baja"].index(prioridad) if prioridad in ["Alta", "Media", "Baja"] else 1,
                                                                 key=f"tar_pri_{card_key}")
                                    new_fecha = st.date_input("Fecha límite",
                                                               value=pd.to_datetime(fecha).date() if pd.notna(fecha) and str(fecha).strip() else date.today() + timedelta(days=7),
                                                               key=f"tar_fecha_{card_key}")
                                new_notas = st.text_input("Notas", value=str(notas) if pd.notna(notas) else "",
                                                          key=f"tar_notas_{card_key}")

                                btn_c1, btn_c2 = st.columns(2)
                                with btn_c1:
                                    if st.button("💾 Guardar", type="primary", use_container_width=True, key=f"tar_save_{card_key}"):
                                        update_data = {
                                            "descripcion": new_desc,
                                            "asignado_a": new_asignado,
                                            "prioridad": new_prioridad,
                                            "estado": new_estado,
                                            "notas": new_notas,
                                            "fecha_limite": new_fecha.isoformat(),
                                        }
                                        try:
                                            update_record(supabase, "tareas", "id_tarea", tid, update_data)
                                            st.success(f"✅ Tarea {tid} actualizada")
                                            st.cache_data.clear()
                                            st.rerun()
                                        except Exception as e:
                                            st.error(f"❌ Error: {e}")
                                with btn_c2:
                                    if st.button("🗑️ Eliminar", use_container_width=True, key=f"tar_del_{card_key}"):
                                        try:
                                            delete_record(supabase, "tareas", "id_tarea", tid)
                                            st.success(f"✅ Tarea {tid} eliminada")
                                            st.cache_data.clear()
                                            st.rerun()
                                        except Exception as e:
                                            st.error(f"❌ Error: {e}")

                                if creado:
                                    st.caption(f"Creado por: {creado}")

                    card_key += 1

    # ═══════════════════════════════════════════
    # TAB 2: NUEVA TAREA (solo Director)
    # ═══════════════════════════════════════════
    if es_dir and len(tabs) > 1:
        with tabs[1]:
            with st.expander("➕ Crear tarea", expanded=True):
                st.markdown("##### ➕ Crear y asignar tarea")

                idx_def = 0
                if default_asignado in trabajadores:
                    idx_def = trabajadores.index(default_asignado)

                col1, col2 = st.columns(2)
                with col1:
                    asignado_a = st.selectbox("👷 Asignar a*", trabajadores, index=idx_def, key="tar_asig_persona")
                    prioridad = st.selectbox("🔴 Prioridad", ["Alta", "Media", "Baja"], index=1, key="tar_asig_pri")
                with col2:
                    estado_inicial = st.selectbox("Estado inicial", ["Pendiente", "En progreso"], key="tar_asig_estado")
                    fecha_limite = st.date_input("📅 Fecha límite", value=date.today() + timedelta(days=7), key="tar_asig_fecha")

                descripcion = st.text_area("📝 Descripción de la tarea*", key="tar_asig_desc",
                                           placeholder="Ej: Revisión de planos estructurales Piso 5")
                notas = st.text_input("📋 Notas", key="tar_asig_notas", placeholder="Observaciones adicionales...")

                if st.button("💾 Crear Tarea", type="primary", use_container_width=True, key="btn_crear_tarea_dir"):
                    if not descripcion.strip():
                        st.error("⚠️ La descripción es obligatoria")
                    else:
                        id_tarea = generar_id_tarea(supabase, PA)
                        data = {
                            "id_tarea": id_tarea,
                            "proyecto": PA,
                            "descripcion": descripcion.strip(),
                            "fecha_limite": fecha_limite.isoformat(),
                            "prioridad": prioridad,
                            "estado": estado_inicial,
                            "asignado_a": asignado_a,
                            "notas": notas.strip(),
                            "creado_por": un,
                        }
                        try:
                            insert_tarea(supabase, data)
                            email_result = send_task_notification(supabase, data, PA)
                            st.success(f"✅ Tarea **{id_tarea}** creada y asignada a **{asignado_a}**")
                            if email_result["ok"]:
                                st.info(f"📧 {email_result['msg']}")
                            elif is_email_configured():
                                st.warning(f"⚠️ Correo: {email_result['msg']}")
                            st.cache_data.clear()
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Error: {e}")

            with st.expander("📋 Asignación masiva", expanded=False):
                trabajadores_sel = st.multiselect("Trabajadores*", trabajadores, key="tar_asig_masiva_lista")
                desc_masiva = st.text_area("Descripción (misma para todos)*", key="tar_asig_masiva_desc",
                                           placeholder="Ej: Inspección general de obra")
                col_m1, col_m2 = st.columns(2)
                with col_m1:
                    pri_masiva = st.selectbox("Prioridad", ["Alta", "Media", "Baja"], index=1, key="tar_asig_masiva_pri")
                    est_masiva = st.selectbox("Estado", ["Pendiente", "En progreso"], key="tar_asig_masiva_estado")
                with col_m2:
                    fecha_masiva = st.date_input("Fecha límite", value=date.today() + timedelta(days=7), key="tar_asig_masiva_fecha")

                if st.button("💾 Asignar a seleccionados", type="primary", use_container_width=True, key="btn_crear_masivo"):
                    if not trabajadores_sel:
                        st.warning("⚠️ Seleccione al menos un trabajador")
                    elif not desc_masiva.strip():
                        st.error("⚠️ La descripción es obligatoria")
                    else:
                        creadas = 0
                        tareas_data = []
                        for trab in trabajadores_sel:
                            id_tarea = generar_id_tarea(supabase, PA)
                            data = {
                                "id_tarea": id_tarea,
                                "proyecto": PA,
                                "descripcion": desc_masiva.strip(),
                                "fecha_limite": fecha_masiva.isoformat(),
                                "prioridad": pri_masiva,
                                "estado": est_masiva,
                                "asignado_a": trab,
                                "notas": "",
                                "creado_por": un,
                            }
                            try:
                                insert_tarea(supabase, data)
                                creadas += 1
                                tareas_data.append(data)
                            except Exception:
                                pass
                        if creadas > 0:
                            email_results = send_task_notifications_bulk(supabase, tareas_data, PA)
                            emails_ok = sum(1 for r in email_results if r["ok"])
                            emails_fail = sum(1 for r in email_results if not r["ok"])
                            st.success(f"✅ {creadas} tareas creadas y asignadas")
                            if emails_ok > 0:
                                st.info(f"📧 Correos enviados: {emails_ok} de {creadas}")
                            if emails_fail > 0 and is_email_configured():
                                st.warning(f"⚠️ {emails_fail} correo(s) no enviados - verifique los emails de los trabajadores")
                            st.cache_data.clear()
                            st.rerun()
                        else:
                            st.error("❌ No se pudieron crear las tareas")