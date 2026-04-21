# modules/attendance.py
import streamlit as st
from supabase import Client
import pandas as pd
from datetime import date
from database.queries import get_asistencia, update_record, delete_record, insert_record
from utils.seed_data import render_seed_button, seed_asistencia_data

ESTADOS = ["Presente", "Ausente", "Permiso", "Vacaciones"]


def _get_trabajadores_base(supabase: Client, proyecto: str):
    """Obtiene la lista base de trabajadores activos del proyecto."""
    # Intenta obtener de trabajadores registrados en asistencias previas
    resp = supabase.table("asistencia").select("trabajador,cargo").eq("proyecto", proyecto).execute()
    if resp.data:
        df = pd.DataFrame(resp.data).drop_duplicates(subset=["trabajador"]).reset_index(drop=True)
        df["activo"] = True
        return df[["trabajador", "cargo", "activo"]]
    # Fallback: trabajadores por defecto
    return pd.DataFrame([
        {"trabajador": "Carlos Ramírez", "cargo": "Maestro de obra", "activo": True},
        {"trabajador": "José Martínez", "cargo": "Albañil", "activo": True},
        {"trabajador": "Miguel Torres", "cargo": "Ayudante general", "activo": True},
        {"trabajador": "Pedro Gómez", "cargo": "Herrero", "activo": True},
        {"trabajador": "Luis Hernández", "cargo": "Electricista", "activo": True},
        {"trabajador": "Andrés López", "cargo": "Plomero", "activo": True},
        {"trabajador": "Roberto Díaz", "cargo": "Carpintero", "activo": True},
        {"trabajador": "Fernando Vargas", "cargo": "Pintor", "activo": True},
        {"trabajador": "Diego Morales", "cargo": "Ayudante general", "activo": True},
        {"trabajador": "Javier Castillo", "cargo": "Operador de maquinaria", "activo": True},
        {"trabajador": "Raúl Peña", "cargo": "Maestro de obra", "activo": True},
        {"trabajador": "Sandra Muñoz", "cargo": "Auxiliar de obra", "activo": True},
    ])


