# modules/dashboard.py
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from database.queries import get_actividades, get_avances, get_tareas, get_nomina, get_materiales, get_asistencia, insert_avance, update_record, delete_record
from utils.formatting import fmt_cop, fmt_dec
import datetime

def calcular_avances(df_act, df_av):
    if df_act.empty:
        return pd.DataFrame()
    dr = df_act.copy()
    for c in ["valor_unitario", "cantidad_total", "valor_total"]:
        if c in dr.columns:
            dr[c] = pd.to_numeric(dr[c], errors="coerce").fillna(0)
    dr["cantidad_ejecutada"] = 0.0
    if not df_av.empty and "id_item" in df_av.columns:
        ag = df_av.groupby("id_item")["cantidad"].sum().reset_index()
        ag.columns = ["codigo", "cantidad_ejecutada"]
        dr = dr.merge(ag, on="codigo", how="left")
        if "cantidad_ejecutada_y" in dr.columns:
            dr["cantidad_ejecutada"] = dr["cantidad_ejecutada_y"].fillna(0)
            dr.drop(columns=["cantidad_ejecutada_x", "cantidad_ejecutada_y"], inplace=True, errors="ignore")
        elif "cantidad_ejecutada" in dr.columns:
            dr["cantidad_ejecutada"] = dr["cantidad_ejecutada"].fillna(0)
    dr["pct_avance"] = dr.apply(
        lambda r: min(round(r["cantidad_ejecutada"] / r["cantidad_total"] * 100, 1) if r["cantidad_total"] > 0 else 0, 100),
        axis=1
    )
    dr["valor_ejecutado"] = dr["cantidad_ejecutada"] * dr["valor_unitario"]
    return dr

def _pie_chart(labels, values, title, colors=None):
    kwargs = dict(labels=labels, values=values, hole=0.45,
        textinfo='label+percent', textfont_size=16, textfont_color='#000000',
        hovertemplate='<b>%{label}</b><br>%{value:,.0f}<br>%{percent}<extra></extra>',
        marker_line_color='#333333', marker_line_width=2)
    if colors:
        kwargs['marker'] = dict(colors=colors, line=dict(color='#333333', width=2))
    fig = go.Figure(data=[go.Pie(**kwargs)])
    fig.update_layout(
        title=dict(text=title, font=dict(size=20, color='#000000'), x=0.5),
margin=dict(t=50, b=20, l=20, r=20), height=350,
        paper_bgcolor='#f9f9f9', plot_bgcolor='#f9f9f9',
        legend=dict(orientation='h', yanchor='bottom', y=-0.15, xanchor='center', x=0.5, font=dict(size=14, color='#000000'))
    )
    st.plotly_chart(fig, use_container_width=True)

def _donut_progress(pct, label="Avance Global"):
    fig = go.Figure(data=[go.Pie(
        labels=[label, 'Restante'], values=[pct, 100 - pct], hole=0.7,
        marker=dict(colors=['#b6d7a8' if pct >= 50 else '#f4cccc', '#cccccc'], line=dict(color='#333333', width=2)),
        textinfo='none', hovertemplate='%{label}: %{value:.1f}%<extra></extra>'
    )])
    fig.update_layout(
        margin=dict(t=40, b=20, l=20, r=20), height=280,
        paper_bgcolor='#f9f9f9', plot_bgcolor='#f9f9f9',
        annotations=[dict(text=f'<b>{pct:.1f}%</b>', x=0.5, y=0.5, font_size=38, font_color='#000000', showarrow=False),
                      dict(text=label, x=0.5, y=0.35, font_size=16, font_color='#555555', showarrow=False)]
    )
    st.plotly_chart(fig, use_container_width=True)

