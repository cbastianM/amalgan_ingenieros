# modules/materials.py
import streamlit as st
from supabase import Client
import pandas as pd
from datetime import date
from database.queries import get_materiales, update_record, delete_record, insert_record
from database.demo_data import MATERIALES_APROBADOS
from utils.seed_data import render_seed_button, seed_materiales_data

CATALOGO = {m["material"]: m for m in MATERIALES_APROBADOS}
CATEGORIAS = sorted(set(m["categoria"] for m in MATERIALES_APROBADOS))

ESTADOS_RAPIDOS = [
    ("📋 Solicitado", "Solicitado"),
    ("🔄 En proceso", "En proceso"),
    ("✅ Entregado", "Entregado"),
    ("❌ Cancelado", "Cancelado"),
]

def render_materiales(supabase: Client):
    PA = st.session_state.nombre_proyecto
    usuario = st.session_state.usuario_actual

    st.markdown(f'''
    <div style="background:#4e342e;padding:18px 28px;border-radius:12px;margin-bottom:24px;display:flex;align-items:center;gap:16px">
        <span style="font-size:32px">🏗️</span>
        <div>
            <div style="color:#fff;font-size:20px;font-weight:700">Solicitudes de Materiales</div>
            <div style="color:#d7ccc8;font-size:13px">Requerimientos - {PA}</div>
        </div>
    </div>
    ''', unsafe_allow_html=True)

    col_btns = st.columns(4)
    for i, (label, estado) in enumerate(ESTADOS_RAPIDOS):
        with col_btns[i % 4]:
            if st.button(label, key=f"qest_mat_{estado}", use_container_width=True):
                st.session_state.mat_estado_sel = estado
                st.rerun()

    default_estado = st.session_state.get("mat_estado_sel", "Solicitado")

    st.markdown("##### 📦 Material Aprobado del Proyecto")
    with st.expander("📋 Ver catálogo de materiales aprobados", expanded=False):
        df_cat = pd.DataFrame(MATERIALES_APROBADOS)
        st.dataframe(df_cat, hide_index=True, use_container_width=True,
                     column_config={
                         "material": st.column_config.TextColumn("Material", width="large"),
                         "unidad": st.column_config.TextColumn("Unidad", width="small"),
                         "categoria": st.column_config.TextColumn("Categoría", width="medium"),
                     })

    with st.form("form_mat_rapido"):
        col_f, col_m = st.columns([1, 2])
        with col_f:
            st.markdown("**Filtrar por categoría:**")
            cat_sel = st.selectbox("Categoría:", ["Todas"] + CATEGORIAS, key="mat_cat_filter")
            if cat_sel == "Todas":
                materiales_filtrados = [m["material"] for m in MATERIALES_APROBADOS]
            else:
                materiales_filtrados = [m["material"] for m in MATERIALES_APROBADOS if m["categoria"] == cat_sel]
            mat_sel = st.selectbox("Material aprobado:*", materiales_filtrados, key="mat_material_sel")
            unidad_auto = CATALOGO[mat_sel]["unidad"] if mat_sel in CATALOGO else ""
            st.text_input("Unidad:", value=unidad_auto, disabled=True, key="mat_unidad_auto")
            cantidad = st.number_input("Cantidad:*", min_value=0.0, step=1.0, key="mat_cant_new", placeholder="Ej: 120")
            destino = st.text_input("Destino / Actividad:", key="mat_destino", placeholder="Ej: Vigas Piso 5")
            estado = st.selectbox("Estado:", ["Solicitado", "En proceso", "Entregado", "Cancelado"],
                index=["Solicitado", "En proceso", "Entregado", "Cancelado"].index(default_estado) if default_estado in ["Solicitado", "En proceso", "Entregado", "Cancelado"] else 0,
                key="mat_estado_new")
        with col_m:
            obs = st.text_area("Observaciones:", key="mat_obs_new", placeholder="Ej: Pedido urgente, solicitud de cotización, etc.")
            st.info(f"👤 Registrado por: **{usuario}**")
            if mat_sel:
                st.markdown(f"**Vista previa:** {int(cantidad) if cantidad == int(cantidad) else cantidad} {unidad_auto} de **{mat_sel}**" +
                            (f" para {destino}" if destino else ""))

        fecha_sol = st.date_input("Fecha:", value=date.today(), key="mat_fecha_new", label_visibility="collapsed")

        guardar = st.form_submit_button("💾 Crear Solicitud", type="primary", use_container_width=True)
        if guardar:
            if not mat_sel or cantidad <= 0:
                st.error("⚠️ Seleccione un material e ingrese una cantidad mayor a 0")
            else:
                partes = [f"{int(cantidad) if cantidad == int(cantidad) else cantidad} {unidad_auto} de {mat_sel}"]
                if destino.strip():
                    partes.append(f"para {destino.strip()}")
                if obs.strip():
                    partes.append(f"— {obs.strip()}")
                requerimiento = " ".join(partes)
                data = {
                    "proyecto": PA,
                    "fecha": fecha_sol.isoformat(),
                    "requerimiento": requerimiento,
                    "material": mat_sel,
                    "cantidad": cantidad,
                    "unidad": unidad_auto,
                    "estado": estado,
                    "usuario": usuario,
                }
                try:
                    insert_record(supabase, "materiales", data)
                    st.success(f"✅ Solicitud creada: {requerimiento[:80]}")
                    st.session_state.mat_estado_sel = "Solicitado"
                    st.cache_data.clear()
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error: {e}")

    st.markdown("---")

    # ═══ TABLA INTERACTIVA CON FILTROS ═══
    dfm = get_materiales(supabase, PA)

    if dfm.empty:
        st.info("📭 No hay solicitudes de materiales")
        render_seed_button(supabase, PA, "Materiales", seed_materiales_data, key_prefix="mat")
        return

    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        estados_lista = ["Todos"] + sorted(dfm["estado"].dropna().unique().tolist()) if "estado" in dfm.columns else ["Todos"]
        filtro_estado = st.selectbox("Estado:", estados_lista, key="mat_fest")
    with col_f2:
        mat_vals = ["Todos"] + sorted(dfm["material"].dropna().unique().tolist()) if "material" in dfm.columns else ["Todos"]
        filtro_material = st.selectbox("Material:", mat_vals, key="mat_fmat")
    with col_f3:
        filtro_buscar = st.text_input("Buscar:", key="mat_fbuscar")

    df_mf = dfm.copy()
    if filtro_estado != "Todos" and "estado" in df_mf.columns:
        df_mf = df_mf[df_mf["estado"] == filtro_estado]
    if filtro_material != "Todos" and "material" in df_mf.columns:
        df_mf = df_mf[df_mf["material"] == filtro_material]
    if filtro_buscar and "requerimiento" in df_mf.columns:
        df_mf = df_mf[df_mf["requerimiento"].str.contains(filtro_buscar, case=False, na=False)]

    if not df_mf.empty and "estado" in df_mf.columns:
        sol = int((df_mf["estado"] == "Solicitado").sum())
        proc = int((df_mf["estado"] == "En proceso").sum())
        ent = int((df_mf["estado"] == "Entregado").sum())
        canc = int((df_mf["estado"] == "Cancelado").sum())
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("📋 Solicitados", sol)
        m2.metric("🔄 En Proceso", proc)
        m3.metric("✅ Entregados", ent)
        m4.metric("❌ Cancelados", canc)

    if df_mf.empty:
        st.info("📭 No hay datos con los filtros seleccionados")
        render_seed_button(supabase, PA, "Materiales", seed_materiales_data, key_prefix="mat")
        return

    cols_mat = [c for c in ["id", "fecha", "material", "cantidad", "unidad", "requerimiento", "estado", "usuario"] if c in df_mf.columns]
    config = {
        "id": st.column_config.TextColumn("ID", disabled=True),
        "fecha": st.column_config.TextColumn("Fecha", disabled=True),
        "material": st.column_config.TextColumn("Material", disabled=True, width="large"),
        "cantidad": st.column_config.NumberColumn("Cantidad", disabled=True, width="small"),
        "unidad": st.column_config.TextColumn("Unidad", disabled=True, width="small"),
        "requerimiento": st.column_config.TextColumn("Requerimiento", width="large"),
        "estado": st.column_config.SelectboxColumn("Estado", options=["Solicitado", "En proceso", "Entregado", "Cancelado"]),
        "usuario": st.column_config.TextColumn("Usuario", disabled=True, width="medium"),
    }
    config_f = {k: v for k, v in config.items() if k in cols_mat}

    df_edit = st.data_editor(df_mf[cols_mat], column_config=config_f, hide_index=True, use_container_width=True, key="editor_mat")

    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("💾 Guardar Cambios", type="primary", use_container_width=True, key="btn_save_mat"):
            cambios = 0
            df_original = df_mf[cols_mat]
            for idx, row in df_edit.iterrows():
                orig = df_original.loc[idx]
                if "id" in row and not row.equals(orig):
                    update_data = {}
                    for col in cols_mat:
                        if col not in ["id", "fecha"] and col in row.index and row[col] != orig.get(col):
                            update_data[col] = row[col]
                    if update_data:
                        try:
                            update_record(supabase, "materiales", "id", row["id"], update_data)
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
        reg_del = st.text_input("ID a eliminar:", key="mat_del_id2", placeholder="Escriba el ID...")
        if st.button("🗑️ Eliminar", use_container_width=True, key="btn_del_mat2"):
            if reg_del.strip():
                try:
                    delete_record(supabase, "materiales", "id", reg_del.strip())
                    st.success("✅ Registro eliminado")
                    st.cache_data.clear()
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error: {e}")

    render_seed_button(supabase, PA, "Materiales", seed_materiales_data, key_prefix="mat")