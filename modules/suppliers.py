import streamlit as st
import pandas as pd
from database.queries import insertproveedor, update_record, delete_record

CATEGORIAS_RAPIDAS = [
    ("🧱 Materiales", "Materiales"),
    ("🔧 Equipos", "Equipos"),
    ("🚛 Transporte", "Transporte"),
    ("👷 Mano de obra", "Mano de obra"),
    ("⚙️ Servicios", "Servicios"),
    ("🔩 Ferretería", "Ferretería"),
]

CATEGORIAS = ["Materiales", "Equipos", "Transporte", "Mano de obra", "Servicios", "Ferretería", "Concreto", "Acero", "Otro"]

BADGE_COLORS = {
    "Materiales": "#6a1b9a",
    "Equipos": "#1565c0",
    "Transporte": "#e65100",
    "Mano de obra": "#2e7d32",
    "Servicios": "#00838f",
    "Ferretería": "#4e342e",
    "Concreto": "#37474f",
    "Acero": "#546e7a",
    "Otro": "#757575",
}

def render_proveedores(supabase):
    st.markdown('''
    <div style="background:#6a1b9a;padding:18px 28px;border-radius:12px;margin-bottom:24px;display:flex;align-items:center;gap:16px">
        <span style="font-size:32px">🏢</span>
        <div>
            <div style="color:#fff;font-size:20px;font-weight:700">Proveedores</div>
            <div style="color:#ce93d8;font-size:13px">Directorio del proyecto</div>
        </div>
    </div>
    ''', unsafe_allow_html=True)

    row1_cats = CATEGORIAS_RAPIDAS[:3]
    row2_cats = CATEGORIAS_RAPIDAS[3:]
    col_r1 = st.columns(2)
    for i, (label, cat) in enumerate(row1_cats):
        with col_r1[i]:
            if st.button(label, key=f"qcat_prov_{cat}", use_container_width=True):
                st.session_state.prov_cat_sel = cat
                st.rerun()
    col_r2 = st.columns(2)
    for i, (label, cat) in enumerate(row2_cats):
        with col_r2[i]:
            if st.button(label, key=f"qcat_prov_{cat}", use_container_width=True):
                st.session_state.prov_cat_sel = cat
                st.rerun()

    with st.expander("➕ Nuevo proveedor", expanded=True):
        default_cat = st.session_state.get("prov_cat_sel", "Materiales")
        with st.form("form_prov_rapido"):
            col1, col2 = st.columns(2)
            with col1:
                nit = st.text_input("NIT *", key="prov_nit_new")
                contacto = st.text_input("Persona de Contacto", key="prov_contacto_new")
                categoria = st.selectbox(
                    "Categoría", CATEGORIAS,
                    index=CATEGORIAS.index(default_cat) if default_cat in CATEGORIAS else 0,
                    key="prov_categoria_new"
                )
            with col2:
                nombre = st.text_input("Nombre/Razón Social *", key="prov_nombre_new")
                telefono = st.text_input("Teléfono", key="prov_telefono_new")
                direccion = st.text_input("Dirección", key="prov_direccion_new")
            notas = st.text_area("Notas", key="prov_notas_new")

            guardar = st.form_submit_button("💾 Guardar Proveedor", type="primary", use_container_width=True)
        if guardar and nit.strip() and nombre.strip():
            data = {"nit": nit.strip(), "nombre": nombre.strip(), "contacto": contacto.strip(),
                    "telefono": telefono.strip(), "categoria": categoria, "direccion": direccion.strip(), "notas": notas.strip()}
            try:
                result = insertproveedor(supabase, data)
                if result:
                    st.success(f"✅ Proveedor '{nombre}' guardado correctamente")
                    st.session_state.prov_cat_sel = "Materiales"
                    st.cache_data.clear()
                    st.rerun()
                else:
                    st.error("❌ Error al guardar")
            except Exception as e:
                st.error(f"❌ Error: {e}")
        elif guardar:
            st.error("⚠️ NIT y Nombre son obligatorios")

    with st.expander("📋 Proveedores registrados"):
        response = supabase.table("proveedores").select("*").execute()
        if not response.data:
            st.info("📭 No hay proveedores registrados")
            return

        df = pd.DataFrame(response.data)

        col_f1, col_f2 = st.columns(2)
        with col_f1:
            categorias = ["Todas"] + sorted(df["categoria"].dropna().unique().tolist()) if "categoria" in df.columns else ["Todas"]
            cat_sel = st.selectbox("Categoría:", categorias, key="prov_fcat")
        with col_f2:
            buscar = st.text_input("Buscar por nombre:", key="prov_fbuscar")

        df_f = df.copy()
        if cat_sel != "Todas" and "categoria" in df_f.columns:
            df_f = df_f[df_f["categoria"] == cat_sel]
        if buscar and "nombre" in df_f.columns:
            df_f = df_f[df_f["nombre"].str.contains(buscar, case=False, na=False)]

        k1, k2 = st.columns(2)
        k1.metric("Total Proveedores", len(df_f))
        k2.metric("Categorías", df_f["categoria"].nunique() if "categoria" in df_f.columns and not df_f.empty else 0)

        if df_f.empty:
            st.info("📭 No hay datos con los filtros seleccionados")
            return

        rows = [df_f.iloc[i:i+2] for i in range(0, len(df_f), 2)]
        for row_pair in rows:
            left_col, right_col = st.columns(2)
            for col_idx, (idx, row) in enumerate(row_pair.iterrows()):
                current_col = left_col if col_idx == 0 else right_col
                with current_col:
                    row_id = str(row.get("id", ""))
                    row_nombre = str(row.get("nombre", ""))
                    row_categoria = str(row.get("categoria", ""))
                    badge_color = BADGE_COLORS.get(row_categoria, "#757575")

                    with st.expander(label=f"{row_nombre}"):
                        st.markdown(
                            f'<span style="background:{badge_color};color:#fff;padding:3px 10px;border-radius:12px;font-size:12px;font-weight:600">{row_categoria}</span>',
                            unsafe_allow_html=True
                        )
                        st.markdown("")

                        with st.form(f"edit_prov_{row_id}"):
                            e_nit = st.text_input("NIT", value=str(row.get("nit", "")), key=f"prov_e_nit_{row_id}")
                            e_nombre = st.text_input("Nombre/Razón Social", value=str(row.get("nombre", "")), key=f"prov_e_nombre_{row_id}")
                            e_contacto = st.text_input("Persona de Contacto", value=str(row.get("contacto", "")), key=f"prov_e_contacto_{row_id}")
                            e_telefono = st.text_input("Teléfono", value=str(row.get("telefono", "")), key=f"prov_e_telefono_{row_id}")
                            e_categoria = st.selectbox(
                                "Categoría", CATEGORIAS,
                                index=CATEGORIAS.index(row_categoria) if row_categoria in CATEGORIAS else 0,
                                key=f"prov_e_categoria_{row_id}"
                            )
                            e_direccion = st.text_input("Dirección", value=str(row.get("direccion", "")), key=f"prov_e_direccion_{row_id}")
                            e_notas = st.text_area("Notas", value=str(row.get("notas", "")), key=f"prov_e_notas_{row_id}")

                            col_save, col_del = st.columns(2)
                            with col_save:
                                save_clicked = st.form_submit_button("💾 Guardar", type="primary", use_container_width=True)
                            with col_del:
                                del_clicked = st.form_submit_button("🗑️ Eliminar", type="secondary", use_container_width=True)

                            if save_clicked:
                                update_data = {}
                                original = row
                                fields = {
                                    "nit": e_nit, "nombre": e_nombre, "contacto": e_contacto,
                                    "telefono": e_telefono, "categoria": e_categoria,
                                    "direccion": e_direccion, "notas": e_notas
                                }
                                for col, val in fields.items():
                                    old_val = str(original.get(col, "")) if original.get(col) is not None else ""
                                    new_val = val.strip()
                                    if new_val != old_val:
                                        update_data[col] = new_val
                                if update_data:
                                    try:
                                        update_record(supabase, "proveedores", "id", row_id, update_data)
                                        st.success("✅ Proveedor actualizado")
                                        st.cache_data.clear()
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"❌ Error: {e}")
                                else:
                                    st.info("ℹ️ No se detectaron cambios")

                            if del_clicked:
                                try:
                                    delete_record(supabase, "proveedores", "id", row_id)
                                    st.success("✅ Proveedor eliminado")
                                    st.cache_data.clear()
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"❌ Error: {e}")