def _treemap_avance(df_ca):
    if df_ca.empty or "componente" not in df_ca.columns:
        st.info("No hay datos de actividades para mostrar el mapa.")
        return
    df_map = df_ca.copy()
    df_map["label"] = df_map["codigo"] + "<br>" + df_map["descripcion"].str[:30]
    df_map["pct_text"] = df_map["pct_avance"].apply(lambda x: f"{x:.0f}%")
    df_map["valor_text"] = df_map["valor_total"].apply(lambda x: fmt_cop(x))
    df_map["hover"] = ("<b>" + df_map["codigo"] + "</b> — " + df_map["descripcion"].str[:50] + "<br>" +
                       "Avance: " + df_map["pct_text"] + "<br>" +
                       "Ejecutado: " + df_map["valor_ejecutado"].apply(fmt_cop) + " / " + df_map["valor_text"])
    if "capitulo" in df_map.columns:
        path_col = ["capitulo", "componente", "label"]
    else:
        path_col = ["componente", "label"]
    color_vals = df_map["pct_avance"].tolist()
    fig = px.treemap(
        df_map, path=path_col, values="valor_total",
        color="pct_avance", color_continuous_scale=["#f4cccc", "#f9e0a0", "#b6d7a8"],
        range_color=[0, 100], custom_data=["hover"],
        hover_data={"pct_avance": False, "valor_total": False, "label": False, "hover": True}
    )
    fig.update_traces(
        hovertemplate="%{customdata[0]}<extra></extra>",
        textinfo="label+text",
        text=df_map["pct_text"].tolist(),
        textfont=dict(size=16, color="#000000"),
        textposition="middle center",
        marker_line_width=2,
        marker_line_color="#333333"
    )
    fig.update_layout(
        margin=dict(t=30, b=10, l=10, r=10), height=400,
        paper_bgcolor='#f9f9f9',
        coloraxis_colorbar=dict(
            title=dict(text="% Avance", side="right", font=dict(size=14, color="#000000")),
            thickness=20, len=0.7,
            tickfont=dict(size=13, color="#000000")
        ),
        treemapcolorway=["#f4cccc", "#f9e0a0", "#b6d7a8"]
    )
    st.plotly_chart(fig, use_container_width=True)

def _sunburst_avance(df_ca):
    if df_ca.empty or "componente" not in df_ca.columns:
        return
    df_sun = df_ca.copy()
    df_sun["label"] = df_sun["codigo"] + " " + df_sun["descripcion"].str[:25]
    path_cols = ["capitulo", "componente", "label"] if "capitulo" in df_sun.columns else ["componente", "label"]
    fig = px.sunburst(
        df_sun, path=path_cols, values="valor_total",
        color="pct_avance", color_continuous_scale=["#f4cccc", "#f9e0a0", "#b6d7a8"],
        range_color=[0, 100]
    )
    fig.update_traces(
        textfont=dict(size=15, color="#000000"),
        textinfo="label+percent entry",
        insidetextorientation="radial",
        marker_line_width=2,
        marker_line_color="#333333"
    )
    fig.update_layout(margin=dict(t=10, b=10, l=10, r=10), height=400,
        paper_bgcolor='#f9f9f9',
        coloraxis_colorbar=dict(
            title=dict(text="% Avance", side="right", font=dict(size=14, color="#000000")),
            thickness=20, len=0.7,
            tickfont=dict(size=13, color="#000000")
        ))
    st.plotly_chart(fig, use_container_width=True)

