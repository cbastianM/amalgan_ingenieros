# modules/payroll.py
import streamlit as st
from supabase import Client
import pandas as pd
from datetime import date
from database.queries import get_nomina, update_record, delete_record, insert_record
from utils.formatting import fmt_cop
from utils.seed_data import render_seed_button, seed_nomina_data

TIPOS_RAPIDOS = [
    ("💵 Quincenal", "Quincenal"),
    ("💰 Mensual", "Mensual"),
    ("📊 Jornal", "Jornal diario"),
    ("🎁 Bono", "Bonificacion"),
    ("💵 Préstamo", "Prestamo"),
    ("📉 Deducción", "Deduccion"),
]

def render_nomina(supabase: Client):
    PA = st.session_state.nombre_proyecto
    usuario = st.session_state.usuario_actual

    st.markdown(f'''
    <div style="background:#880e4f;padding:18px 28px;border-radius:12px;margin-bottom:24px;display:flex;align-items:center;gap:16px">
        <span style="font-size:32px">💵</span>
        <div>
            <div style="color:#fff;font-size:20px;font-weight:700">Control de Nómina</div>
            <div style="color:#f8bbd0;font-size:13px">Pagos y deducciones - {PA}</div>
        </div>
    </div>
    ''', unsafe_allow_html=True)

    col_btns = st.columns(6)
    for i, (label, tipo) in enumerate(TIPOS_RAPIDOS):
        with col_btns[i % 6]:
            if st.button(label, key=f"qtipo_nom_{tipo}", use_container_width=True):
                st.session_state.nom_tipo_sel = tipo
                st.rerun()

    default_tipo = st.session_state.get("nom_tipo_sel", "Quincenal")

    with st.form("form_nom_rapido"):
        col1, col2 = st.columns(2)
        with col1:
            trabajador = st.text_input("Trabajador:", key="nom_trab_new", placeholder="Nombre completo")
            tipo = st.selectbox("Tipo:", ["Mensual", "Quincenal", "Jornal diario", "Bonificacion", "Prestamo", "Anticipo", "Deduccion"],
                index=["Mensual", "Quincenal", "Jornal diario", "Bonificacion", "Prestamo", "Anticipo", "Deduccion"].index(default_tipo) if default_tipo in ["Mensual", "Quincenal", "Jornal diario", "Bonificacion", "Prestamo", "Anticipo", "Deduccion"] else 0,
                key="nom_tipo_new")
        with col2:
            valor = st.number_input("Valor ($):", min_value=0, step=50000, key="nom_valor_new", format="%d")
            notas = st.text_input("Notas:", key="nom_notas_new")

        guardar = st.form_submit_button("💾 Registrar Movimiento", type="primary", use_container_width=True)
        if guardar and trabajador.strip() and valor > 0:
            data = {
                "proyecto": PA, "fecha": date.today().isoformat(), "trabajador": trabajador.strip(),
                "tipo": tipo, "valor": valor, "notas": notas.strip()
            }
            try:
                insert_record(supabase, "nomina", data)
                st.success(f"✅ Movimiento registrado: {fmt_cop(valor)} - {tipo}")
                st.cache_data.clear()
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error: {e}")
        elif guardar:
            st.error("⚠️ Complete trabajador y valor")

    st.markdown("---")

    # ═══ TABLA INTERACTIVA CON FILTROS ═══
    dfn = get_nomina(supabase, PA)

    if dfn.empty:
        st.info("📭 No hay movimientos de nómina")
        render_seed_button(supabase, PA, "Nómina", seed_nomina_data, key_prefix="nom")
        return

    col_f1, col_f2 = st.columns(2)
    with col_f1:
        tipos_lista = ["Todos"] + sorted(dfn["tipo"].dropna().unique().tolist()) if "tipo" in dfn.columns else ["Todos"]
        filtro_tipo = st.selectbox("Tipo:", tipos_lista, key="nom_ftipo")
    with col_f2:
        filtro_buscar = st.text_input("Buscar trabajador:", key="nom_fbuscar")

    df_nf = dfn.copy()
    if filtro_tipo != "Todos" and "tipo" in df_nf.columns:
        df_nf = df_nf[df_nf["tipo"] == filtro_tipo]
    if filtro_buscar and "trabajador" in df_nf.columns:
        df_nf = df_nf[df_nf["trabajador"].str.contains(filtro_buscar, case=False, na=False)]

    if not df_nf.empty and "tipo" in df_nf.columns and "valor" in df_nf.columns:
        ing = df_nf[df_nf["tipo"].isin(["Mensual", "Quincenal", "Jornal diario", "Bonificacion"])]["valor"].sum()
        pre = df_nf[df_nf["tipo"].isin(["Prestamo", "Anticipo"])]["valor"].sum()
        ded = df_nf[df_nf["tipo"] == "Deduccion"]["valor"].sum() if "Deduccion" in df_nf["tipo"].values else 0
        n1, n2, n3, n4 = st.columns(4)
        n1.metric("Total Pagos", fmt_cop(ing))
        n2.metric("Préstamos", fmt_cop(pre))
        n3.metric("Deducciones", fmt_cop(ded))
        n4.metric("Neto", fmt_cop(ing - pre - ded))

        st.markdown("**Distribución de Nómina**")
        nom_chart = df_nf.groupby("tipo")["valor"].sum().sort_values(ascending=True)
        st.bar_chart(nom_chart, height=300)

    if df_nf.empty:
        st.info("📭 No hay datos con los filtros seleccionados")
        render_seed_button(supabase, PA, "Nómina", seed_nomina_data, key_prefix="nom")
        return

    cols_nom = [c for c in ["id", "fecha", "trabajador", "tipo", "valor", "notas"] if c in df_nf.columns]
    config = {
        "id": st.column_config.TextColumn("ID", disabled=True),
        "fecha": st.column_config.TextColumn("Fecha", disabled=True),
        "trabajador": st.column_config.TextColumn("Trabajador", width="medium"),
        "tipo": st.column_config.SelectboxColumn("Tipo", options=["Mensual", "Quincenal", "Jornal diario", "Bonificacion", "Prestamo", "Anticipo", "Deduccion"]),
        "valor": st.column_config.NumberColumn("Valor", format="$ %,.0f", step=1000),
        "notas": st.column_config.TextColumn("Notas", width="medium"),
    }
    config_f = {k: v for k, v in config.items() if k in cols_nom}

    df_edit = st.data_editor(
        df_nf[cols_nom].sort_values("fecha", ascending=False) if "fecha" in df_nf.columns else df_nf[cols_nom],
        column_config=config_f, hide_index=True, use_container_width=True, key="editor_nom"
    )

    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("💾 Guardar Cambios", type="primary", use_container_width=True, key="btn_save_nom"):
            cambios = 0
            df_original = df_nf[cols_nom].sort_values("fecha", ascending=False) if "fecha" in df_nf.columns else df_nf[cols_nom]
            for idx, row in df_edit.iterrows():
                orig = df_original.loc[idx]
                if "id" in row and not row.equals(orig):
                    update_data = {}
                    for col in cols_nom:
                        if col not in ["id"] and col in row.index and row[col] != orig.get(col):
                            update_data[col] = row[col]
                    if update_data:
                        try:
                            update_record(supabase, "nomina", "id", row["id"], update_data)
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
        reg_del = st.text_input("ID a eliminar:", key="nom_del_id2", placeholder="Escriba el ID...")
        if st.button("🗑️ Eliminar", use_container_width=True, key="btn_del_nom2"):
            if reg_del.strip():
                try:
                    delete_record(supabase, "nomina", "id", reg_del.strip())
                    st.success("✅ Registro eliminado")
                    st.cache_data.clear()
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error: {e}")

    render_seed_button(supabase, PA, "Nómina", seed_nomina_data, key_prefix="nom")