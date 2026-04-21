# modules/inventory.py
import streamlit as st
from supabase import Client
import pandas as pd
from datetime import datetime, date
from database.queries import insert_control_inventario, update_record, delete_record
from utils.seed_data import render_seed_button, seed_inventario

MATERIALES_RAPIDOS = [
    ("🧱 Cemento", "Cemento", "bultos"),
    ("🏔️ Arena", "Arena", "m3"),
    ("🪨 Grava", "Grava", "m3"),
    ("🔩 Varilla", "Varilla", "varillas"),
    ("🧱 Ladrillo", "Ladrillo", "und"),
    ("💧 Piedra", "Piedra", "m3"),
]

def render_almacenista(supabase: Client):
    PA = st.session_state.nombre_proyecto
    usuario = st.session_state.usuario_actual

    st.markdown(f'''
    <div style="background:#ff6f00;padding:18px 28px;border-radius:12px;margin-bottom:24px;display:flex;align-items:center;gap:16px">
        <span style="font-size:32px">📦</span>
        <div>
            <div style="color:#fff;font-size:20px;font-weight:700">Control de Inventario</div>
            <div style="color:#ffe0b2;font-size:13px">Almacén - {PA}</div>
        </div>
    </div>
    ''', unsafe_allow_html=True)

    col_tipo1, col_tipo2 = st.columns(2)
    with col_tipo1:
        btn_ent = st.button("📥 Entrada Rápida", type="primary", use_container_width=True, key="btn_inv_ent")
    with col_tipo2:
        btn_sal = st.button("📤 Salida Rápida", type="primary", use_container_width=True, key="btn_inv_sal")

    tipo_mov_default = "Entrada" if btn_ent else "Salida" if btn_sal else st.session_state.get("inv_tipo_mov", "Entrada")
    if btn_ent or btn_sal:
        st.session_state.inv_tipo_mov = tipo_mov_default

    tipo_mov = st.session_state.get("inv_tipo_mov", "Entrada")

    col_btns = st.columns(6)
    for i, (label, mat, und) in enumerate(MATERIALES_RAPIDOS):
        with col_btns[i % 6]:
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
            unidad = st.selectbox("Unidad:", ["bultos", "m3", "kg", "ton", "und", "varillas", "pies2", "galones"],
                index=["bultos", "m3", "kg", "ton", "und", "varillas", "pies2", "galones"].index(default_und) if default_und in ["bultos", "m3", "kg", "ton", "und", "varillas", "pies2", "galones"] else 4,
                key="inv_und_new")
        with col2:
            responsable = st.text_input("Responsable:", key="inv_resp_new")
            observaciones = st.text_area("Observaciones:", key="inv_obs_new")

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

    st.markdown("---")

    # ═══ TABLA INTERACTIVA CON FILTROS ═══

    response = supabase.table("control_inventario").select("*").eq("proyecto", PA).execute()
    if not response.data:
        st.info("📭 No hay movimientos registrados")
        return

    df = pd.DataFrame(response.data)

    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        filtro_tipo = st.selectbox("Tipo:", ["Todos", "Entrada", "Salida"], key="inv_ftipo")
    with col_f2:
        materiales_lista = ["Todos"] + sorted(df["material"].dropna().unique().tolist()) if "material" in df.columns else ["Todos"]
        filtro_material = st.selectbox("Material:", materiales_lista, key="inv_fmat")
    with col_f3:
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
    k1, k2, k3 = st.columns(3)
    k1.metric("Total", len(df_f))
    k2.metric("Entradas", ent)
    k3.metric("Salidas", sal)

    if df_f.empty:
        st.info("📭 No hay datos con los filtros seleccionados")
        return

    cols_inv = [c for c in ["id", "fecha", "tipo_movimiento", "material", "cantidad", "unidad", "responsable", "observaciones"] if c in df_f.columns]
    config = {
        "id": st.column_config.TextColumn("ID", disabled=True),
        "fecha": st.column_config.TextColumn("Fecha", disabled=True),
        "tipo_movimiento": st.column_config.TextColumn("Tipo", disabled=True),
        "material": st.column_config.TextColumn("Material", width="medium"),
        "cantidad": st.column_config.NumberColumn("Cantidad", step=0.1),
        "unidad": st.column_config.SelectboxColumn("Unidad", options=["bultos", "m3", "kg", "ton", "und", "varillas", "pies2", "galones"]),
        "responsable": st.column_config.TextColumn("Responsable", width="medium"),
        "observaciones": st.column_config.TextColumn("Obs.", width="large"),
    }
    config_f = {k: v for k, v in config.items() if k in cols_inv}

    df_edit = st.data_editor(
        df_f.sort_values(["fecha", "hora"] if "hora" in df_f.columns else ["fecha"], ascending=False)[cols_inv],
        column_config=config_f, hide_index=True, use_container_width=True, key="editor_inv"
    )

    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("💾 Guardar Cambios", type="primary", use_container_width=True, key="btn_save_inv"):
            cambios = 0
            df_original = df_f.sort_values(["fecha", "hora"] if "hora" in df_f.columns else ["fecha"], ascending=False)[cols_inv]
            for idx, row in df_edit.iterrows():
                orig = df_original.loc[idx]
                if "id" in row and not row.equals(orig):
                    update_data = {}
                    for col in cols_inv:
                        if col not in ["id", "fecha", "tipo_movimiento"] and col in row.index and row[col] != orig.get(col):
                            update_data[col] = row[col]
                    if update_data:
                        try:
                            update_record(supabase, "control_inventario", "id", row["id"], update_data)
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
        registro_eliminar = st.text_input("ID a eliminar:", key="inv_del_id2", placeholder="Escriba el ID...")
        if st.button("🗑️ Eliminar", use_container_width=True, key="btn_del_inv2"):
            if registro_eliminar.strip():
                try:
                    delete_record(supabase, "control_inventario", "id", registro_eliminar.strip())
                    st.success(f"✅ Registro eliminado")
                    st.cache_data.clear()
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error: {e}")

    render_seed_button(supabase, PA, "Inventario", seed_inventario, key_prefix="inv")