# modules/inventory.py
import streamlit as st
import pandas as pd
from datetime import datetime, date
from database.queries import insert_control_inventario, update_record, delete_record

MATERIALES_RAPIDOS = [
    ("🧱 Cemento", "Cemento", "bultos"),
    ("🏔️ Arena", "Arena", "m3"),
    ("🪨 Grava", "Grava", "m3"),
    ("🔩 Varilla", "Varilla", "varillas"),
    ("🧱 Ladrillo", "Ladrillo", "und"),
    ("💧 Piedra", "Piedra", "m3"),
]

def render_almacenista(supabase):
    PA = st.session_state.nombre_proyecto
    usuario = st.session_state.usuario_actual
    es_dir = st.session_state.get("rol", "").lower() == "director"

    st.markdown(f'''
    <div style="background:#ff6f00;padding:14px 24px;border-radius:12px;margin-bottom:20px;display:flex;align-items:center;gap:14px">
        <span style="font-size:28px">📦</span>
        <div>
            <div style="color:#fff;font-size:18px;font-weight:700">Control de Inventario</div>
            <div style="color:#ffe0b2;font-size:12px">Almacén - {PA}</div>
        </div>
    </div>
    ''', unsafe_allow_html=True)

    with st.expander("📥 Registrar movimiento", expanded=True):
        col_tipo1, col_tipo2 = st.columns(2)
        with col_tipo1:
            btn_ent = st.button("📥 Entrada Rápida", type="primary", use_container_width=True, key="btn_inv_ent")
        with col_tipo2:
            btn_sal = st.button("📤 Salida Rápida", type="primary", use_container_width=True, key="btn_inv_sal")

        tipo_mov_default = "Entrada" if btn_ent else "Salida" if btn_sal else st.session_state.get("inv_tipo_mov", "Entrada")
        if btn_ent or btn_sal:
            st.session_state.inv_tipo_mov = tipo_mov_default

        tipo_mov = st.session_state.get("inv_tipo_mov", "Entrada")

        row1_mats = MATERIALES_RAPIDOS[:3]
        row2_mats = MATERIALES_RAPIDOS[3:]
        col_r1 = st.columns(2)
        for i, (label, mat, und) in enumerate(row1_mats):
            with col_r1[i]:
                if st.button(label, key=f"qmat_inv_{mat}", use_container_width=True):
                    st.session_state.inv_qmat = mat
                    st.session_state.inv_qund = und
                    st.rerun()
        col_r2 = st.columns(2)
        for i, (label, mat, und) in enumerate(row2_mats):
            with col_r2[i]:
                if st.button(label, key=f"qmat_inv_{mat}", use_container_width=True):
                    st.session_state.inv_qmat = mat
                    st.session_state.inv_qund = und
                    st.rerun()

        default_mat = st.session_state.get("inv_qmat", "")
        default_und = st.session_state.get("inv_qund", "und")

        with st.form("form_inv_rapido"):
            col1, col2 = st.columns(2)
            with col1:
                material = st.text_input("Material:", value=default_mat, placeholder="ej: Cemento, Arena...", key="inv_mat_new")
                cantidad = st.number_input("Cantidad:", min_value=0.0, step=1.0, key="inv_cant_new")
            with col2:
                unidad = st.selectbox("Unidad:", ["bultos", "m3", "kg", "ton", "und", "varillas", "pies2", "galones"],
                    index=["bultos", "m3", "kg", "ton", "und", "varillas", "pies2", "galones"].index(default_und) if default_und in ["bultos", "m3", "kg", "ton", "und", "varillas", "pies2", "galones"] else 4,
                    key="inv_und_new")
                responsable = st.text_input("Responsable:", key="inv_resp_new")
            observaciones = st.text_area("Observaciones:", key="inv_obs_new", height=68)

            guardar = st.form_submit_button(f"💾 Registrar {tipo_mov}", type="primary", use_container_width=True)
            if guardar and material and cantidad > 0:
                data = {
                    "proyecto": PA, "fecha": date.today().isoformat(), "hora": datetime.now().strftime("%H:%M:%S"),
                    "tipo_movimiento": tipo_mov, "material": material.strip(), "cantidad": cantidad, "unidad": unidad,
                    "responsable": responsable.strip(), "observaciones": observaciones.strip(), "usuario": usuario
                }
                try:
                    insert_control_inventario(supabase, data)
                    st.success(f"✅ {tipo_mov} registrada: {cantidad} {unidad} de {material}")
                    st.session_state.inv_qmat = ""
                    st.session_state.inv_qund = ""
                    st.cache_data.clear()
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error: {e}")
            elif guardar:
                st.error("⚠️ Complete material y cantidad")

    with st.expander("📂 Movimientos registrados"):
        response = supabase.table("control_inventario").select("*").eq("proyecto", PA).execute()
        if not response.data:
            st.info("📭 No hay movimientos registrados")
            return

        df = pd.DataFrame(response.data)

        col_f1, col_f2 = st.columns(2)
        with col_f1:
            filtro_tipo = st.selectbox("Tipo:", ["Todos", "Entrada", "Salida"], key="inv_ftipo")
            materiales_lista = ["Todos"] + sorted(df["material"].dropna().unique().tolist()) if "material" in df.columns else ["Todos"]
            filtro_material = st.selectbox("Material:", materiales_lista, key="inv_fmat")
        with col_f2:
            filtro_fecha = st.date_input("Fecha:", value=None, key="inv_ffecha")

        df_f = df.copy()
        if filtro_tipo != "Todos" and "tipo_movimiento" in df_f.columns:
            df_f = df_f[df_f["tipo_movimiento"] == filtro_tipo]
        if filtro_material != "Todos" and "material" in df_f.columns:
            df_f = df_f[df_f["material"] == filtro_material]
        if filtro_fecha and "fecha" in df_f.columns:
            df_f = df_f[df_f["fecha"] == filtro_fecha.isoformat()]

        ent = len(df_f[df_f["tipo_movimiento"] == "Entrada"]) if not df_f.empty and "tipo_movimiento" in df_f.columns else 0
        sal = len(df_f[df_f["tipo_movimiento"] == "Salida"]) if not df_f.empty and "tipo_movimiento" in df_f.columns else 0
        k1, k2 = st.columns(2)
        k1.metric("Total", len(df_f))
        k2.metric("Entradas", ent)
        k1, k2 = st.columns(2)
        k1.metric("Salidas", sal)

        if df_f.empty:
            st.info("📭 No hay datos con los filtros seleccionados")
            return

        df_f = df_f.sort_values(["fecha", "hora"] if "hora" in df_f.columns else ["fecha"], ascending=False)

        colores_tipo = {"Entrada": ("#2e7d32", "🟢"), "Salida": ("#c62828", "🔴")}

        rows = [df_f.iloc[i:i+2] for i in range(0, len(df_f), 2)]
        for row_pair in rows:
            left_col, right_col = st.columns(2)
            for col_idx, (idx, row) in enumerate(row_pair.iterrows()):
                current_col = left_col if col_idx == 0 else right_col
                with current_col:
                    tipo = row.get("tipo_movimiento", "")
                    color, badge = colores_tipo.get(tipo, ("#333", "⚪"))
                    fecha_str = row.get("fecha", "")
                    hora_str = row.get("hora", "")
                    mat = row.get("material", "")
                    cant = row.get("cantidad", 0)
                    und = row.get("unidad", "")
                    resp = row.get("responsable", "")
                    obs = row.get("observaciones", "")
                    rid = row.get("id", "")

                    preview = f"{badge} **{fecha_str}** · **{tipo}** · {mat} — {cant} {und}"

                    with st.expander(preview):
                        st.markdown(f"""
                        | Campo | Valor |
                        |---|---|
                        | Fecha | {fecha_str} |
                        | Hora | {hora_str} |
                        | Tipo | {tipo} |
                        | Material | {mat} |
                        | Cantidad | {cant} {und} |
                        | Responsable | {resp or '—'} |
                        | Observaciones | {obs or '—'} |
                        | Usuario | {row.get('usuario', '—')} |
                        | ID | `{rid}` |
                        """)

                        if es_dir:
                            edit_key = f"inv_edit_{rid}"
                            if st.button("✏️ Editar", key=f"inv_edtbtn_{rid}"):
                                st.session_state[edit_key] = True
                            if st.session_state.get(edit_key):
                                with st.form(f"inv_edit_form_{rid}"):
                                    e_mat = st.text_input("Material", value=mat, key=f"inv_ef_mat_{rid}")
                                    e_cant = st.number_input("Cantidad", value=float(cant), min_value=0.0, step=0.1, key=f"inv_ef_cant_{rid}")
                                    e_und = st.selectbox("Unidad", ["bultos", "m3", "kg", "ton", "und", "varillas", "pies2", "galones"],
                                        index=["bultos", "m3", "kg", "ton", "und", "varillas", "pies2", "galones"].index(und) if und in ["bultos", "m3", "kg", "ton", "und", "varillas", "pies2", "galones"] else 4,
                                        key=f"inv_ef_und_{rid}")
                                    e_resp = st.text_input("Responsable", value=resp, key=f"inv_ef_resp_{rid}")
                                    e_obs = st.text_area("Observaciones", value=obs, key=f"inv_ef_obs_{rid}", height=68)
                                    submitted = st.form_submit_button("💾 Guardar", type="primary")
                                    if submitted:
                                        update_data = {
                                            "material": e_mat.strip(), "cantidad": e_cant, "unidad": e_und,
                                            "responsable": e_resp.strip(), "observaciones": e_obs.strip()
                                        }
                                        try:
                                            update_record(supabase, "control_inventario", "id", rid, update_data)
                                            st.success("✅ Registro actualizado")
                                            st.session_state[edit_key] = False
                                            st.cache_data.clear()
                                            st.rerun()
                                        except Exception as e:
                                            st.error(f"❌ Error: {e}")

                            if st.button("🗑️ Eliminar", key=f"inv_delbtn_{rid}"):
                                try:
                                    delete_record(supabase, "control_inventario", "id", rid)
                                    st.success("✅ Registro eliminado")
                                    st.cache_data.clear()
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"❌ Error: {e}")

