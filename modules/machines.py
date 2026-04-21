# modules/machines.py
import streamlit as st
from supabase import Client
import pandas as pd
from datetime import datetime, time, date
from database.queries import insert_control_maquinas, update_record, delete_record
from utils.seed_data import render_seed_button, seed_maquinas_data

EQUIPOS_RAPIDOS = [
    ("🚛 Volqueta", "Volqueta"),
    ("⛏️ Retroexcavadora", "Retroexcavadora"),
    ("🚜 Mototrac", "Mototrac"),
    ("🏗️ Grúa", "Grúa"),
]

MATERIALES_TRANSPORTE = [
    ("🏔️ Gravilla", "Gravilla"), ("🌍 Tierra", "Tierra"), ("🏜️ Arena", "Arena"), ("🧱 Escombros", "Escombros"),
]

def render_controlador(supabase: Client):
    PA = st.session_state.nombre_proyecto
    usuario = st.session_state.usuario_actual

    st.markdown(f'''
    <div style="background:#1565c0;padding:18px 28px;border-radius:12px;margin-bottom:24px;display:flex;align-items:center;gap:16px">
        <span style="font-size:32px">🚜</span>
        <div>
            <div style="color:#fff;font-size:20px;font-weight:700">Control de Máquinas</div>
            <div style="color:#bbdefb;font-size:13px">Equipos y Volquetas - {PA}</div>
        </div>
    </div>
    ''', unsafe_allow_html=True)

    col_tipo1, col_tipo2 = st.columns(2)
    with col_tipo1:
        btn_vol = st.button("🚛 Volqueta", type="primary", use_container_width=True, key="btn_tipo_vol")
    with col_tipo2:
        btn_eq = st.button("⚙️ Equipo", type="primary", use_container_width=True, key="btn_tipo_eq")

    if btn_vol:
        st.session_state.maq_tipo = "Volqueta"
    elif btn_eq:
        st.session_state.maq_tipo = "Equipo"

    tipo_default = st.session_state.get("maq_tipo", "Volqueta")

    if tipo_default == "Volqueta":
        col_btns = st.columns(4)
        for i, (label, mat) in enumerate(MATERIALES_TRANSPORTE):
            with col_btns[i]:
                if st.button(label, key=f"qmatm_{mat}", use_container_width=True):
                    st.session_state.maq_mat_sel = mat
                    st.rerun()

        default_mat = st.session_state.get("maq_mat_sel", "")
        with st.form("form_volqueta"):
            col1, col2 = st.columns(2)
            with col1:
                placa = st.text_input("Placa:", placeholder="ej: ABC123", key="maq_placa_new").upper()
                material = st.text_input("Material:", value=default_mat, key="maq_mat_new")
                volumen = st.number_input("Volumen por viaje (m³):", min_value=0.0, step=0.5, key="maq_vol_new")
            with col2:
                operador = st.text_input("Operador:", key="maq_oper_new")
                num_viajes = st.number_input("Número de viajes:", min_value=1, step=1, value=1, key="maq_viajes_new")
                observaciones = st.text_area("Observaciones:", key="maq_obs_new")

            guardar = st.form_submit_button("💾 Registrar Volqueta", type="primary", use_container_width=True)
            if guardar and placa and material and volumen > 0:
                volumen_total = volumen * num_viajes
                data = {
                    "proyecto": PA, "fecha": date.today().isoformat(), "tipo_equipo": "Volqueta",
                    "placa": placa.strip(), "operador": operador.strip(),
                    "hora_inicio": datetime.now().strftime("%H:%M:%S"), "hora_fin": datetime.now().strftime("%H:%M:%S"),
                    "horas_trabajadas": 0, "material_transportado": material.strip(),
                    "volumen_m3": volumen_total, "numero_viajes": num_viajes,
                    "observaciones": observaciones.strip(), "usuario": usuario
                }
                try:
                    insert_control_maquinas(supabase, data)
                    st.success(f"✅ Registrados {num_viajes} viaje(s) - Total: {volumen_total} m³ de {material}")
                    st.session_state.maq_mat_sel = ""
                    st.cache_data.clear()
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error: {e}")
            elif guardar:
                st.error("⚠️ Complete placa, material y volumen")

    else:
        col_btns = st.columns(4)
        for i, (label, eq) in enumerate(EQUIPOS_RAPIDOS):
            with col_btns[i]:
                if st.button(label, key=f"qeq_{eq}", use_container_width=True):
                    st.session_state.maq_eq_sel = eq
                    st.rerun()

        default_eq = st.session_state.get("maq_eq_sel", "Retroexcavadora")
        with st.form("form_equipo"):
            col1, col2 = st.columns(2)
            with col1:
                tipo_equipo = st.selectbox("Tipo de equipo:",
                    ["Retroexcavadora", "Mototrac", "Grúa", "Compactador", "Mixer", "Volqueta", "Otro"],
                    index=["Retroexcavadora", "Mototrac", "Grúa", "Compactador", "Mixer", "Volqueta", "Otro"].index(default_eq) if default_eq in ["Retroexcavadora", "Mototrac", "Grúa", "Compactador", "Mixer", "Volqueta", "Otro"] else 0,
                    key="eq_tipo_new")
                placa_eq = st.text_input("Placa/ID:", key="eq_placa_new").upper()
                operador_eq = st.text_input("Operador:", key="eq_oper_new")
            with col2:
                hora_inicio = st.time_input("Hora inicio:", key="eq_hora_ini_new")
                hora_fin = st.time_input("Hora fin:", key="eq_hora_fin_new")
                observaciones_eq = st.text_area("Observaciones:", key="eq_obs_new")

            if hora_inicio and hora_fin:
                dt_inicio = datetime.combine(date.today(), hora_inicio)
                dt_fin = datetime.combine(date.today(), hora_fin)
                delta = dt_fin - dt_inicio
                horas = delta.total_seconds() / 3600
                if horas < 0:
                    horas += 24
                st.info(f"⏱️ Horas calculadas: **{horas:.2f} horas**")
            else:
                horas = 0

            guardar = st.form_submit_button("💾 Registrar Equipo", type="primary", use_container_width=True)
            if guardar and placa_eq and horas > 0:
                data = {
                    "proyecto": PA, "fecha": date.today().isoformat(), "tipo_equipo": tipo_equipo,
                    "placa": placa_eq.strip(), "operador": operador_eq.strip(),
                    "hora_inicio": hora_inicio.strftime("%H:%M:%S"), "hora_fin": hora_fin.strftime("%H:%M:%S"),
                    "horas_trabajadas": round(horas, 2), "material_transportado": None, "volumen_m3": 0, "numero_viajes": 0,
                    "observaciones": observaciones_eq.strip(), "usuario": usuario
                }
                try:
                    insert_control_maquinas(supabase, data)
                    st.success(f"✅ Equipo registrado: {tipo_equipo} ({placa_eq}) - {horas:.2f} horas")
                    st.session_state.maq_eq_sel = "Retroexcavadora"
                    st.cache_data.clear()
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error: {e}")
            elif guardar:
                st.error("⚠️ Complete placa y verifique horas")

    st.markdown("---")

    # ═══ TABLA INTERACTIVA CON FILTROS ═══

    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        filtro_tipo = st.selectbox("Tipo:", ["Todos", "Volqueta", "Retroexcavadora", "Mototrac", "Grúa", "Compactador", "Mixer", "Otro"], key="hist_filtro_tipo")
    with col_f2:
        filtro_placa = st.text_input("Buscar placa:", key="hist_filtro_placa")
    with col_f3:
        filtro_fecha = st.date_input("Fecha:", value=date.today(), key="hist_filtro_fecha")

    query = supabase.table("control_maquinas").select("*").eq("proyecto", PA).eq("fecha", filtro_fecha.isoformat())
    response = query.execute()

    if not response.data:
        st.info("📭 No hay registros para esta fecha")
        return

    df = pd.DataFrame(response.data)
    if filtro_tipo != "Todos" and "tipo_equipo" in df.columns:
        df = df[df["tipo_equipo"] == filtro_tipo]
    if filtro_placa and "placa" in df.columns:
        df = df[df["placa"].str.contains(filtro_placa.upper(), na=False)]

    if df.empty:
        st.info("📭 No hay registros con los filtros seleccionados")
        return

    total_h = df["horas_trabajadas"].sum() if "horas_trabajadas" in df.columns else 0
    total_m3 = df["volumen_m3"].sum() if "volumen_m3" in df.columns else 0
    k1, k2, k3 = st.columns(3)
    k1.metric("Registros", len(df))
    k2.metric("Horas", f"{total_h:.1f}h")
    k3.metric("Volumen", f"{total_m3:.1f} m³")

    cols_maq = [c for c in ["id", "hora_inicio", "hora_fin", "tipo_equipo", "placa", "operador", "horas_trabajadas", "material_transportado", "volumen_m3", "numero_viajes", "observaciones"] if c in df.columns]
    config_maq = {
        "id": st.column_config.TextColumn("ID", disabled=True),
        "hora_inicio": st.column_config.TextColumn("H. Inicio", disabled=True, width="small"),
        "hora_fin": st.column_config.TextColumn("H. Fin", disabled=True, width="small"),
        "tipo_equipo": st.column_config.SelectboxColumn("Tipo", options=["Volqueta", "Retroexcavadora", "Mototrac", "Grúa", "Compactador", "Mixer", "Otro"]),
        "placa": st.column_config.TextColumn("Placa", width="small"),
        "operador": st.column_config.TextColumn("Operador", width="medium"),
        "horas_trabajadas": st.column_config.NumberColumn("Horas", step=0.5, format="%.1f"),
        "material_transportado": st.column_config.TextColumn("Material", width="medium"),
        "volumen_m3": st.column_config.NumberColumn("m³", step=0.5, format="%.1f"),
        "numero_viajes": st.column_config.NumberColumn("Viajes", step=1),
        "observaciones": st.column_config.TextColumn("Obs.", width="medium"),
    }
    config_f = {k: v for k, v in config_maq.items() if k in cols_maq}

    df_edit = st.data_editor(
        df.sort_values("hora_inicio")[cols_maq] if "hora_inicio" in df.columns else df[cols_maq],
        column_config=config_f, hide_index=True, use_container_width=True, key="editor_maq"
    )

    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("💾 Guardar Cambios", type="primary", use_container_width=True, key="btn_save_maq"):
            cambios = 0
            df_original = df.sort_values("hora_inicio")[cols_maq] if "hora_inicio" in df.columns else df[cols_maq]
            for idx, row in df_edit.iterrows():
                orig = df_original.loc[idx]
                if "id" in row and not row.equals(orig):
                    update_data = {}
                    for col in cols_maq:
                        if col not in ["id", "hora_inicio", "hora_fin"] and col in row.index and row[col] != orig.get(col):
                            update_data[col] = row[col]
                    if update_data:
                        try:
                            update_record(supabase, "control_maquinas", "id", row["id"], update_data)
                            cambios += 1
                        except Exception:
                            pass
            if cambios > 0:
                st.success(f"✅ {cambios} registro(s) actualizado(s)")
                st.cache_data.clear()
                st.rerun()
            else:
                st.info("ℹ️ No se detectaron cambios")
    with col_btn2:
        reg_del = st.text_input("ID a eliminar:", key="maq_del_id2", placeholder="Escriba el ID...")
        if st.button("🗑️ Eliminar", use_container_width=True, key="btn_del_maq2"):
            if reg_del.strip():
                try:
                    delete_record(supabase, "control_maquinas", "id", reg_del.strip())
                    st.success("✅ Registro eliminado")
                    st.cache_data.clear()
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error: {e}")

    render_seed_button(supabase, PA, "Máquinas", seed_maquinas_data, key_prefix="maq")