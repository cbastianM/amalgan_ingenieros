import streamlit as st
from supabase import Client
import pandas as pd
from database.queries import insertproveedor, update_record, delete_record
from utils.seed_data import render_seed_button, seed_proveedores_data

CATEGORIAS_RAPIDAS = [
    ("🧱 Materiales", "Materiales"),
    ("🔧 Equipos", "Equipos"),
    ("🚛 Transporte", "Transporte"),
    ("👷 Mano de obra", "Mano de obra"),
    ("⚙️ Servicios", "Servicios"),
    ("🔩 Ferretería", "Ferretería"),
]

def render_proveedores(supabase: Client):
    st.markdown('''
    <div style="background:#6a1b9a;padding:18px 28px;border-radius:12px;margin-bottom:24px;display:flex;align-items:center;gap:16px">
        <span style="font-size:32px">🏢</span>
        <div>
            <div style="color:#fff;font-size:20px;font-weight:700">Proveedores</div>
            <div style="color:#ce93d8;font-size:13px">Directorio del proyecto</div>
        </div>
    </div>
    ''', unsafe_allow_html=True)

    col_btns = st.columns(6)
    for i, (label, cat) in enumerate(CATEGORIAS_RAPIDAS):
        with col_btns[i % 6]:
            if st.button(label, key=f"qcat_prov_{cat}", use_container_width=True):
                st.session_state.prov_cat_sel = cat
                st.rerun()

    default_cat = st.session_state.get("prov_cat_sel", "Materiales")

    with st.form("form_prov_rapido"):
        col1, col2 = st.columns(2)
        with col1:
            nit = st.text_input("NIT:", key="prov_nit_new")
            nombre = st.text_input("Nombre/Razón Social:", key="prov_nombre_new")
            contacto = st.text_input("Persona de Contacto:", key="prov_contacto_new")
        with col2:
            telefono = st.text_input("Teléfono:", key="prov_telefono_new")
            categoria = st.selectbox(
                "Categoría:", ["Materiales", "Equipos", "Transporte", "Mano de obra", "Servicios", "Ferretería", "Concreto", "Acero", "Otro"],
                index=["Materiales", "Equipos", "Transporte", "Mano de obra", "Servicios", "Ferretería", "Concreto", "Acero", "Otro"].index(default_cat) if default_cat in ["Materiales", "Equipos", "Transporte", "Mano de obra", "Servicios", "Ferretería", "Concreto", "Acero", "Otro"] else 0,
                key="prov_categoria_new"
            )
            direccion = st.text_input("Dirección:", key="prov_direccion_new")

        notas = st.text_area("Notas:", key="prov_notas_new")

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

    st.markdown("---")

    # ═══ TABLA INTERACTIVA CON FILTROS ═══
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

    cols_prov = [c for c in ["id", "nit", "nombre", "contacto", "telefono", "categoria", "direccion", "notas"] if c in df_f.columns]
    config = {
        "id": st.column_config.TextColumn("ID", disabled=True),
        "nit": st.column_config.TextColumn("NIT", width="small"),
        "nombre": st.column_config.TextColumn("Nombre", width="medium"),
        "contacto": st.column_config.TextColumn("Contacto", width="medium"),
        "telefono": st.column_config.TextColumn("Teléfono", width="small"),
        "categoria": st.column_config.SelectboxColumn("Categoría", options=["Materiales", "Equipos", "Transporte", "Mano de obra", "Servicios", "Ferretería", "Concreto", "Acero", "Otro"]),
        "direccion": st.column_config.TextColumn("Dirección", width="medium"),
        "notas": st.column_config.TextColumn("Notas", width="large"),
    }
    config_f = {k: v for k, v in config.items() if k in cols_prov}

    df_edit = st.data_editor(df_f[cols_prov], column_config=config_f, hide_index=True, use_container_width=True, key="editor_prov")

    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("💾 Guardar Cambios", type="primary", use_container_width=True, key="btn_save_prov"):
            cambios = 0
            df_original = df_f[cols_prov]
            for idx, row in df_edit.iterrows():
                orig = df_original.loc[idx]
                if "id" in row and not row.equals(orig):
                    update_data = {}
                    for col in cols_prov:
                        if col != "id" and col in row.index and row[col] != orig.get(col):
                            update_data[col] = row[col]
                    if update_data:
                        try:
                            update_record(supabase, "proveedores", "id", row["id"], update_data)
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
        reg_del = st.text_input("ID a eliminar:", key="prov_del_id2", placeholder="Escriba el ID...")
        if st.button("🗑️ Eliminar", use_container_width=True, key="btn_del_prov2"):
            if reg_del.strip():
                try:
                    delete_record(supabase, "proveedores", "id", reg_del.strip())
                    st.success("✅ Proveedor eliminado")
                    st.cache_data.clear()
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error: {e}")

    render_seed_button(supabase, "", "Proveedores", seed_proveedores_data, key_prefix="prov")