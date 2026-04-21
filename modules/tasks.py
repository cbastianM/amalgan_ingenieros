import streamlit as st
from supabase import Client
from database.queries import get_tareas, update_tarea_estado, insert_tarea, generar_id_tarea, delete_record, update_record
import pandas as pd
from datetime import datetime, date, timedelta
from utils.seed_data import render_seed_button, seed_tareas_data
from .profiles import get_current_profile


def _get_trabajadores(supabase: Client, proyecto: str):
    resp = supabase.table("asistencia").select("trabajador,cargo").eq("proyecto", proyecto).execute()
    if resp.data:
        df = pd.DataFrame(resp.data).drop_duplicates(subset=["trabajador"]).reset_index(drop=True)
        return df["trabajador"].tolist()
    return [
        "Carlos Ramírez", "José Martínez", "Miguel Torres", "Pedro Gómez",
        "Luis Hernández", "Andrés López", "Roberto Díaz", "Fernando Vargas",
        "Diego Morales", "Javier Castillo", "Raúl Peña", "Sandra Muñoz"
    ]


def render_mis_tareas(supabase: Client):
    PA = st.session_state.nombre_proyecto
    un = st.session_state.usuario_actual
    es_dir = st.session_state.rol_actual == "Director"

    st.markdown(f'''
    <div style="background:#1b5e20;padding:18px 28px;border-radius:12px;margin-bottom:18px;display:flex;align-items:center;gap:16px">
        <span style="font-size:32px">📋</span>
        <div>
            <div style="color:#fff;font-size:20px;font-weight:700">Gestión de Tareas</div>
            <div style="color:#a5d6a7;font-size:13px">{PA} - {un}</div>
        </div>
    </div>
    ''', unsafe_allow_html=True)

    trabajadores = _get_trabajadores(supabase, PA)
    current_profile = get_current_profile() or {}
    default_asignado = current_profile.get("asignado_default") if current_profile else None
    if default_asignado and default_asignado not in trabajadores:
        trabajadores.append(default_asignado)
    df_tareas = get_tareas(supabase, PA)

    tab_names = ["📋 Ver Tareas"]
    if es_dir:
        tab_names.append("➕ Asignar Tareas")
    tabs = st.tabs(tab_names)

    # ═══════════════════════════════════════════
    # TAB 1: VER / EDITAR TAREAS (todos)
    # ═══════════════════════════════════════════
    with tabs[0]:
        if df_tareas.empty:
            st.info("📭 No hay tareas registradas.")
            render_seed_button(supabase, PA, "Tareas", seed_tareas_data, key_prefix="tar")
            return

        if not es_dir and "asignado_a" in df_tareas.columns:
            df_tareas = df_tareas[df_tareas["asignado_a"] == un]

        if df_tareas.empty:
            st.info("📭 No tienes tareas asignadas.")
            return

        col_btns = st.columns(5)
        with col_btns[0]:
            if st.button("⏳ Pendientes", use_container_width=True, key="btn_est_pend"):
                st.session_state.tar_filtro_est = "Pendiente"
                st.rerun()
        with col_btns[1]:
            if st.button("🔄 En Progreso", use_container_width=True, key="btn_est_prog"):
                st.session_state.tar_filtro_est = "En progreso"
                st.rerun()
        with col_btns[2]:
            if st.button("✅ Completadas", use_container_width=True, key="btn_est_comp"):
                st.session_state.tar_filtro_est = "Completada"
                st.rerun()
        with col_btns[3]:
            if st.button("🔴 Alta", type="primary", use_container_width=True, key="btn_pri_alta"):
                st.session_state.tar_filtro_pri = "Alta"
                st.rerun()
        with col_btns[4]:
            if st.button("🔄 Limpiar", use_container_width=True, key="btn_clear_filt"):
                st.session_state.tar_filtro_pri = "Todas"
                st.session_state.tar_filtro_est = "Todos"
                st.rerun()

        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1:
            filtro_estado = st.selectbox("Estado:", ["Todos", "Pendiente", "En progreso", "Completada"],
                                         index=["Todos", "Pendiente", "En progreso", "Completada"].index(
                                             st.session_state.get("tar_filtro_est", "Todos")),
                                         key="tar_filtro_est")
        with col_f2:
            filtro_prioridad = st.selectbox("Prioridad:", ["Todas", "Alta", "Media", "Baja"],
                                             index=["Todas", "Alta", "Media", "Baja"].index(
                                                 st.session_state.get("tar_filtro_pri", "Todas")),
                                             key="tar_filtro_pri")
        with col_f3:
            filtro_buscar = st.text_input("Buscar:", key="tar_filtro_buscar")

        df_f = df_tareas.copy()
        if filtro_estado != "Todos" and "estado" in df_f.columns:
            df_f = df_f[df_f["estado"] == filtro_estado]
        if filtro_prioridad != "Todas" and "prioridad" in df_f.columns:
            df_f = df_f[df_f["prioridad"] == filtro_prioridad]
        if filtro_buscar and "descripcion" in df_f.columns:
            df_f = df_f[df_f["descripcion"].str.contains(filtro_buscar, case=False, na=False)]

        pendientes = len(df_f[df_f["estado"] == "Pendiente"]) if "estado" in df_f.columns and not df_f.empty else 0
        progreso = len(df_f[df_f["estado"] == "En progreso"]) if "estado" in df_f.columns and not df_f.empty else 0
        completadas = len(df_f[df_f["estado"] == "Completada"]) if "estado" in df_f.columns and not df_f.empty else 0

        k1, k2, k3 = st.columns(3)
        k1.metric("⏳ Pendientes", pendientes)
        k2.metric("🔄 En Progreso", progreso)
        k3.metric("✅ Completadas", completadas)

        st.markdown("---")
        st.markdown("**📋 Edite las tareas directamente en la tabla:**")

        cols_vis = ["id_tarea", "descripcion", "asignado_a", "prioridad", "estado", "fecha_limite", "notas"]
        cols_existentes = [c for c in cols_vis if c in df_f.columns]

        if df_f.empty:
            df_display = pd.DataFrame(columns=cols_existentes)
        else:
            df_display = df_f[cols_existentes].copy()
            if "fecha_limite" in df_display.columns:
                df_display["fecha_limite"] = pd.to_datetime(df_display["fecha_limite"], errors="coerce").dt.date

        config = {
            "id_tarea": st.column_config.TextColumn("ID", disabled=True, width="small"),
            "descripcion": st.column_config.TextColumn("Descripción*", width="large", required=True),
            "asignado_a": st.column_config.SelectboxColumn("Asignado a*", options=trabajadores, width="medium", required=True),
            "prioridad": st.column_config.SelectboxColumn("Prioridad", options=["Alta", "Media", "Baja"], width="small"),
            "estado": st.column_config.SelectboxColumn("Estado", options=["Pendiente", "En progreso", "Completada"], width="small"),
            "fecha_limite": st.column_config.DateColumn("Fecha Límite", width="small", format="DD/MM/YYYY"),
            "notas": st.column_config.TextColumn("Notas", width="medium"),
        }
        config_f = {k: v for k, v in config.items() if k in cols_existentes}

        df_edit = st.data_editor(
            df_display,
            column_config=config_f,
            hide_index=True,
            use_container_width=True,
            key="editor_tareas",
            num_rows="fixed",
            disabled=not es_dir
        )

        col_btn1, col_btn2, col_btn3 = st.columns([2, 2, 1])
        with col_btn1:
            if st.button("💾 Guardar Cambios", type="primary", use_container_width=True, key="btn_save_tareas"):
                guardados, actualizados = 0, 0
                for idx, row in df_edit.iterrows():
                    if not row.get("descripcion") or not row.get("asignado_a"):
                        continue
                    if pd.notna(row.get("id_tarea")) and row["id_tarea"]:
                        try:
                            update_data = {
                                "descripcion": row["descripcion"],
                                "asignado_a": row["asignado_a"],
                                "prioridad": row.get("prioridad", "Media"),
                                "estado": row.get("estado", "Pendiente"),
                                "notas": str(row.get("notas", "") or ""),
                            }
                            fl = row.get("fecha_limite")
                            if pd.notna(fl) and str(fl).strip():
                                try:
                                    update_data["fecha_limite"] = pd.to_datetime(str(fl)).strftime("%Y-%m-%d")
                                except Exception:
                                    update_data["fecha_limite"] = str(fl)
                            update_record(supabase, "tareas", "id_tarea", row["id_tarea"], update_data)
                            actualizados += 1
                        except Exception as e:
                            st.error(f"Error actualizando {row.get('id_tarea')}: {e}")
                if actualizados > 0:
                    st.success(f"✅ {actualizados} tarea(s) actualizada(s)")
                    st.cache_data.clear()
                    st.rerun()
                else:
                    st.info("ℹ️ No se detectaron cambios")

        with col_btn2:
            if st.button("🔄 Refrescar", use_container_width=True, key="btn_refresh_tar"):
                st.rerun()

        with col_btn3:
            if es_dir:
                if st.button("🗑️ Eliminar", use_container_width=True, key="btn_del_tar"):
                    st.session_state.mostrar_del_tar = True

        if es_dir and st.session_state.get("mostrar_del_tar", False):
            with st.expander("🗑️ Eliminar Tarea por ID", expanded=True):
                tarea_del = st.text_input("ID de tarea a eliminar:", key="tar_del_input", placeholder="Ej: T-001")
                col_d1, col_d2 = st.columns(2)
                with col_d1:
                    if st.button("Confirmar", type="primary", use_container_width=True, key="btn_conf_del"):
                        if tarea_del.strip():
                            try:
                                delete_record(supabase, "tareas", "id_tarea", tarea_del.strip())
                                st.success(f"✅ Tarea {tarea_del} eliminada")
                                st.session_state.mostrar_del_tar = False
                                st.cache_data.clear()
                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ Error: {e}")
                with col_d2:
                    if st.button("Cancelar", use_container_width=True, key="btn_cancel_del"):
                        st.session_state.mostrar_del_tar = False
                        st.rerun()

    # ═══════════════════════════════════════════
    # TAB 2: ASIGNAR TAREAS (solo Director)
    # ═══════════════════════════════════════════
    if es_dir and len(tabs) > 1:
        with tabs[1]:
            st.markdown("##### ➕ Crear y asignar tareas al personal del proyecto")
            st.info("Seleccione un trabajador, describa la tarea y defina prioridad y fecha límite.")

            col_asig1, col_asig2 = st.columns(2)
            with col_asig1:
                idx_def = 0
                if default_asignado in trabajadores:
                    idx_def = trabajadores.index(default_asignado)
                asignado_a = st.selectbox("👷 Asignar a:*", trabajadores, index=idx_def, key="tar_asig_persona")
                descripcion = st.text_area("📝 Descripción de la tarea:*", key="tar_asig_desc",
                                           placeholder="Ej: Revisión de planos estructurales Piso 5")
            with col_asig2:
                prioridad = st.selectbox("🔴 Prioridad:", ["Alta", "Media", "Baja"], index=1, key="tar_asig_pri")
                fecha_limite = st.date_input("📅 Fecha límite:", value=date.today() + timedelta(days=7), key="tar_asig_fecha")
                estado_inicial = st.selectbox("Estado inicial:", ["Pendiente", "En progreso"], key="tar_asig_estado")

            col_notas, col_creado = st.columns([2, 1])
            with col_notas:
                notas = st.text_input("📋 Notas:", key="tar_asig_notas", placeholder="Observaciones adicionales...")
            with col_creado:
                st.markdown(f"<div style='margin-top:28px; color:#666;'>Creado por: <b>{un}</b></div>", unsafe_allow_html=True)

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
                        st.success(f"✅ Tarea **{id_tarea}** creada y asignada a **{asignado_a}**")
                        st.cache_data.clear()
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error: {e}")

            # Asignación masiva
            st.markdown("---")
            st.markdown("##### 📋 Asignación masiva — Seleccione múltiples trabajadores:")

            trabajadores_sel = st.multiselect("Trabajadores:", trabajadores, key="tar_asig_masiva_lista")
            desc_masiva = st.text_area("Descripción (misma para todos):*", key="tar_asig_masiva_desc",
                                       placeholder="Ej: Inspección general de obra")
            col_m1, col_m2, col_m3 = st.columns(3)
            with col_m1:
                pri_masiva = st.selectbox("Prioridad:", ["Alta", "Media", "Baja"], index=1, key="tar_asig_masiva_pri")
            with col_m2:
                fecha_masiva = st.date_input("Fecha límite:", value=date.today() + timedelta(days=7), key="tar_asig_masiva_fecha")
            with col_m3:
                est_masiva = st.selectbox("Estado:", ["Pendiente", "En progreso"], key="tar_asig_masiva_estado")

            if st.button("💾 Asignar a todos los seleccionados", type="primary", use_container_width=True, key="btn_crear_masivo"):
                if not trabajadores_sel:
                    st.warning("⚠️ Seleccione al menos un trabajador")
                elif not desc_masiva.strip():
                    st.error("⚠️ La descripción es obligatoria")
                else:
                    creadas = 0
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
                        except Exception:
                            pass
                    if creadas > 0:
                        st.success(f"✅ {creadas} tareas creadas y asignadas")
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        st.error("❌ No se pudieron crear las tareas")