def render_dashboard(supabase):
    PA = st.session_state.nombre_proyecto
    config = st.session_state.datos_proyecto
    es_dir = st.session_state.rol_actual == "Director"

    st.markdown(f'''
    <div style="background:#075e54;padding:18px 28px;border-radius:12px;margin-bottom:24px">
        <h2 style="color:#fff;margin:0">📊 Panel de Control</h2>
        <p style="color:#b2dfdb;margin:5px 0 0 0">Seguimiento en tiempo real  •  {PA}</p>
    </div>
    ''', unsafe_allow_html=True)

    st.divider()

    df_act = get_actividades(supabase)
    df_av = get_avances(supabase, PA)
    df_ca = calcular_avances(df_act, df_av)

    if df_act.empty:
        st.warning("No hay actividades cargadas.")
        st.stop()

    total_act = len(df_ca) if not df_ca.empty else 0
    con_avance = int((df_ca["cantidad_ejecutada"] > 0).sum()) if not df_ca.empty else 0
    completadas = int((df_ca["pct_avance"] >= 100).sum()) if not df_ca.empty else 0
    sin_avance = total_act - con_avance
    valor_ejecutado = df_ca["valor_ejecutado"].sum() if not df_ca.empty else 0
    valor_total = df_ca["valor_total"].sum() if not df_ca.empty else 0
    pct_avance = round((df_ca["pct_avance"] * df_ca["valor_total"]).sum() / valor_total, 1) if valor_total > 0 else 0

    # ═══ PESTAÑAS POR SECCION ═══
    presupuesto_obra = float(config.get("costo_total_obra", 0))
    presupuesto_directo = float(config.get("total_costo_directo", 0))
    presupuesto_suministros = float(config.get("total_costo_suministros", 0))
    presupuesto_total = float(config.get("costo_total_proyecto", presupuesto_obra))
    df_nom = get_nomina(supabase, PA)
    total_nomina = float(df_nom["valor"].sum()) if not df_nom.empty and "valor" in df_nom.columns else 0.0

    tabs = st.tabs(["💰 Presupuesto", "Actividades", "Tareas", "Inventario", "Asistencia", "Nomina"])

    # ──── TAB: PRESUPUESTO ────
    with tabs[0]:
        st.markdown("### 💰 Presupuesto vs Ejecutado")
        c1, c2 = st.columns(2)
        with c1:
            st.metric("📋 Presupuesto Obra", fmt_cop(presupuesto_obra))
        with c2:
            st.metric("🏗️ Ejecutado (Actividades)", fmt_cop(valor_ejecutado),
                      delta=f"{float(valor_ejecutado) / presupuesto_obra * 100:.1f}%" if presupuesto_obra > 0 else None)
        c1, c2 = st.columns(2)
        with c1:
            st.metric("🔩 Costo Directo", fmt_cop(presupuesto_directo))
        with c2:
            st.metric("📦 Suministros", fmt_cop(presupuesto_suministros))
        c1, c2 = st.columns(2)
        with c1:
            st.metric("👷 Nomina Pagada", fmt_cop(total_nomina))
        with c2:
            st.metric("📊 Total Proyecto", fmt_cop(presupuesto_total))

        col_bc1, col_bc2 = st.columns(2)
        with col_bc1:
            ejecutado_presupuesto = min(valor_ejecutado, presupuesto_obra)
            pendiente = max(presupuesto_obra - valor_ejecutado, 0)
            _pie_chart(
                ["Ejecutado", "Pendiente"],
                [float(ejecutado_presupuesto), float(pendiente)],
                "Presupuesto de Obra",
                colors=["#4CAF50", "#E0E0E0"]
            )
        with col_bc2:
            if not df_ca.empty and "componente" in df_ca.columns:
                comp_costos = df_ca.groupby("componente").agg(
                    ejecutado=("valor_ejecutado", "sum"),
                    presupuesto=("valor_total", "sum")
                ).reset_index()
                comp_costos["componente"] = comp_costos["componente"].str[:25]
                comp_costos = comp_costos.sort_values("presupuesto", ascending=True).tail(6)
                comp_costos["ejecutado"] = comp_costos["ejecutado"].astype(float)
                comp_costos["presupuesto"] = comp_costos["presupuesto"].astype(float)

                fig = go.Figure()
                fig.add_trace(go.Bar(
                    y=comp_costos["componente"],
                    x=comp_costos["presupuesto"],
                    name="Presupuesto",
                    orientation='h',
                    marker_color="#E0E0E0",
                    text=comp_costos["presupuesto"].apply(fmt_cop),
                    textposition='outside',
                    textfont=dict(size=11, color="#666")
                ))
                fig.add_trace(go.Bar(
                    y=comp_costos["componente"],
                    x=comp_costos["ejecutado"],
                    name="Ejecutado",
                    orientation='h',
                    marker_color="#4CAF50",
                    text=comp_costos["ejecutado"].apply(fmt_cop),
                    textposition='inside',
                    textfont=dict(size=11, color="#fff")
                ))
                fig.update_layout(
                    barmode='overlay',
                    height=300,
                    margin=dict(l=10, r=80, t=10, b=10),
                    legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1, font=dict(size=11)),
                    paper_bgcolor="#f9f9f9",
                    plot_bgcolor="#f9f9f9"
                )
                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    # ──── TAB: ACTIVIDADES ────
    with tabs[1]:
        if df_ca.empty:
            st.info("No hay datos de actividades.")
        else:
            with st.expander("Mapa Interactivo de Actividades", expanded=True):
                map_view = st.radio("Vista del mapa:", ["Treemap (avance por presupuesto)", "Sunburst (avance por jerarquía)"],
                                     horizontal=True, key="dash_map_view")
            if "Treemap" in map_view:
                _treemap_avance(df_ca)
            else:
                _sunburst_avance(df_ca)

            with st.expander("📊 Estado General", expanded=False):
                st.markdown("### 🍩 Estado General del Proyecto")
                col_g1, col_g2 = st.columns(2)
                with col_g1:
                    _donut_progress(pct_avance, "Avance Global")
                with col_g2:
                    est_labels = ["Completadas", "En Progreso", "Sin Avance"]
                    est_values = [completadas, con_avance - completadas, sin_avance]
                    est_colors = ["#b6d7a8", "#f9e0a0", "#f4cccc"]
                    _pie_chart(est_labels, est_values, "Estado de Actividades", colors=est_colors)
                col_g1, col_g2 = st.columns(2)
                with col_g1:
                    comp_avance = None
                    if "componente" in df_ca.columns:
                        comp_avance = df_ca.groupby("componente").agg(
                            pct_promedio=("pct_avance", "mean"),
                            valor_total=("valor_total", "sum"),
                            valor_ejecutado=("valor_ejecutado", "sum"),
                            cantidad=("id", "count")
                        ).reset_index()
                        _pie_chart(
                            comp_avance["componente"].tolist(),
                            comp_avance["valor_ejecutado"].tolist(),
                            "$ Ejecutado por Componente",
                            colors=px.colors.qualitative.Bold[:len(comp_avance)]
                        )

                if comp_avance is not None:
                    st.divider()
                    col_b1, col_b2 = st.columns(2)
                    with col_b1:
                        st.markdown("**% Avance Promedio por Componente**")
                        chart_data = comp_avance.set_index("componente")["pct_promedio"]
                        chart_data.index = chart_data.index.str[:25]
                        st.bar_chart(chart_data, height=280)
                    with col_b2:
                        st.markdown("**$ Ejecutado vs $ Total por Componente**")
                        comp_chart = comp_avance[["componente", "valor_total", "valor_ejecutado"]].copy()
                        comp_chart["componente"] = comp_chart["componente"].str[:25]
                        comp_chart = comp_chart.set_index("componente")
                        comp_chart.columns = ["Total", "Ejecutado"]
                        st.bar_chart(comp_chart, height=280)

    # ──── TAB: TAREAS ────
    with tabs[2]:
        k1, k2 = st.columns(2)
        k1.metric("Total Actividades", total_act)
        k2.metric("Completadas", completadas)
        k1, k2 = st.columns(2)
        k1.metric("% Avance", f"{pct_avance}%")
        st.divider()

        dtar = get_tareas(supabase, PA)
        if dtar.empty:
            st.info("No hay datos de tareas.")
        else:
            if "estado" in dtar.columns:
                col_t1, col_t2 = st.columns(2)
                with col_t1:
                    estado_labels = dtar["estado"].value_counts().index.tolist()
                    estado_values = dtar["estado"].value_counts().values.tolist()
                    tarea_colors = {"Pendiente": "#f4cccc", "En progreso": "#f9e0a0", "Completada": "#b6d7a8"}
                    tc = [tarea_colors.get(l, "#3498db") for l in estado_labels]
                    _pie_chart(estado_labels, estado_values, "Distribución de Tareas", colors=tc)
                with col_t2:
                    if "prioridad" in dtar.columns:
                        pri_labels = dtar["prioridad"].value_counts().index.tolist()
                        pri_values = dtar["prioridad"].value_counts().values.tolist()
                        pri_colors = {"Alta": "#f4cccc", "Media": "#f9e0a0", "Baja": "#b6d7a8"}
                        pc = [pri_colors.get(l, "#9b59b6") for l in pri_labels]
                        _pie_chart(pri_labels, pri_values, "Tareas por Prioridad", colors=pc)

                with st.expander("✏️ Cambiar estado de tarea", expanded=False):
                    st.markdown("**Cambiar estado de tarea:**")
                    tar_options = dtar["id_tarea"] + " — " + dtar["descripcion"].str[:60] + " [" + dtar["estado"] + "]"
                    sel_tar = st.selectbox("Seleccionar tarea:", tar_options.tolist(), key="dash_tar_sel")
                    if sel_tar:
                        sel_id = sel_tar.split(" — ")[0]
                        tar_row = dtar[dtar["id_tarea"] == sel_id].iloc[0]
                        col_te, col_tp = st.columns(2)
                        with col_te:
                            nuevo_est = st.selectbox("Nuevo estado:", ["Pendiente", "En progreso", "Completada"],
                                index=["Pendiente", "En progreso", "Completada"].index(tar_row["estado"]) if tar_row["estado"] in ["Pendiente", "En progreso", "Completada"] else 0,
                                key="dash_tar_estado")
                            nueva_nota = st.text_input("Notas:", value=str(tar_row.get("notas", "") or ""), key="dash_tar_nota")
                        with col_tp:
                            nuevo_pri = st.selectbox("Prioridad:", ["Alta", "Media", "Baja"],
                                index=["Alta", "Media", "Baja"].index(tar_row["prioridad"]) if "prioridad" in tar_row and tar_row["prioridad"] in ["Alta", "Media", "Baja"] else 1,
                                key="dash_tar_pri")
                        if st.button("💾 Actualizar Tarea", type="primary", use_container_width=True, key="btn_update_tar_dash"):
                            from database.queries import update_tarea_estado
                            try:
                                update_tarea_estado(supabase, sel_id, nuevo_est, nueva_nota)
                                if nuevo_pri != tar_row.get("prioridad"):
                                    update_record(supabase, "tareas", "id_tarea", sel_id, {"prioridad": nuevo_pri})
                                st.success(f"✅ Tarea {sel_id} actualizada a **{nuevo_est}**")
                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ Error: {e}")

    # ──── TAB: INVENTARIO ────
    with tabs[3]:
        response_inv = supabase.table("control_inventario").select("*").eq("proyecto", PA).execute()
        if not response_inv.data:
            st.info("No hay datos de inventario")
        else:
            df_inv = pd.DataFrame(response_inv.data)
            col_i1, col_i2 = st.columns(2)
            with col_i1:
                if "tipo_movimiento" in df_inv.columns:
                    tipo_labels = df_inv["tipo_movimiento"].value_counts().index.tolist()
                    tipo_values = df_inv["tipo_movimiento"].value_counts().values.tolist()
                    _pie_chart(tipo_labels, tipo_values, "Movimientos por Tipo",
                        colors=["#b6d7a8" if l == "Entrada" else "#f4cccc" if l == "Salida" else "#f9e0a0" for l in tipo_labels])
            with col_i2:
                if "material" in df_inv.columns:
                    mat_labels = df_inv["material"].value_counts().head(8).index.tolist()
                    mat_values = df_inv["material"].value_counts().head(8).values.tolist()
                    _pie_chart(mat_labels, mat_values, "Distribución de Materiales",
                        colors=px.colors.qualitative.Bold[:len(mat_labels)])
            if "cantidad" in df_inv.columns and "tipo_movimiento" in df_inv.columns:
                ent = df_inv[df_inv["tipo_movimiento"] == "Entrada"]["cantidad"].sum() if "tipo_movimiento" in df_inv.columns else 0
                sal = df_inv[df_inv["tipo_movimiento"] == "Salida"]["cantidad"].sum() if "tipo_movimiento" in df_inv.columns else 0
                marker_colors = ['#b6d7a8', '#f4cccc']
                fig = go.Figure(go.Funnel(y=["Entradas", "Salidas"], x=[ent, sal], textinfo='value+percent total',
                    textfont=dict(size=16, color="#000000"),
                    marker=dict(color=marker_colors)))
                fig.update_layout(title=dict(text="Volumen Entradas vs Salidas", font=dict(size=20, color="#000000"), x=0.5), margin=dict(t=50, b=20, l=20, r=20), height=350, paper_bgcolor='#f9f9f9')
                st.plotly_chart(fig, use_container_width=True)

    # ──── TAB: ASISTENCIA ────
    with tabs[4]:
        from datetime import date as dt_mod
        dfa = get_asistencia(supabase, PA, dt_mod.today())
        if dfa.empty or "estado" not in dfa.columns:
            st.info("No hay datos de asistencia para hoy")
        else:
            ast_labels = dfa["estado"].value_counts().index.tolist()
            ast_values = dfa["estado"].value_counts().values.tolist()
            ast_colors_map = {"Presente": "#b6d7a8", "Ausente": "#f4cccc", "Permiso": "#f9e0a0", "Vacaciones": "#d5e8d4"}
            ac = [ast_colors_map.get(l, "#9b59b6") for l in ast_labels]
            col_a1, col_a2 = st.columns(2)
            with col_a1:
                _pie_chart(ast_labels, ast_values, "Asistencia de Hoy", colors=ac)
            with col_a2:
                if "cargo" in dfa.columns:
                    cargo_counts = dfa.groupby("cargo")["estado"].value_counts().unstack(fill_value=0)
                    st.bar_chart(cargo_counts, height=280)

    # ──── TAB: NOMINA ────
    with tabs[5]:
        if not es_dir:
            st.warning("⚠️ Solo el Director puede ver la nómina.")
        else:
            dfn = get_nomina(supabase, PA)
            if dfn.empty or "tipo" not in dfn.columns or "valor" not in dfn.columns:
                st.info("No hay datos de nómina.")
            else:
                col_n1, col_n2 = st.columns(2)
                with col_n1:
                    ing = dfn[dfn["tipo"].isin(["Mensual", "Quincenal", "Jornal diario", "Bonificacion"])]["valor"].sum()
                    pre = dfn[dfn["tipo"].isin(["Prestamo", "Anticipo"])]["valor"].sum()
                    ded = dfn[dfn["tipo"] == "Deduccion"]["valor"].sum() if "Deduccion" in dfn["tipo"].values else 0
                    n1, n2 = st.columns(2)
                    n1.metric("Pago Bruto", fmt_cop(ing))
                    n2.metric("Préstamos", fmt_cop(pre))
                    n1, n2 = st.columns(2)
                    n1.metric("Deducciones", fmt_cop(ded))
                    n2.metric("Neto", fmt_cop(ing - pre - ded))
                with col_n2:
                    nom_labels = dfn.groupby("tipo")["valor"].sum().sort_values(ascending=False).index.tolist()
                    nom_values = dfn.groupby("tipo")["valor"].sum().sort_values(ascending=False).values.tolist()
                    nom_colors_map = {"Mensual": "#b6d7a8", "Quincenal": "#d5e8d4", "Jornal diario": "#f9e0a0",
                        "Bonificacion": "#ffe0b2", "Prestamo": "#f4cccc", "Anticipo": "#f9e0a0", "Deduccion": "#e8c8c8"}
                    nc = [nom_colors_map.get(l, "#95a5a6") for l in nom_labels]
                    _pie_chart(nom_labels, nom_values, "Distribución de Nómina", colors=nc)

    st.divider()