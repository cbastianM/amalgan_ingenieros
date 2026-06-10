# modules/materials.py
import streamlit as st
import pandas as pd
from datetime import date
from database.queries import insert_record, update_record, delete_record, get_materiales

CATEGORIAS = ["Materiales", "Equipos", "Transporte", "Mano de obra", "Servicios", "Ferretería", "Concreto", "Acero"]

ESTADOS_RAPIDOS = [
    ("📝 Solicitado", "Solicitado"),
    ("🔄 En Proceso", "En proceso"),
    ("✅ Entregado", "Entregado"),
    ("❌ Cancelado", "Cancelado"),
]

MATERIALES_APROBADOS = [
    {"material": "Cemento", "unidad": "bultos", "categoria": "Materiales"},
    {"material": "Arena", "unidad": "m3", "categoria": "Materiales"},
    {"material": "Grava", "unidad": "m3", "categoria": "Materiales"},
    {"material": "Varilla", "unidad": "varillas", "categoria": "Materiales"},
    {"material": "Ladrillo", "unidad": "und", "categoria": "Materiales"},
    {"material": "Piedra", "unidad": "m3", "categoria": "Materiales"},
]

CATALOGO = {m["material"]: m for m in MATERIALES_APROBADOS}

def _badge(estado):
    colors = {"Solicitado": "#1565c0", "En proceso": "#f57f17", "Entregado": "#2e7d32", "Cancelado": "#c62828"}
    color = colors.get(estado, "#555")
    return f'<span style="background:{color};color:#fff;padding:2px 10px;border-radius:10px;font-size:12px;font-weight:600">{estado}</span>'


