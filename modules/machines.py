# modules/machines.py
import streamlit as st
import pandas as pd
from datetime import datetime, time, date
from database.queries import insert_control_maquinas, update_record, delete_record

EQUIPOS_RAPIDOS = [
    ("🚛 Volqueta", "Volqueta"),
    ("⛏️ Retroexcavadora", "Retroexcavadora"),
    ("🚜 Mototrac", "Mototrac"),
    ("🏗️ Grúa", "Grúa"),
]

MATERIALES_TRANSPORTE = [
    ("🏔️ Gravilla", "Gravilla"), ("🌍 Tierra", "Tierra"), ("🏜️ Arena", "Arena"), ("🧱 Escombros", "Escombros"),
]

def render_controlador(supabase):
    PA = st.session_state.nombre_proyecto
    usuario = st.session_state.usuario_actual
    es_dir = st.session_state.get("rol_actual") == "Director"
    es_residente = st.session_state.get("rol_actual") == "Residente"
    puede_editar = es_dir or es_residente

    st.markdown(f'''
    <div style="background:#1565c0;padding:14px 24px;border-radius:10px;margin-bottom:18px;display:flex;align-items:center;gap:14px">
        <span style="font-size:28px">🚜</span>
        <div>
            <div style="color:#fff;font-size:18px;font-weight:700">Control de Máquinas</div>
            <div style="color:#bbdefb;font-size:12px">Equipos y Volquetas - {PA}</div>
        </div>
    </div>
    ''', unsafe_allow_html=True)

    with st.expander("➕ Registrar equipo", expanded=True):
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
            col_r1 = st.columns(2)
            for i, (label, mat) in enumerate(MATERIALES_TRANSPORTE[:2]):
                with col_r1[i]:
                    if st.button(label, key=f"qmatm_{mat}", use_container_width=True):
                        st.session_state.maq_mat_sel = mat
                        st.rerun()
            col_r2 = st.columns(2)
            for i, (label, mat) in enumerate(MATERIALES_TRANSPORTE[2:]):
                with col_r2[i]:
                    if st.button(label, key=f"qmatm_{mat}", use_container_width=True):
                        st.session_state.maq_mat_sel = mat
                        st.rerun()

            default_mat = st.session_state.get("maq_mat_sel", "")
            with st.form("form_volqueta"):
                col1, col2 = st.columns(2)
                with col1:
                    placa = st.text_input("Placa:", placeholder="ej: ABC123", key="maq_placa_new").upper()
                    operador = st.text_input("Operador:", key="maq_oper_new")
                    volumen = st.number_input("Volumen por viaje (m³):", min_value=0.0, step=0.5, key="maq_vol_new")
                with col2:
                    material = st.text_input("Material:", value=default_mat, key="maq_mat_new")
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
            col_r1 = st.columns(2)
            quick_items = EQUIPOS_RAPIDOS[:3]
            for i in range(3):
                with col_r1[i]:
                    if i < len(quick_items):
                        label, eq = quick_items[i]
                        if st.button(label, key=f"qeq_{eq}", use_container_width=True):
                            st.session_state.maq_eq_sel = eq
                            st.rerun()
            col_r2 = st.columns(2)
            if st.button("🏗️ Grúa", key="qeq_Grua_extra", use_container_width=True):
                st.session_state.maq_eq_sel = "Grúa"
                st.rerun()

            default_eq = st.session_state.get("maq_eq_sel", "Retroexcavadora")
            with st.form("form_equipo"):
                col1, col2 = st.columns(2)
                with col1:
                    tipo_equipo = st.selectbox("Tipo de equipo:",
                        ["Retroexcavadora", "Mototrac", "Grúa", "Compactador", "Mixer", "Volqueta", "Otro"],
                        index=["Retroexcavadora", "Mototrac", "Grúa", "Compactador", "Mixer", "Volqueta", "Otro"].index(default_eq) if default_eq in ["Retroexcavadora", "Mototrac", "Grúa", "Compactador", "Mixer", "Volqueta", "Otro"] else 0,
                        key="eq_tipo_new")
                    operador_eq = st.text_input("Operador:", key="eq_oper_new")
                    hora_fin = st.time_input("Hora fin:", key="eq_hora_fin_new")
                with col2:
                    placa_eq = st.text_input("Placa/ID:", key="eq_placa_new").upper()
                    hora_inicio = st.time_input("Hora inicio:", key="eq_hora_ini_new")
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

    with st.expander("📋 Registros del día", expanded=False):
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            filtro_tipo = st.selectbox("Tipo:", ["Todos", "Volqueta", "Retroexcavadora", "Mototrac", "Grúa", "Compactador", "Mixer", "Otro"], key="hist_filtro_tipo")
            filtro_placa = st.text_input("Buscar placa:", key="hist_filtro_placa")
        with col_f2:
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
        k1, k2 = st.columns(2)
        k1.metric("Registros", len(df))
        k2.metric("Horas", f"{total_h:.1f}h")
        k1, k2 = st.columns(2)
        k1.metric("Volumen", f"{total_m3:.1f} m³")

        if "hora_inicio" in df.columns:
            df_sorted = df.sort_values("hora_inicio")
        else:
            df_sorted = df

        tipo_icon = {
            "Volqueta": "🚛", "Retroexcavadora": "⛏️", "Mototrac": "🚜",
            "Grúa": "🏗️", "Compactador": "🔨", "Mixer": "🔄", "Otro": "⚙️"
        }

        rows = [df_sorted.iloc[i:i+2] for i in range(0, len(df_sorted), 2)]
        for row_pair in rows:
            left_col, right_col = st.columns(2)
            for col_idx, (idx, row) in enumerate(row_pair.iterrows()):
                current_col = left_col if col_idx == 0 else right_col
                with current_col:
                    rec_id = str(row.get("id", ""))
                    tipo = row.get("tipo_equipo", "")
                    placa = row.get("placa", "")
                    operador = row.get("operador", "")
                    fecha_val = row.get("fecha", "")
                    icon = tipo_icon.get(tipo, "⚙️")

                    preview = f"{icon} **{tipo}** — `{placa}` — {operador}"

                    badge_color = "#1565c0" if tipo == "Volqueta" else "#2e7d32"
                    badge = f'<span style="background:{badge_color};color:#fff;padding:2px 8px;border-radius:12px;font-size:11px;margin-left:6px">{fecha_val}</span>'

                    header_display = f"{preview} {badge}"
                    st.markdown(header_display, unsafe_allow_html=True)

                    with st.expander(f"{icon} {tipo} — {placa}", key=f"card_{rec_id}_{idx}"):
                        c1, c2 = st.columns(2)
                        with c1:
                            st.markdown(f"**Placa:** {placa}")
                            st.markdown(f"**Operador:** {operador or '—'}")
                            st.markdown(f"**Hora inicio:** {row.get('hora_inicio', '—')}")
                            st.markdown(f"**Hora fin:** {row.get('hora_fin', '—')}")
                        with c2:
                            st.markdown(f"**Horas trabajadas:** {row.get('horas_trabajadas', 0)}")
                            mat = row.get('material_transportado', None)
                            st.markdown(f"**Material:** {mat if mat and str(mat) != 'None' else '—'}")
                            vol = row.get('volumen_m3', 0)
                            st.markdown(f"**Volumen:** {vol} m³" if vol and float(vol) > 0 else "**Volumen:** —")
                            viajes = row.get('numero_viajes', 0)
                            st.markdown(f"**Viajes:** {viajes}" if viajes and int(viajes) > 0 else "**Viajes:** —")

                        obs = row.get("observaciones", "")
                        if obs and str(obs).strip():
                            st.markdown(f"📝 _{obs}_")

                        if puede_editar:
                            st.markdown("---")
                            edit_key = f"edit_maq_{rec_id}"
                            if st.button("✏️ Editar", key=f"btn_edit_{rec_id}_{idx}", use_container_width=True):
                                st.session_state[f"editing_{edit_key}"] = True
                                st.rerun()

                            if st.session_state.get(f"editing_{edit_key}", False):
                                with st.form(f"form_edit_{rec_id}_{idx}"):
                                    e_tipo = st.selectbox("Tipo:", ["Volqueta", "Retroexcavadora", "Mototrac", "Grúa", "Compactador", "Mixer", "Otro"],
                                        index=["Volqueta", "Retroexcavadora", "Mototrac", "Grúa", "Compactador", "Mixer", "Otro"].index(tipo) if tipo in ["Volqueta", "Retroexcavadora", "Mototrac", "Grúa", "Compactador", "Mixer", "Otro"] else 0,
                                        key=f"ed_tipo_{rec_id}_{idx}")
                                    e_placa = st.text_input("Placa:", value=str(placa), key=f"ed_placa_{rec_id}_{idx}").upper()
                                    e_oper = st.text_input("Operador:", value=str(operador or ""), key=f"ed_oper_{rec_id}_{idx}")
                                    e_horas = st.number_input("Horas trabajadas:", min_value=0.0, step=0.5, value=float(row.get("horas_trabajadas", 0) or 0), key=f"ed_horas_{rec_id}_{idx}")
                                    e_mat = st.text_input("Material:", value=str(row.get("material_transportado", "") or ""), key=f"ed_mat_{rec_id}_{idx}")
                                    e_vol = st.number_input("Volumen (m³):", min_value=0.0, step=0.5, value=float(row.get("volumen_m3", 0) or 0), key=f"ed_vol_{rec_id}_{idx}")
                                    e_viajes = st.number_input("Viajes:", min_value=0, step=1, value=int(row.get("numero_viajes", 0) or 0), key=f"ed_viajes_{rec_id}_{idx}")
                                    e_obs = st.text_area("Observaciones:", value=str(row.get("observaciones", "") or ""), key=f"ed_obs_{rec_id}_{idx}")

                                    col_save, col_cancel = st.columns(2)
                                    with col_save:
                                        save_btn = st.form_submit_button("💾 Guardar", type="primary", use_container_width=True)
                                    with col_cancel:
                                        cancel_btn = st.form_submit_button("❌ Cancelar", use_container_width=True)

                                    if cancel_btn:
                                        st.session_state[f"editing_{edit_key}"] = False
                                        st.rerun()

                                    if save_btn:
                                        update_data = {
                                            "tipo_equipo": e_tipo,
                                            "placa": e_placa.strip(),
                                            "operador": e_oper.strip(),
                                            "horas_trabajadas": e_horas,
                                            "material_transportado": e_mat.strip() if e_mat.strip() else None,
                                            "volumen_m3": e_vol,
                                            "numero_viajes": e_viajes,
                                            "observaciones": e_obs.strip(),
                                        }
                                        try:
                                            update_record(supabase, "control_maquinas", "id", rec_id, update_data)
                                            st.success("✅ Registro actualizado")
                                            st.session_state[f"editing_{edit_key}"] = False
                                            st.cache_data.clear()
                                            st.rerun()
                                        except Exception as e:
                                            st.error(f"❌ Error: {e}")

                        if es_dir:
                            st.markdown("---")
                            col_del = st.columns(1)[0]
                            with col_del:
                                if st.button(f"🗑️ Eliminar registro", key=f"btn_del_card_{rec_id}_{idx}", use_container_width=True):
                                    try:
                                        delete_record(supabase, "control_maquinas", "id", rec_id)
                                        st.success("✅ Registro eliminado")
                                        st.cache_data.clear()
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"❌ Error: {e}")