def render_asistencia(supabase: Client):
    PA = st.session_state.nombre_proyecto
    usuario = st.session_state.usuario_actual

    st.markdown(f'''
    <div style="background:#00695c;padding:18px 28px;border-radius:12px;margin-bottom:18px;display:flex;align-items:center;gap:16px">
        <span style="font-size:32px">👷</span>
        <div>
            <div style="color:#fff;font-size:20px;font-weight:700">Control de Asistencia</div>
            <div style="color:#b2dfdb;font-size:13px">Registro diario - {PA}</div>
        </div>
    </div>
    ''', unsafe_allow_html=True)

    # ═══ FECHA DE ASISTENCIA ═══
    fecha_reg = st.date_input("📅 Fecha de asistencia:", value=date.today(), key="ast_fecha_reg")

    # ═══ BOTONES DE ACCIÓN RÁPIDA ═══
    col_btns = st.columns(5)
    with col_btns[0]:
        if st.button("✅ Todos Presente", type="primary", use_container_width=True, key="btn_ast_todosp"):
            _registrar_masivo(supabase, PA, fecha_reg, usuario, "Presente")
    with col_btns[1]:
        if st.button("❌ Todos Ausente", type="secondary", use_container_width=True, key="btn_ast_todosa"):
            _registrar_masivo(supabase, PA, fecha_reg, usuario, "Ausente")
    with col_btns[2]:
        if st.button("📝 Marcar Permiso", type="secondary", use_container_width=True, key="btn_ast_perm"):
            st.session_state.ast_estado_def = "Permiso"
            st.rerun()
    with col_btns[3]:
        if st.button("🏖️ Marcar Vacaciones", type="secondary", use_container_width=True, key="btn_ast_vac"):
            st.session_state.ast_estado_def = "Vacaciones"
            st.rerun()
    with col_btns[4]:
        if st.button("🗑️ Limpiar Fecha", type="secondary", use_container_width=True, key="btn_ast_clear"):
            _limpiar_fecha(supabase, PA, fecha_reg)

    default_estado = st.session_state.get("ast_estado_def", "Presente")

    # ═══ TABLA DE REGISTRO MASIVO ═══
    st.markdown("---")
    st.markdown("**📋 Registro de Asistencia — Haga clic en la celda de Estado para cambiar:**")

    # Obtener base de trabajadores y asistencias existentes para esa fecha
    df_base = _get_trabajadores_base(supabase, PA)
    df_existente = get_asistencia(supabase, PA, fecha_reg)

    # Merge para mostrar estado actual si existe
    if not df_existente.empty and "trabajador" in df_existente.columns:
        df_merge = df_base.merge(
            df_existente[["trabajador", "estado", "id"]].rename(columns={"id": "id_registro"}),
            on="trabajador", how="left"
        )
        df_merge["estado"] = df_merge["estado"].fillna(default_estado)
        df_merge["ya_registrado"] = df_merge["id_registro"].notna()
    else:
        df_merge = df_base.copy()
        df_merge["estado"] = default_estado
        df_merge["id_registro"] = None
        df_merge["ya_registrado"] = False

    # Agregar columna indicador visual
    df_merge["_ind"] = df_merge["ya_registrado"].apply(lambda x: "✅" if x else "⏳")

    # Configuración de columnas visibles (solo las esenciales)
    cols_vis = ["_ind", "trabajador", "cargo", "estado"]
    config = {
        "_ind": st.column_config.TextColumn("", disabled=True, width="small"),
        "trabajador": st.column_config.TextColumn("Trabajador", disabled=True, width="medium"),
        "cargo": st.column_config.TextColumn("Cargo", disabled=True, width="medium"),
        "estado": st.column_config.SelectboxColumn("Estado", options=ESTADOS, width="small"),
    }

    df_edit = st.data_editor(
        df_merge[cols_vis],
        column_config=config,
        hide_index=True,
        use_container_width=True,
        key="editor_ast_masivo",
        num_rows="dynamic"
    )

    # Botón guardar cambios
    col_btn1, col_btn2, col_btn3 = st.columns([2, 2, 1])
    with col_btn1:
        if st.button("💾 Guardar Asistencia", type="primary", use_container_width=True, key="btn_save_ast"):
            guardados, actualizados = 0, 0
            for idx, row in df_edit.iterrows():
                trab = row["trabajador"]
                estado = row["estado"]
                cargo = df_merge.loc[idx, "cargo"]
                ya_reg = df_merge.loc[idx, "ya_registrado"]
                id_reg = df_merge.loc[idx, "id_registro"]

                if ya_reg and id_reg:
                    # Actualizar existente
                    try:
                        update_record(supabase, "asistencia", "id", id_reg, {"estado": estado})
                        actualizados += 1
                    except Exception:
                        pass
                else:
                    # Insertar nuevo
                    try:
                        data = {
                            "proyecto": PA,
                            "fecha": fecha_reg.isoformat(),
                            "trabajador": trab,
                            "cargo": cargo,
                            "estado": estado,
                            "usuario": usuario
                        }
                        insert_record(supabase, "asistencia", data)
                        guardados += 1
                    except Exception:
                        pass
            total = guardados + actualizados
            if total > 0:
                st.success(f"✅ {guardados} nuevos, {actualizados} actualizados")
                st.cache_data.clear()
                st.rerun()
            else:
                st.info("ℹ️ No se realizaron cambios")

    with col_btn2:
        if st.button("🔄 Refrescar", use_container_width=True, key="btn_refresh_ast"):
            st.rerun()

    with col_btn3:
        # Botón para eliminar registros de esta fecha
        if st.button("🗑️ Borrar Todo", use_container_width=True, key="btn_del_fecha"):
            _limpiar_fecha(supabase, PA, fecha_reg)

    # ═══ RESUMEN DE LA FECHA ═══
    st.markdown("---")
    st.markdown(f"**📊 Resumen del {fecha_reg.strftime('%d/%m/%Y')}:**")
    dfa = get_asistencia(supabase, PA, fecha_reg)
    if not dfa.empty and "estado" in dfa.columns:
        pres = int((dfa["estado"] == "Presente").sum())
        aus = int((dfa["estado"] == "Ausente").sum())
        perm = int((dfa["estado"] == "Permiso").sum())
        vac = int((dfa["estado"] == "Vacaciones").sum())
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("✅ Presentes", pres)
        k2.metric("❌ Ausentes", aus)
        k3.metric("📝 Permisos", perm)
        k4.metric("🏖️ Vacaciones", vac)
    else:
        st.info("📭 Aún no hay registros para esta fecha")

    render_seed_button(supabase, PA, "Asistencia", seed_asistencia_data, key_prefix="ast")


def _registrar_masivo(supabase: Client, proyecto: str, fecha: date, usuario: str, estado: str):
    """Registra a todos los trabajadores base con el mismo estado."""
    df_base = _get_trabajadores_base(supabase, proyecto)
    df_existente = get_asistencia(supabase, proyecto, fecha)
    existentes = set()
    if not df_existente.empty and "trabajador" in df_existente.columns:
        existentes = set(df_existente["trabajador"].tolist())

    guardados = 0
    for _, row in df_base.iterrows():
        if row["trabajador"] not in existentes:
            try:
                data = {
                    "proyecto": proyecto,
                    "fecha": fecha.isoformat(),
                    "trabajador": row["trabajador"],
                    "cargo": row["cargo"],
                    "estado": estado,
                    "usuario": usuario
                }
                insert_record(supabase, "asistencia", data)
                guardados += 1
            except Exception:
                pass
    if guardados > 0:
        st.success(f"✅ {guardados} trabajadores marcados como {estado}")
        st.cache_data.clear()
        st.rerun()
    else:
        st.info("ℹ️ Todos los trabajadores ya tenían registro para esta fecha")


def _limpiar_fecha(supabase: Client, proyecto: str, fecha: date):
    """Elimina todos los registros de asistencia de una fecha."""
    try:
        resp = supabase.table("asistencia").select("id").eq("proyecto", proyecto).eq("fecha", fecha.isoformat()).execute()
        if resp.data:
            for r in resp.data:
                delete_record(supabase, "asistencia", "id", r["id"])
            st.success(f"✅ Registros del {fecha.strftime('%d/%m/%Y')} eliminados")
            st.cache_data.clear()
            st.rerun()
        else:
            st.info("ℹ️ No había registros para eliminar")
    except Exception as e:
        st.error(f"❌ Error al eliminar: {e}")