def render_materiales(supabase):
    PA = st.session_state.nombre_proyecto
    usuario = st.session_state.usuario_actual

    st.markdown(f'''
    <div style="background:#4e342e;padding:12px 20px;border-radius:10px;margin-bottom:16px;display:flex;align-items:center;gap:12px">
        <span style="font-size:26px">🏗️</span>
        <div>
            <div style="color:#fff;font-size:18px;font-weight:700">Solicitudes de Materiales</div>
            <div style="color:#d7ccc8;font-size:12px">Requerimientos - {PA}</div>
        </div>
    </div>
    ''', unsafe_allow_html=True)

    with st.expander("➕ Nueva solicitud", expanded=True):
        col_r1 = st.columns(2)
        for i, (label, estado) in enumerate(ESTADOS_RAPIDOS[:2]):
            with col_r1[i]:
                if st.button(label, key=f"qest_mat_{estado}", use_container_width=True):
                    st.session_state.mat_estado_sel = estado
                    st.rerun()
        col_r2 = st.columns(2)
        for i, (label, estado) in enumerate(ESTADOS_RAPIDOS[2:]):
            with col_r2[i]:
                if st.button(label, key=f"qest_mat_{estado}", use_container_width=True):
                    st.session_state.mat_estado_sel = estado
                    st.rerun()

        default_estado = st.session_state.get("mat_estado_sel", "Solicitado")

        with st.expander("📋 Catálogo de materiales aprobados", expanded=False):
            df_cat = pd.DataFrame(MATERIALES_APROBADOS)
            st.dataframe(df_cat, hide_index=True, use_container_width=True,
                         column_config={
                             "material": st.column_config.TextColumn("Material", width="large"),
                             "unidad": st.column_config.TextColumn("Unidad", width="small"),
                             "categoria": st.column_config.TextColumn("Categoría", width="medium"),
                         })

        with st.form("form_mat_rapido"):
            st.markdown("**Nueva solicitud**")
            col1, col2 = st.columns(2)
            with col1:
                cat_sel = st.selectbox("Categoría:", ["Todas"] + CATEGORIAS, key="mat_cat_filter")
                if cat_sel == "Todas":
                    materiales_filtrados = [m["material"] for m in MATERIALES_APROBADOS]
                else:
                    materiales_filtrados = [m["material"] for m in MATERIALES_APROBADOS if m["categoria"] == cat_sel]
                cantidad = st.number_input("Cantidad:*", min_value=0.0, step=1.0, key="mat_cant_new", placeholder="Ej: 120")
                estado = st.selectbox("Estado:", ["Solicitado", "En proceso", "Entregado", "Cancelado"],
                    index=["Solicitado", "En proceso", "Entregado", "Cancelado"].index(default_estado) if default_estado in ["Solicitado", "En proceso", "Entregado", "Cancelado"] else 0,
                    key="mat_estado_new")
            with col2:
                mat_sel = st.selectbox("Material aprobado:*", materiales_filtrados, key="mat_material_sel")
                unidad_auto = CATALOGO[mat_sel]["unidad"] if mat_sel in CATALOGO else ""
                st.text_input("Unidad:", value=unidad_auto, disabled=True, key="mat_unidad_auto")
                destino = st.text_input("Destino / Actividad:", key="mat_destino", placeholder="Ej: Vigas Piso 5")
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

    with st.expander("📋 Solicitudes registradas"):
        dfm = get_materiales(supabase, PA)

        if dfm.empty:
            st.info("📭 No hay solicitudes de materiales")
            return

        col_f1, col_f2 = st.columns(2)
        with col_f1:
            estados_lista = ["Todos"] + sorted(dfm["estado"].dropna().unique().tolist()) if "estado" in dfm.columns else ["Todos"]
            filtro_estado = st.selectbox("Estado:", estados_lista, key="mat_fest")
            mat_vals = ["Todos"] + sorted(dfm["material"].dropna().unique().tolist()) if "material" in dfm.columns else ["Todos"]
            filtro_material = st.selectbox("Material:", mat_vals, key="mat_fmat")
        with col_f2:
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
            m1, m2 = st.columns(2)
            m1.metric("📦 Solicitados", sol)
            m2.metric("🔄 En Proceso", pro)
            m1, m2 = st.columns(2)
            m1.metric("✅ Entregados", ent)
            m2.metric("❌ Cancelados", canc)

        if df_mf.empty:
            st.info("📭 No hay datos con los filtros seleccionados")
            return

        rows = [df_mf.iloc[i:i+2] for i in range(0, len(df_mf), 2)]
        for row_pair in rows:
            left_col, right_col = st.columns(2)
            for col_idx, (idx, row) in enumerate(row_pair.iterrows()):
                current_col = left_col if col_idx == 0 else right_col
                with current_col:
                    material = row.get("material", "")
                    estado_val = row.get("estado", "")
                    cantidad_val = row.get("cantidad", "")
                    unidad_val = row.get("unidad", "")
                    row_id = str(row.get("id", ""))
                    fecha_val = str(row.get("fecha", ""))
                    req_val = str(row.get("requerimiento", ""))
                    usuario_val = str(row.get("usuario", ""))
                    destino_val = str(row.get("destino", ""))

                    label = f"{material} — {_badge(estado_val)} — {cantidad_val} {unidad_val}"
                    with st.expander(label, expanded=False):
                        st.markdown(f"**ID:** {row_id} &nbsp;|&nbsp; **Fecha:** {fecha_val} &nbsp;|&nbsp; **Usuario:** {usuario_val}")
                        if req_val:
                            st.markdown(f"**Requerimiento:** {req_val}")
                        if destino_val and destino_val != "None":
                            st.markdown(f"**Destino:** {destino_val}")

                        st.markdown("---")
                        ecol1, ecol2 = st.columns(2)
                        with ecol1:
                            new_estado = st.selectbox("Nuevo estado:", ["Solicitado", "En proceso", "Entregado", "Cancelado"],
                                index=["Solicitado", "En proceso", "Entregado", "Cancelado"].index(estado_val) if estado_val in ["Solicitado", "En proceso", "Entregado", "Cancelado"] else 0,
                                key=f"mat_estado_edit_{row_id}")
                        with ecol2:
                            new_req = st.text_input("Requerimiento:", value=req_val, key=f"mat_req_edit_{row_id}")

                        ecol3, ecol4 = st.columns(2)
                        with ecol3:
                            new_cantidad = st.number_input("Cantidad:", value=float(cantidad_val) if cantidad_val else 0.0, key=f"mat_cant_edit_{row_id}", min_value=0.0, step=1.0)
                        with ecol4:
                            new_destino = st.text_input("Destino:", value=destino_val if destino_val != "None" else "", key=f"mat_dest_edit_{row_id}")

                        bcol1, bcol2 = st.columns(2)
                        with bcol1:
                            if st.button(f"💾 Guardar", key=f"mat_save_{row_id}", use_container_width=True):
                                update_data = {"estado": new_estado, "requerimiento": new_req, "cantidad": new_cantidad, "destino": new_destino}
                                try:
                                    update_record(supabase, "materiales", "id", row_id, update_data)
                                    st.success("✅ Registro actualizado")
                                    st.cache_data.clear()
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"❌ Error: {e}")
                        with bcol2:
                            if st.button(f"🗑️ Eliminar", key=f"mat_del_{row_id}", use_container_width=True):
                                try:
                                    delete_record(supabase, "materiales", "id", row_id)
                                    st.success("✅ Registro eliminado")
                                    st.cache_data.clear()
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"❌ Error: {e}")

