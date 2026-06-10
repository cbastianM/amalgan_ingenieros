# modules/payroll.py
import streamlit as st
import pandas as pd
from datetime import date
from database.queries import get_nomina, update_record, delete_record, insert_record
from utils.formatting import fmt_cop

TIPOS_RAPIDOS = [
    ("💵 Quincenal", "Quincenal"),
    ("💰 Mensual", "Mensual"),
    ("📊 Jornal", "Jornal diario"),
    ("🎁 Bono", "Bonificacion"),
    ("💵 Préstamo", "Prestamo"),
    ("📉 Deducción", "Deduccion"),
]

BADGE_COLORS = {
    "Mensual": "#1565c0",
    "Quincenal": "#2e7d32",
    "Jornal diario": "#f57f17",
    "Bonificacion": "#7b1fa2",
    "Prestamo": "#c62828",
    "Anticipo": "#e65100",
    "Deduccion": "#424242",
}

def _badge(tipo):
    color = BADGE_COLORS.get(tipo, "#555")
    return f'<span style="background:{color};color:#fff;padding:2px 8px;border-radius:10px;font-size:11px;font-weight:600">{tipo}</span>'

def render_nomina(supabase):
    PA = st.session_state.nombre_proyecto
    usuario = st.session_state.usuario_actual
    es_dir = st.session_state.rol_actual == "Director"

    st.markdown(f'''
    <div style="background:#880e4f;padding:14px 24px;border-radius:10px;margin-bottom:20px;display:flex;align-items:center;gap:14px">
        <span style="font-size:28px">💵</span>
        <div>
            <div style="color:#fff;font-size:18px;font-weight:700">Control de Nómina</div>
            <div style="color:#f8bbd0;font-size:12px">Pagos y deducciones - {PA}</div>
        </div>
    </div>
    ''', unsafe_allow_html=True)

    with st.expander("➕ Registrar movimiento", expanded=True):
        row1_tipos = TIPOS_RAPIDOS[:3]
        row2_tipos = TIPOS_RAPIDOS[3:]
        col_r1 = st.columns(2)
        for i, (label, tipo) in enumerate(row1_tipos):
            with col_r1[i]:
                if st.button(label, key=f"qtipo_nom_{tipo}", use_container_width=True):
                    st.session_state.nom_tipo_sel = tipo
                    st.rerun()
        col_r2 = st.columns(2)
        for i, (label, tipo) in enumerate(row2_tipos):
            with col_r2[i]:
                if st.button(label, key=f"qtipo_nom_{tipo}", use_container_width=True):
                    st.session_state.nom_tipo_sel = tipo
                    st.rerun()

        default_tipo = st.session_state.get("nom_tipo_sel", "Quincenal")

        with st.form("form_nom_rapido"):
            col1, col2 = st.columns(2)
            with col1:
                trabajador = st.text_input("Trabajador:", key="nom_trab_new", placeholder="Nombre completo")
                valor = st.number_input("Valor ($):", min_value=0, step=50000, key="nom_valor_new", format="%d")
            with col2:
                tipo = st.selectbox("Tipo:", ["Mensual", "Quincenal", "Jornal diario", "Bonificacion", "Prestamo", "Anticipo", "Deduccion"],
                    index=["Mensual", "Quincenal", "Jornal diario", "Bonificacion", "Prestamo", "Anticipo", "Deduccion"].index(default_tipo) if default_tipo in ["Mensual", "Quincenal", "Jornal diario", "Bonificacion", "Prestamo", "Anticipo", "Deduccion"] else 0,
                    key="nom_tipo_new")
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

    with st.expander("📋 Movimientos registrados", expanded=False):
        dfn = get_nomina(supabase, PA)

        if dfn.empty:
            st.info("📭 No hay movimientos de nómina")
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
            n1, n2 = st.columns(2)
            n1.metric("Ingresos", fmt_cop(ing))
            n2.metric("Préstamos", fmt_cop(pre))
            n1, n2 = st.columns(2)
            n1.metric("Deducciones", fmt_cop(ded))
            n2.metric("Neto", fmt_cop(ing - pre - ded))

            st.markdown("**Distribución de Nómina**")
            nom_chart = df_nf.groupby("tipo")["valor"].sum().sort_values(ascending=True)
            st.bar_chart(nom_chart, height=300)

        if df_nf.empty:
            st.info("📭 No hay datos con los filtros seleccionados")
            return

        df_sorted = df_nf.sort_values("fecha", ascending=False) if "fecha" in df_nf.columns else df_nf

        rows = [df_sorted.iloc[i:i+2] for i in range(0, len(df_sorted), 2)]
        for row_pair in rows:
            left_col, right_col = st.columns(2)
            for col_idx, (idx, row) in enumerate(row_pair.iterrows()):
                current_col = left_col if col_idx == 0 else right_col
                with current_col:
                    trab = row.get("trabajador", "")
                    tipo = row.get("tipo", "")
                    valor_raw = row.get("valor", 0)
                    fecha = row.get("fecha", "")
                    notas = row.get("notas", "")
                    rec_id = row.get("id", "")

                    label_html = f'{trab} &nbsp;{_badge(tipo)}&nbsp; — &nbsp;**{fmt_cop(valor_raw)}**'

                    with st.expander(label_html):
                        st.markdown(f"**Fecha:** {fecha}")
                        st.markdown(f"**Trabajador:** {trab}")
                        st.markdown(f"**Tipo:** {tipo}")
                        st.markdown(f"**Valor:** {fmt_cop(valor_raw)}")
                        if notas and str(notas).strip():
                            st.markdown(f"**Notas:** {notas}")

                        if es_dir:
                            st.markdown("---")
                            col_edit1, col_edit2 = st.columns([3, 1])
                            with col_edit1:
                                e_trab = st.text_input("Trabajador", value=str(trab), key=f"nom_e_trab_{rec_id}")
                                e_tipo = st.selectbox("Tipo", ["Mensual", "Quincenal", "Jornal diario", "Bonificacion", "Prestamo", "Anticipo", "Deduccion"],
                                    index=["Mensual", "Quincenal", "Jornal diario", "Bonificacion", "Prestamo", "Anticipo", "Deduccion"].index(tipo) if tipo in ["Mensual", "Quincenal", "Jornal diario", "Bonificacion", "Prestamo", "Anticipo", "Deduccion"] else 0,
                                    key=f"nom_e_tipo_{rec_id}")
                                e_valor = st.number_input("Valor", value=int(valor_raw) if pd.notna(valor_raw) else 0, step=50000, key=f"nom_e_valor_{rec_id}", format="%d")
                                e_notas = st.text_input("Notas", value=str(notas) if pd.notna(notas) else "", key=f"nom_e_notas_{rec_id}")

                                if st.button("💾 Guardar", key=f"nom_save_{rec_id}", type="primary", use_container_width=True):
                                    upd = {
                                        "trabajador": e_trab.strip(),
                                        "tipo": e_tipo,
                                        "valor": e_valor,
                                        "notas": e_notas.strip(),
                                    }
                                    if e_trab.strip() and e_valor > 0:
                                        try:
                                            update_record(supabase, "nomina", "id", rec_id, upd)
                                            st.success("✅ Registro actualizado")
                                            st.cache_data.clear()
                                            st.rerun()
                                        except Exception as e:
                                            st.error(f"❌ Error: {e}")
                                    else:
                                        st.error("⚠️ Complete trabajador y valor")
                            with col_edit2:
                                st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
                                if st.button("🗑️ Eliminar", key=f"nom_del_{rec_id}", use_container_width=True):
                                    try:
                                        delete_record(supabase, "nomina", "id", rec_id)
                                        st.success("✅ Registro eliminado")
                                        st.cache_data.clear()
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"❌ Error: {e}")

