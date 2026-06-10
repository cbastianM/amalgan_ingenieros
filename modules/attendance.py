# modules/attendance.py
import streamlit as st
import pandas as pd
from datetime import date
from database.queries import get_asistencia, update_record, delete_record, insert_record

ESTADOS = ["Presente", "Ausente", "Permiso", "Vacaciones"]


def _get_trabajadores_base(supabase, proyecto: str):
    resp = supabase.table("asistencia").select("trabajador,cargo").eq("proyecto", proyecto).execute()
    if resp.data:
        df = pd.DataFrame(resp.data).drop_duplicates(subset=["trabajador"]).reset_index(drop=True)
        df["activo"] = True
        return df[["trabajador", "cargo", "activo"]]
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


def render_asistencia(supabase):
    PA = st.session_state.nombre_proyecto
    usuario = st.session_state.usuario_actual

    st.markdown(f'''
    <div style="background:#00695c;padding:14px 24px;border-radius:10px;margin-bottom:14px;display:flex;align-items:center;gap:12px">
        <span style="font-size:28px">👷</span>
        <div>
            <div style="color:#fff;font-size:18px;font-weight:700">Control de Asistencia</div>
            <div style="color:#b2dfdb;font-size:12px">{PA}</div>
        </div>
    </div>
    ''', unsafe_allow_html=True)

    with st.expander("📅 Registrar asistencia", expanded=True):
        col_fecha, col_acciones = st.columns(2)
        with col_fecha:
            fecha_reg = st.date_input("📅 Fecha", value=date.today(), key="ast_fecha_reg")
        with col_acciones:
            col_btn_a, col_btn_b = st.columns(2)
            with col_btn_a:
                if st.button("✅ Todos Presente", type="primary", use_container_width=True, key="btn_ast_todosp"):
                    _registrar_masivo(supabase, PA, fecha_reg, usuario, "Presente")
            with col_btn_b:
                if st.button("❌ Todos Ausente", type="secondary", use_container_width=True, key="btn_ast_todosa"):
                    _registrar_masivo(supabase, PA, fecha_reg, usuario, "Ausente")

        col_limpiar, _ = st.columns([1, 1])
        with col_limpiar:
            if st.button("🗑️ Limpiar Fecha", type="secondary", use_container_width=True, key="btn_ast_clear"):
                _limpiar_fecha(supabase, PA, fecha_reg)

        default_estado = st.session_state.get("ast_estado_def", "Presente")

        df_base = _get_trabajadores_base(supabase, PA)
        df_existente = get_asistencia(supabase, PA, fecha_reg)

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

        cols_vis = ["trabajador", "cargo", "estado"]
        config = {
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

        col_btn1, col_btn2 = st.columns([3, 1])
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
                        try:
                            update_record(supabase, "asistencia", "id", id_reg, {"estado": estado})
                            actualizados += 1
                        except Exception:
                            pass
                    else:
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
            if st.button("🔄", use_container_width=True, key="btn_refresh_ast"):
                st.rerun()

    with st.expander("📊 Resumen", expanded=False):
        dfa = get_asistencia(supabase, PA, fecha_reg)
        if not dfa.empty and "estado" in dfa.columns:
            pres = int((dfa["estado"] == "Presente").sum())
            aus = int((dfa["estado"] == "Ausente").sum())
            perm = int((dfa["estado"] == "Permiso").sum())
            vac = int((dfa["estado"] == "Vacaciones").sum())
            k1, k2 = st.columns(2)
            k1.metric("✅ Presentes", pres)
            k2.metric("❌ Ausentes", aus)
            k1, k2 = st.columns(2)
            k1.metric("📝 Permisos", perm)
            k2.metric("🏖️ Vacaciones", vac)
        else:
            st.info("📭 Aún no hay registros para esta fecha")


def _registrar_masivo(supabase, proyecto: str, fecha: date, usuario: str, estado: str):
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


def _limpiar_fecha(supabase, proyecto: str, fecha: date):
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