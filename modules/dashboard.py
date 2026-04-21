# modules/dashboard.py
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from supabase import Client
from database.queries import get_actividades, get_avances, get_tareas, get_nomina, get_materiales, get_asistencia, insert_avance, update_record, delete_record
from utils.formatting import fmt_cop, fmt_dec
from utils.seed_data import seed_actividades_data, seed_avances_data, seed_config_data
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
        ag.columns = ["id", "cantidad_ejecutada"]
        dr = dr.merge(ag, on="id", how="left")
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
        margin=dict(t=50, b=20, l=20, r=20), height=420,
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
        margin=dict(t=40, b=20, l=20, r=20), height=320,
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
    df_map["label"] = df_map["id"] + "<br>" + df_map["descripcion"].str[:30]
    df_map["pct_text"] = df_map["pct_avance"].apply(lambda x: f"{x:.0f}%")
    df_map["valor_text"] = df_map["valor_total"].apply(lambda x: fmt_cop(x))
    df_map["hover"] = ("<b>" + df_map["id"] + "</b> — " + df_map["descripcion"].str[:50] + "<br>" +
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
        margin=dict(t=30, b=10, l=10, r=10), height=650,
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
    df_sun["label"] = df_sun["id"] + " " + df_sun["descripcion"].str[:25]
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
    fig.update_layout(margin=dict(t=10, b=10, l=10, r=10), height=650,
        paper_bgcolor='#f9f9f9',
        coloraxis_colorbar=dict(
            title=dict(text="% Avance", side="right", font=dict(size=14, color="#000000")),
            thickness=20, len=0.7,
            tickfont=dict(size=13, color="#000000")
        ))
    st.plotly_chart(fig, use_container_width=True)

def render_dashboard(supabase: Client):
    PA = st.session_state.nombre_proyecto
    config = st.session_state.datos_proyecto
    es_dir = st.session_state.rol_actual == "Director"

    st.markdown(f'''
    <div style="background:#075e54;padding:18px 28px;border-radius:12px;margin-bottom:24px">
        <h2 style="color:#fff;margin:0">📊 Panel de Control</h2>
        <p style="color:#b2dfdb;margin:5px 0 0 0">Seguimiento en tiempo real  •  {PA}</p>
    </div>
    ''', unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    costo_directo = config.get("total_costo_directo", 0) or 0
    suministros = config.get("total_costo_suministros", 0) or 0
    costo_obra = config.get("costo_total_obra", 0) or 0
    costo_total = config.get("costo_total_proyecto", 0) or 0
    c1.metric("Costo Directo", fmt_cop(costo_directo))
    c2.metric("Suministros", fmt_cop(suministros))
    c3.metric("Costo Obra", fmt_cop(costo_obra))
    c4.metric("Total Proyecto", fmt_cop(costo_total))
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

    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("Total Actividades", total_act)
    k2.metric("Con Avance", con_avance)
    k3.metric("Completadas", completadas)
    k4.metric("% Avance", f"{pct_avance}%")
    k5.metric("$ Ejecutado", fmt_cop(valor_ejecutado))
    st.divider()

    # ═══ PESTAÑAS POR SECCION ═══
    tabs = st.tabs(["Actividades", "Tareas", "Inventario", "Asistencia", "Nomina"])

    # ──── TAB: ACTIVIDADES ────
    with tabs[0]:
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

            st.markdown("### 🍩 Estado General del Proyecto")
            col_g1, col_g2, col_g3 = st.columns(3)
            with col_g1:
                _donut_progress(pct_avance, "Avance Global")
        with col_g2:
            est_labels = ["Completadas", "En Progreso", "Sin Avance"]
            est_values = [completadas, con_avance - completadas, sin_avance]
            est_colors = ["#b6d7a8", "#f9e0a0", "#f4cccc"]
            _pie_chart(est_labels, est_values, "Estado de Actividades", colors=est_colors)
            with col_g3:
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
                    st.bar_chart(chart_data, height=350)
                with col_b2:
                    st.markdown("**$ Ejecutado vs $ Total por Componente**")
                    comp_chart = comp_avance[["componente", "valor_total", "valor_ejecutado"]].copy()
                    comp_chart["componente"] = comp_chart["componente"].str[:25]
                    comp_chart = comp_chart.set_index("componente")
                    comp_chart.columns = ["Total", "Ejecutado"]
                    st.bar_chart(comp_chart, height=350)

    # ──── TAB: TAREAS ────
    with tabs[1]:
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

                st.markdown("**Cambiar estado de tarea:**")
                tar_options = dtar["id_tarea"] + " — " + dtar["descripcion"].str[:60] + " [" + dtar["estado"] + "]"
                sel_tar = st.selectbox("Seleccionar tarea:", tar_options.tolist(), key="dash_tar_sel")
                if sel_tar:
                    sel_id = sel_tar.split(" — ")[0]
                    tar_row = dtar[dtar["id_tarea"] == sel_id].iloc[0]
                    col_te, col_tp, col_tn = st.columns(3)
                    with col_te:
                        nuevo_est = st.selectbox("Nuevo estado:", ["Pendiente", "En progreso", "Completada"],
                            index=["Pendiente", "En progreso", "Completada"].index(tar_row["estado"]) if tar_row["estado"] in ["Pendiente", "En progreso", "Completada"] else 0,
                            key="dash_tar_estado")
                    with col_tp:
                        nuevo_pri = st.selectbox("Prioridad:", ["Alta", "Media", "Baja"],
                            index=["Alta", "Media", "Baja"].index(tar_row["prioridad"]) if "prioridad" in tar_row and tar_row["prioridad"] in ["Alta", "Media", "Baja"] else 1,
                            key="dash_tar_pri")
                    with col_tn:
                        nueva_nota = st.text_input("Notas:", value=str(tar_row.get("notas", "") or ""), key="dash_tar_nota")
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
    with tabs[2]:
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
                fig.update_layout(title=dict(text="Volumen Entradas vs Salidas", font=dict(size=20, color="#000000"), x=0.5), margin=dict(t=50, b=20, l=20, r=20), height=420, paper_bgcolor='#f9f9f9')
                st.plotly_chart(fig, use_container_width=True)

    # ──── TAB: ASISTENCIA ────
    with tabs[3]:
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
                    st.bar_chart(cargo_counts, height=350)

    # ──── TAB: NOMINA ────
    with tabs[4]:
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
                    n1, n2, n3, n4 = st.columns(4)
                    n1.metric("Total Pagos", fmt_cop(ing))
                    n2.metric("Préstamos", fmt_cop(pre))
                    n3.metric("Deducciones", fmt_cop(ded))
                    n4.metric("Neto", fmt_cop(ing - pre - ded))
                with col_n2:
                    nom_labels = dfn.groupby("tipo")["valor"].sum().sort_values(ascending=False).index.tolist()
                    nom_values = dfn.groupby("tipo")["valor"].sum().sort_values(ascending=False).values.tolist()
                    nom_colors_map = {"Mensual": "#b6d7a8", "Quincenal": "#d5e8d4", "Jornal diario": "#f9e0a0",
                        "Bonificacion": "#ffe0b2", "Prestamo": "#f4cccc", "Anticipo": "#f9e0a0", "Deduccion": "#e8c8c8"}
                    nc = [nom_colors_map.get(l, "#95a5a6") for l in nom_labels]
                    _pie_chart(nom_labels, nom_values, "Distribución de Nómina", colors=nc)

    st.divider()

    # ═══ REGISTRAR AVANCE POR DESPLEGABLES ═══

    df_act_list = df_ca.copy() if not df_ca.empty else pd.DataFrame()
    if not df_act_list.empty:
        with st.expander("Registrar Avance", expanded=False):
            act_options = (df_act_list["id"] + " — " + df_act_list["descripcion"].str[:50] + " (" + df_act_list["pct_avance"].astype(str) + "%)").tolist()
            col_av1, col_av2, col_av3 = st.columns([3, 1, 1])
        with col_av1:
            sel_actividad = st.selectbox("Actividad:", act_options, key="dash_av_actividad")
        with col_av2:
            cant_avance = st.number_input("Cantidad ejecutada:", min_value=0.0, step=1.0, key="dash_av_cant")
        with col_av3:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("💾 Guardar Avance", type="primary", use_container_width=True, key="btn_save_avance_dropdown"):
                if sel_actividad and cant_avance > 0:
                    sel_id = sel_actividad.split(" — ")[0]
                    data = {
                        "proyecto": PA,
                        "fecha": datetime.date.today().isoformat(),
                        "id_item": sel_id,
                        "cantidad": cant_avance,
                        "usuario": st.session_state.usuario_actual
                    }
                    try:
                        insert_avance(supabase, data)
                        st.success(f"✅ Avance registrado: {cant_avance} a actividad {sel_id}")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error: {e}")
                else:
                    st.warning("⚠️ Seleccione una actividad e ingrese una cantidad > 0")

    # ═══ TABLA RESUMEN ═══
    with st.expander("Tabla de Actividades", expanded=False):
        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1:
            componentes = df_ca["componente"].unique().tolist() if "componente" in df_ca.columns else []
            filtro_comp = st.multiselect("Componente:", componentes, key="dash_fcomp")
        with col_f2:
            capitulos = df_ca["capitulo"].unique().tolist() if "capitulo" in df_ca.columns else []
            filtro_cap = st.multiselect("Capítulo:", capitulos, key="dash_fcap")
        with col_f3:
            buscar = st.text_input("Buscar actividad:", key="dash_buscar")

        df_filt = df_ca.copy()
        if filtro_comp and "componente" in df_filt.columns:
            df_filt = df_filt[df_filt["componente"].isin(filtro_comp)]
        if filtro_cap and "capitulo" in df_filt.columns:
            df_filt = df_filt[df_filt["capitulo"].isin(filtro_cap)]
        if buscar and "descripcion" in df_filt.columns:
            df_filt = df_filt[df_filt["descripcion"].str.contains(buscar, case=False, na=False)]

        if df_filt.empty:
            st.info("No hay actividades con los filtros seleccionados")
        else:
            display_cols = [c for c in ["id", "capitulo", "componente", "descripcion", "unidad", "cantidad_total", "cantidad_ejecutada", "pct_avance", "valor_total", "valor_ejecutado"] if c in df_filt.columns]
            tbl_config = {
                "id": st.column_config.TextColumn("ID", disabled=True, width="small"),
                "capitulo": st.column_config.TextColumn("Capítulo", disabled=True, width="small"),
                "componente": st.column_config.TextColumn("Componente", disabled=True, width="medium"),
                "descripcion": st.column_config.TextColumn("Descripción", disabled=True, width="large"),
                "unidad": st.column_config.TextColumn("Unidad", disabled=True, width="small"),
                "cantidad_total": st.column_config.NumberColumn("Cant. Total", disabled=True, format="%.2f", width="small"),
                "cantidad_ejecutada": st.column_config.NumberColumn("Cant. Ejec.", disabled=True, format="%.2f", width="small"),
                "pct_avance": st.column_config.NumberColumn("% Avance", disabled=True, format="%.1f %%", width="small"),
                "valor_total": st.column_config.NumberColumn("Valor Total", disabled=True, format="$ %,.0f", width="medium"),
                "valor_ejecutado": st.column_config.NumberColumn("Valor Ejec.", disabled=True, format="$ %,.0f", width="medium"),
            }
            config_f = {k: v for k, v in tbl_config.items() if k in display_cols}
            st.dataframe(df_filt[display_cols], column_config=config_f, use_container_width=True, hide_index=True, key="df_actividades_dash")
