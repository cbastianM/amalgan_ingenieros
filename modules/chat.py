# modules/chat.py
import streamlit as st
import datetime
import pandas as pd
import re
from database.queries import (
    insert_avance, get_actividades, get_trabajadores,
    get_avances, get_materiales, get_asistencia, get_nomina, get_tareas,
    update_record, delete_record, insert_record, insert_control_inventario,
    insert_control_maquinas, insertproveedor, insert_tarea, generar_id_tarea,
    update_tarea_estado
)
from utils.formatting import fmt_cop
from modules.dashboard import calcular_avances

MATERIALES_RAPIDOS = [
    ("🧱 Cemento", "Cemento", "bultos"),
    ("🏔️ Arena", "Arena", "m3"),
    ("🪨 Grava", "Grava", "m3"),
    ("🔩 Varilla", "Varilla", "varillas"),
    ("🧱 Ladrillo", "Ladrillo", "und"),
    ("💧 Piedra", "Piedra", "m3"),
]

BADGE_MAP = {
    "Pendiente": ("badge-pendiente", "#E65100", "#FFF3E0"),
    "En progreso": ("badge-progreso", "#1565C0", "#E3F2FD"),
    "Completada": ("badge-completada", "#2E7D32", "#E8F5E9"),
    "Solicitado": ("badge-pendiente", "#E65100", "#FFF3E0"),
    "En proceso": ("badge-progreso", "#1565C0", "#E3F2FD"),
    "Entregado": ("badge-completada", "#2E7D32", "#E8F5E9"),
    "Cancelado": ("badge-baja", "#757575", "#F5F5F5"),
    "Entrada": ("badge-entrada", "#2E7D32", "#E8F5E9"),
    "Salida": ("badge-salida", "#C62828", "#FFEBEE"),
    "Alta": ("badge-alta", "#C62828", "#FFEBEE"),
    "Media": ("badge-media", "#F57F17", "#FFF8E1"),
    "Baja": ("badge-baja", "#757575", "#F5F5F5"),
}


def _badge(text):
    _, fg, bg = BADGE_MAP.get(text, ("", "#555", "#EEE"))
    return f'<span style="display:inline-block;padding:2px 8px;border-radius:10px;font-size:11px;font-weight:600;color:{fg};background:{bg}">{text}</span>'


BADGE_EMOJI = {
    "Pendiente": "🟠", "En progreso": "🔵", "Completada": "🟢",
    "Solicitado": "🟠", "En proceso": "🔵", "Entregado": "🟢",
    "Cancelado": "⚫", "Entrada": "🟢", "Salida": "🔴",
    "Alta": "🔴", "Media": "🟡", "Baja": "⚪",
}


def _badge_text(text):
    emoji = BADGE_EMOJI.get(text, "⚪")
    return f"{emoji} {text}"


def _pct_bar(pct):
    pct = min(float(pct), 100)
    color = "#4CAF50" if pct >= 100 else "#FF9800" if pct >= 50 else "#2196F3" if pct > 0 else "#9E9E9E"
    return f'''<div style="background:#E0E0E0;border-radius:4px;height:5px;overflow:hidden;margin-top:2px">
        <div style="background:{color};width:{pct:.1f}%;height:100%;border-radius:4px"></div>
    </div>'''


def procesar_mensaje(texto: str, proyecto: str, usuario: str, supabase) -> str:
    tl = texto.lower()
    rol = st.session_state.get("rol_actual", "")
    if "avance" in tl:
        if rol not in ("Director", "Residente"):
            return "🚫 Solo Directores y Residentes pueden registrar avances"
        match = re.search(r'(\d+\.\d+\.\d+|[A-Z]{2,3}-\d+)\s+(\d+(?:\.\d+)?)', texto, re.IGNORECASE)
        if match:
            id_item = match.group(1)
            cantidad = float(match.group(2))
            df_act = get_actividades(supabase)
            if not df_act.empty and id_item in df_act["codigo"].values:
                data = {"proyecto": proyecto, "fecha": datetime.date.today().isoformat(), "id_item": id_item, "cantidad": cantidad, "usuario": usuario}
                insert_avance(supabase, data)
                return f"✅ Avance registrado: {cantidad} al item **{id_item}**"
            else:
                return f"❌ El item **{id_item}** no existe en las actividades"
        else:
            return "📝 Formato: `avance 1.1.01 15`"
    elif "material" in tl or "necesito" in tl:
        req = re.sub(r'(?i)(material|necesito)[:\s]*', '', texto).strip()
        if req:
            data = {"proyecto": proyecto, "fecha": datetime.date.today().isoformat(), "requerimiento": req, "estado": "Solicitado", "usuario": usuario}
            supabase.table("materiales").insert(data).execute()
            return f"📦 Material solicitado: **{req}**"
        else:
            return "📝 Ejemplo: `material: 50 bultos de cemento`"
    elif "asistencia" in tl:
        match = re.search(r'asistencia[:\s]*(.+?)(?:\s*-\s*(.+?))?(?:\s*-\s*(.+?))?', texto, re.IGNORECASE)
        if match:
            nombre = match.group(1).strip()
            cargo = match.group(2).strip() if match.group(2) else "General"
            estado = match.group(3).strip() if match.group(3) else "Presente"
            data = {"proyecto": proyecto, "fecha": datetime.date.today().isoformat(), "trabajador": nombre, "cargo": cargo, "estado": estado, "usuario": usuario}
            supabase.table("asistencia").insert(data).execute()
            return f"👷 Asistencia: **{nombre}** - {estado}"
        else:
            return "📝 Ejemplo: `asistencia: Carlos - Albañil - Presente`"
    else:
        cmds = ["- `avance 1.1.01 15`"]
        cmds.append("- `material: cemento`")
        cmds.append("- `asistencia: Carlos - Presente`")
        return "💡 Comandos:\n" + "\n".join(cmds)


def render_chat(supabase):
    PA = st.session_state.nombre_proyecto
    usuario = st.session_state.usuario_actual
    es_dir = st.session_state.rol_actual == "Director"

    if "chat_historial" not in st.session_state:
        st.session_state.chat_historial = {}
    if PA not in st.session_state.chat_historial:
        st.session_state.chat_historial[PA] = [
            {"role": "assistant", "content": f"🏗️ Proyecto **{PA}** conectado. Usa los accesos rápidos o escribe comandos."}
        ]
    if "chat_mode" not in st.session_state:
        st.session_state.chat_mode = None

    st.markdown(f'''
    <div style="background:#075e54;padding:14px 18px;border-radius:12px;margin-bottom:14px;display:flex;align-items:center;gap:12px">
        <div style="background:#dfe5e7;border-radius:50%;width:44px;height:44px;display:flex;align-items:center;justify-content:center;font-size:22px">💬</div>
        <div>
            <div style="color:#fff;font-size:18px;font-weight:700">Chat de Obra</div>
            <div style="color:#b2dfdb;font-size:12px">{PA} — {usuario}</div>
        </div>
    </div>
    ''', unsafe_allow_html=True)

    rol = st.session_state.rol_actual
    _ALL_BUTTONS = [
        ("📊 Avances", "avances_tabla", {"Director", "Residente"}),
        ("📦 Inventario", "inventario_tabla", {"Director", "Almacenista", "Residente"}),
        ("👷 Asistencia", "asistencia_tabla", {"Director", "Residente", "Controlador"}),
        ("📋 Tareas", "tareas_tabla", {"Director", "Residente"}),
        ("💵 Nómina", "nomina_tabla", {"Director"}),
        ("🏢 Proveedores", "proveedores_tabla", {"Director"}),
        ("🚜 Máquinas", "maquinas_tabla", {"Director", "Controlador"}),
        ("🏗️ Materiales", "materiales_tabla", {"Director", "Residente", "Almacenista"}),
    ]
    botones = [(l, m) for l, m, roles in _ALL_BUTTONS if rol in roles]
    ncols = min(len(botones), 3)
    if ncols > 0:
        rows = [botones[i:i+ncols] for i in range(0, len(botones), ncols)]
        for row in rows:
            cols = st.columns(len(row))
            for idx, (label, mode) in enumerate(row):
                with cols[idx]:
                    if st.button(label, use_container_width=True, key=f"btn_chat_{mode}"):
                        st.session_state.chat_mode = mode
                        st.rerun()

    # ═══ AVANCES ═══
    if st.session_state.chat_mode == "avances_tabla":
        st.info("💡 Seleccione una actividad e ingrese el avance")
        df_act = get_actividades(supabase)
        df_av = get_avances(supabase, PA)
        df_ca = calcular_avances(df_act, df_av)
        if df_ca.empty:
            st.warning("⚠️ No hay actividades cargadas")
        else:
            filtro_comp = st.multiselect("Componente:", df_ca["componente"].unique().tolist() if "componente" in df_ca.columns else [], key="chat_av_comp")
            df_f = df_ca.copy()
            if filtro_comp and "componente" in df_f.columns:
                df_f = df_f[df_f["componente"].isin(filtro_comp)]

            k1, k2 = st.columns(2)
            k1.metric("Actividades", len(df_f))
            k2.metric("% Avance", f"{df_f['pct_avance'].mean():.1f}%" if not df_f.empty and 'pct_avance' in df_f.columns else "0%")
            k1, k2 = st.columns(2)
            k1.metric("Cant. Ejec.", f"{df_f['cantidad_ejecutada'].sum():.1f}" if not df_f.empty and 'cantidad_ejecutada' in df_f.columns else "0")

            st.markdown("---")
            card_items = list(df_f.iterrows())
            rows = [card_items[i:i+2] for i in range(0, len(card_items), 2)]
            for row_pair in rows:
                left_col, right_col = st.columns(2)
                for col_idx, (idx, row) in enumerate(row_pair):
                    current_col = left_col if col_idx == 0 else right_col
                    with current_col:
                        act_id = row.get("codigo", "")
                        desc = row.get("descripcion", "")
                        pct = row.get("pct_avance", 0)
                        c_ejec = row.get("cantidad_ejecutada", 0)
                        c_total = row.get("cantidad_total", 0)

                        preview = f"{act_id} — {str(desc)[:35]}{'...' if len(str(desc))>35 else ''}  {pct:.1f}%"

                        with st.expander(preview):
                            st.markdown(_pct_bar(pct), unsafe_allow_html=True)
                            line = f'<div style="display:flex;gap:16px;font-size:13px;margin:0;padding:0"><div><span style="color:#888;font-size:11px">Avance</span><br><b>{pct:.1f}%</b></div><div><span style="color:#888;font-size:11px">Cantidad</span><br><b>{c_ejec:.1f}/{c_total:.1f} {row.get("unidad", "")}</b></div></div>'
                            st.markdown(line, unsafe_allow_html=True)

                            nuevo = st.number_input("➕ Nuevo avance", min_value=0.0, step=1.0, key=f"chat_av_nuevo_{act_id}")
                            if st.button(f"💾 Registrar", type="primary", use_container_width=True, key=f"chat_av_save_{act_id}"):
                                if nuevo > 0:
                                    data = {"proyecto": PA, "fecha": datetime.date.today().isoformat(), "id_item": act_id, "cantidad": nuevo, "usuario": usuario}
                                    try:
                                        insert_avance(supabase, data)
                                        st.success(f"✅ Avance registrado: {nuevo} a {act_id}")
                                        st.cache_data.clear()
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"❌ Error: {e}")
                                else:
                                    st.warning("⚠️ Ingrese una cantidad mayor a 0")

        col_b1, col_b2 = st.columns(2)
        with col_b2:
            if st.button("❌ Cerrar", use_container_width=True, key="btn_close_chat_av"):
                st.session_state.chat_mode = None
                st.rerun()

    # ═══ INVENTARIO ═══
    elif st.session_state.chat_mode == "inventario_tabla":
        response = supabase.table("control_inventario").select("*").eq("proyecto", PA).execute()
        if not response.data:
            st.info("📭 No hay movimientos registrados")
        else:
            df = pd.DataFrame(response.data)
            col_f1, col_f2 = st.columns(2)
            with col_f1:
                filtro_tipo = st.selectbox("Tipo:", ["Todos", "Entrada", "Salida"], key="chat_inv_tipo")
            with col_f2:
                materiales_lista = ["Todos"] + sorted(df["material"].dropna().unique().tolist()) if "material" in df.columns else ["Todos"]
                filtro_material = st.selectbox("Material:", materiales_lista, key="chat_inv_mat")

            df_f = df.copy()
            if filtro_tipo != "Todos" and "tipo_movimiento" in df_f.columns:
                df_f = df_f[df_f["tipo_movimiento"] == filtro_tipo]
            if filtro_material != "Todos" and "material" in df_f.columns:
                df_f = df_f[df_f["material"] == filtro_material]

            if not df_f.empty:
                ent = len(df_f[df_f["tipo_movimiento"] == "Entrada"]) if "tipo_movimiento" in df_f.columns else 0
                sal = len(df_f[df_f["tipo_movimiento"] == "Salida"]) if "tipo_movimiento" in df_f.columns else 0
                k1, k2 = st.columns(2)
                k1.metric("Total", len(df_f))
                k2.metric("Entradas", ent)
                k1, k2 = st.columns(2)
                k1.metric("Salidas", sal)

                st.markdown("---")
                card_items = list(df_f.iterrows())
                rows = [card_items[i:i+2] for i in range(0, len(card_items), 2)]
                for row_pair in rows:
                    left_col, right_col = st.columns(2)
                    for col_idx, (idx, row) in enumerate(row_pair):
                        current_col = left_col if col_idx == 0 else right_col
                        with current_col:
                            tipo = row.get("tipo_movimiento", "")
                            tipo_badge = _badge_text(tipo)
                            preview = f"{tipo_badge} **{material}** — {cantidad} {row.get('unidad', '')}"

                            with st.expander(preview):
                                st.markdown(_badge(tipo), unsafe_allow_html=True)
                                c1, c2 = st.columns(2)
                                c1.text_input("Responsable", value=str(row.get("responsable", "")), key=f"chat_inv_resp_{idx}", disabled=True)
                                c2.text_input("Fecha", value=str(fecha), key=f"chat_inv_fecha_{idx}", disabled=True)
                                obs = row.get("observaciones", "")
                                if obs and str(obs) != "nan":
                                    st.caption(f"📝 {obs}")

            col_b1, col_b2 = st.columns(2)
            with col_b2:
                if st.button("❌ Cerrar", use_container_width=True, key="btn_close_chat_inv"):
                    st.session_state.chat_mode = None
                    st.rerun()

    # ═══ ASISTENCIA ═══
    elif st.session_state.chat_mode == "asistencia_tabla":
        from database.queries import get_asistencia
        dfa = get_asistencia(supabase, PA)
        if dfa.empty:
            st.info("📭 No hay registros de asistencia")
        else:
            col_f1, col_f2 = st.columns(2)
            with col_f1:
                filtro_fecha_ast = st.date_input("Fecha:", value=datetime.date.today(), key="chat_ast_fecha")
            with col_f2:
                valores_estado = ["Todos"] + dfa["estado"].dropna().unique().tolist() if "estado" in dfa.columns else ["Todos"]
                filtro_estado_ast = st.selectbox("Estado:", valores_estado, key="chat_ast_estado")

            df_ast = dfa.copy()
            if filtro_fecha_ast and "fecha" in df_ast.columns:
                df_ast = df_ast[df_ast["fecha"] == filtro_fecha_ast.isoformat()]
            if filtro_estado_ast != "Todos" and "estado" in df_ast.columns:
                df_ast = df_ast[df_ast["estado"] == filtro_estado_ast]

            if not df_ast.empty and "estado" in df_ast.columns:
                pres = int((df_ast["estado"] == "Presente").sum())
                aus = int((df_ast["estado"] == "Ausente").sum())
                perm = int((df_ast["estado"] == "Permiso").sum())
                k1, k2 = st.columns(2)
                k1.metric("Presentes", pres)
                k2.metric("Ausentes", aus)
                k1, k2 = st.columns(2)
                k1.metric("Permisos", perm)

            if not df_ast.empty:
                st.markdown("---")
                card_items = list(df_ast.iterrows())
                rows = [card_items[i:i+2] for i in range(0, len(card_items), 2)]
                for row_pair in rows:
                    left_col, right_col = st.columns(2)
                    for col_idx, (idx, row) in enumerate(row_pair):
                        current_col = left_col if col_idx == 0 else right_col
                        with current_col:
                            nombre = row.get("trabajador", "")
                            cargo = row.get("cargo", "")
                            estado = row.get("estado", "Presente")
                            preview = f"{_badge_text(estado)} **{nombre}** — {cargo}"
                            with st.expander(preview):
                                new_estado = st.selectbox("Estado", ["Presente", "Ausente", "Permiso", "Vacaciones"],
                                                           index=["Presente", "Ausente", "Permiso", "Vacaciones"].index(estado) if estado in ["Presente", "Ausente", "Permiso", "Vacaciones"] else 0,
                                                           key=f"chat_ast_est_{idx}")
                                if st.button("💾 Guardar", use_container_width=True, key=f"chat_ast_save_{idx}"):
                                    try:
                                        update_record(supabase, "asistencia", "id", row["id"], {"estado": new_estado})
                                        st.success(f"✅ {nombre} → {new_estado}")
                                        st.cache_data.clear()
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"❌ Error: {e}")

            col_b1, col_b2 = st.columns(2)
            with col_b2:
                if st.button("❌ Cerrar", use_container_width=True, key="btn_close_chat_ast"):
                    st.session_state.chat_mode = None
                    st.rerun()

    # ═══ TAREAS ═══
    elif st.session_state.chat_mode == "tareas_tabla":
        df_tareas = get_tareas(supabase, PA)
        if df_tareas.empty:
            st.info("📭 No hay tareas registradas")
        else:
            filtro_estado = st.selectbox("Estado:", ["Todos", "Pendiente", "En progreso", "Completada"], key="chat_tar_est")
            filtro_prioridad = st.selectbox("Prioridad:", ["Todas", "Alta", "Media", "Baja"], key="chat_tar_pri")

            df_f = df_tareas.copy()
            if filtro_estado != "Todos" and "estado" in df_f.columns:
                df_f = df_f[df_f["estado"] == filtro_estado]
            if filtro_prioridad != "Todas" and "prioridad" in df_f.columns:
                df_f = df_f[df_f["prioridad"] == filtro_prioridad]

            if not df_f.empty:
                card_items = list(df_f.iterrows())
                rows = [card_items[i:i+2] for i in range(0, len(card_items), 2)]
                for row_pair in rows:
                    left_col, right_col = st.columns(2)
                    for col_idx, (idx, row) in enumerate(row_pair):
                        current_col = left_col if col_idx == 0 else right_col
                        with current_col:
                            tid = row.get("id_tarea", "")
                            desc = row.get("descripcion", "")
                            prioridad = row.get("prioridad", "Media")
                            estado = row.get("estado", "Pendiente")
                            asignado = row.get("asignado_a", "")
                            fecha = row.get("fecha_limite", "")
                            notas = row.get("notas", "")

                            preview = f"**{tid}** — {str(desc)[:40]}  {_badge_text(estado)}  {_badge_text(prioridad)}"
                            with st.expander(preview):
                                c1, c2 = st.columns(2)
                                with c1:
                                    new_estado = st.selectbox("Estado", ["Pendiente", "En progreso", "Completada"],
                                                              index=["Pendiente", "En progreso", "Completada"].index(estado) if estado in ["Pendiente", "En progreso", "Completada"] else 0,
                                                              key=f"chat_tar_est_{idx}")
                                with c2:
                                    new_prioridad = st.selectbox("Prioridad", ["Alta", "Media", "Baja"],
                                                                index=["Alta", "Media", "Baja"].index(prioridad) if prioridad in ["Alta", "Media", "Baja"] else 1,
                                                                key=f"chat_tar_pri_{idx}")
                                new_notas = st.text_input("Notas", value=str(notas) if pd.notna(notas) else "", key=f"chat_tar_notas_{idx}")
                                st.caption(f"👤 {asignado}  |  📅 {fecha}")
                                if st.button("💾 Guardar", use_container_width=True, key=f"chat_tar_save_{idx}"):
                                    try:
                                        update_tarea_estado(supabase, tid, new_estado, new_notas)
                                        update_record(supabase, "tareas", "id_tarea", tid, {"prioridad": new_prioridad})
                                        st.success(f"✅ Tarea {tid} actualizada")
                                        st.cache_data.clear()
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"❌ Error: {e}")

            col_b1, col_b2 = st.columns(2)
            with col_b2:
                if st.button("❌ Cerrar", use_container_width=True, key="btn_close_chat_tar"):
                    st.session_state.chat_mode = None
                    st.rerun()

    # ═══ NÓMINA ═══
    elif st.session_state.chat_mode == "nomina_tabla":
        dfn = get_nomina(supabase, PA)
        if dfn.empty:
            st.info("📭 Sin movimientos de nómina")
        else:
            filtro_tipo = st.selectbox("Tipo:", ["Todos"] + dfn["tipo"].unique().tolist() if "tipo" in dfn.columns else ["Todos"], key="chat_nom_tipo")
            filtro_buscar = st.text_input("Buscar trabajador:", key="chat_nom_buscar")

            df_nf = dfn.copy()
            if filtro_tipo != "Todos" and "tipo" in df_nf.columns:
                df_nf = df_nf[df_nf["tipo"] == filtro_tipo]
            if filtro_buscar and "trabajador" in df_nf.columns:
                df_nf = df_nf[df_nf["trabajador"].str.contains(filtro_buscar, case=False, na=False)]

            if not df_nf.empty and "tipo" in df_nf.columns and "valor" in df_nf.columns:
                ing = df_nf[df_nf["tipo"].isin(["Mensual", "Quincenal", "Jornal diario", "Bonificacion"])]["valor"].sum()
                k1, k2 = st.columns(2)
                k1.metric("Pago Bruto", fmt_cop(ing))
                k2.metric("Préstamos", fmt_cop(df_nf[df_nf["tipo"].isin(["Prestamo", "Anticipo"])]["valor"].sum()))
                k1, k2 = st.columns(2)
                k1.metric("Deducciones", fmt_cop(df_nf[df_nf["tipo"] == "Deduccion"]["valor"].sum() if "Deduccion" in df_nf["tipo"].values else 0))

                st.markdown("---")
                card_items = list(df_nf.iterrows())
                rows = [card_items[i:i+2] for i in range(0, len(card_items), 2)]
                for row_pair in rows:
                    left_col, right_col = st.columns(2)
                    for col_idx, (idx, row) in enumerate(row_pair):
                        current_col = left_col if col_idx == 0 else right_col
                        with current_col:
                            tipo = row.get("tipo", "")
                            trabajador = row.get("trabajador", "")
                            valor = row.get("valor", 0)
                            fecha = row.get("fecha", "")
                            notas = row.get("notas", "")
                            preview = f"{_badge_text(tipo)} **{trabajador}** — {fmt_cop(valor)}"
                            with st.expander(preview):
                                st.markdown(_badge(tipo), unsafe_allow_html=True)
                                st.caption(f"📅 {fecha}")
                                if str(notas) and str(notas) != "nan":
                                    st.caption(f"📝 {notas}")

            col_b1, col_b2 = st.columns(2)
            with col_b2:
                if st.button("❌ Cerrar", use_container_width=True, key="btn_close_chat_nom"):
                    st.session_state.chat_mode = None
                    st.rerun()

    # ═══ PROVEEDORES ═══
    elif st.session_state.chat_mode == "proveedores_tabla":
        response = supabase.table("proveedores").select("*").execute()
        if not response.data:
            st.info("📭 No hay proveedores registrados")
        else:
            df_prov = pd.DataFrame(response.data)
            categorias = ["Todas"] + sorted(df_prov["categoria"].dropna().unique().tolist()) if "categoria" in df_prov.columns else ["Todas"]
            cat_sel = st.selectbox("Categoría:", categorias, key="chat_prov_cat")
            buscar_prov = st.text_input("Buscar:", key="chat_prov_buscar")

            df_pf = df_prov.copy()
            if cat_sel != "Todas" and "categoria" in df_pf.columns:
                df_pf = df_pf[df_pf["categoria"] == cat_sel]
            if buscar_prov and "nombre" in df_pf.columns:
                df_pf = df_pf[df_pf["nombre"].str.contains(buscar_prov, case=False, na=False)]

            if not df_pf.empty:
                st.markdown("---")
                card_items = list(df_pf.iterrows())
                rows = [card_items[i:i+2] for i in range(0, len(card_items), 2)]
                for row_pair in rows:
                    left_col, right_col = st.columns(2)
                    for col_idx, (idx, row) in enumerate(row_pair):
                        current_col = left_col if col_idx == 0 else right_col
                        with current_col:
                            nombre = row.get("nombre", "")
                            categoria = row.get("categoria", "")
                            contacto = row.get("contacto", "")
                            telefono = row.get("telefono", "")
                            preview = f"**{nombre}**  {_badge_text(categoria)}"
                            with st.expander(preview):
                                st.markdown(_badge(categoria), unsafe_allow_html=True)
                                c1, c2 = st.columns(2)
                                c1.text_input("Contacto", value=str(contacto), key=f"chat_prov_cont_{idx}", disabled=True)
                                c2.text_input("Teléfono", value=str(telefono), key=f"chat_prov_tel_{idx}", disabled=True)
                                direccion = row.get("direccion", "")
                                notas = row.get("notas", "")
                                if str(direccion) and str(direccion) != "nan":
                                    st.caption(f"📍 {direccion}")
                                if str(notas) and str(notas) != "nan":
                                    st.caption(f"📝 {notas}")

            col_b1, col_b2 = st.columns(2)
            with col_b2:
                if st.button("❌ Cerrar", use_container_width=True, key="btn_close_chat_prov"):
                    st.session_state.chat_mode = None
                    st.rerun()

    # ═══ MÁQUINAS ═══
    elif st.session_state.chat_mode == "maquinas_tabla":
        filtro_fecha_maq = st.date_input("Fecha:", value=datetime.date.today(), key="chat_maq_fecha")
        response = supabase.table("control_maquinas").select("*").eq("proyecto", PA).eq("fecha", filtro_fecha_maq.isoformat()).execute()
        if not response.data:
            st.info("📭 No hay registros para esta fecha")
        else:
            df = pd.DataFrame(response.data)
            col_f1, col_f2 = st.columns(2)
            with col_f1:
                filtro_tipo_maq = st.selectbox("Tipo:", ["Todos", "Volqueta", "Retroexcavadora", "Mototrac", "Grúa", "Compactador", "Mixer", "Otro"], key="chat_maq_tipo")
            with col_f2:
                filtro_placa = st.text_input("Buscar placa:", key="chat_maq_placa")

            df_mf = df.copy()
            if filtro_tipo_maq != "Todos" and "tipo_equipo" in df_mf.columns:
                df_mf = df_mf[df_mf["tipo_equipo"] == filtro_tipo_maq]
            if filtro_placa and "placa" in df_mf.columns:
                df_mf = df_mf[df_mf["placa"].str.contains(filtro_placa.upper(), na=False)]

            if not df_mf.empty:
                total_h = df_mf["horas_trabajadas"].sum() if "horas_trabajadas" in df_mf.columns else 0
                total_m3 = df_mf["volumen_m3"].sum() if "volumen_m3" in df_mf.columns else 0
                k1, k2 = st.columns(2)
                k1.metric("Registros", len(df_mf))
                k2.metric("Horas", f"{total_h:.1f}h")
                k1, k2 = st.columns(2)
                k1.metric("Volumen", f"{total_m3:.1f} m³")

                st.markdown("---")
                card_items = list(df_mf.iterrows())
                rows = [card_items[i:i+2] for i in range(0, len(card_items), 2)]
                for row_pair in rows:
                    left_col, right_col = st.columns(2)
                    for col_idx, (idx, row) in enumerate(row_pair):
                        current_col = left_col if col_idx == 0 else right_col
                        with current_col:
                            tipo = row.get("tipo_equipo", "")
                            placa = row.get("placa", "")
                            operador = row.get("operador", "")
                            h_inicio = row.get("hora_inicio", "")
                            h_fin = row.get("hora_fin", "")
                            horas = row.get("horas_trabajadas", 0)
                            preview = f"**{tipo}** {placa} — {operador} ({horas}h)"
                            with st.expander(preview):
                                c1, c2 = st.columns(2)
                                c1.text_input("Horario", value=f"{h_inicio} - {h_fin}", key=f"chat_maq_hora_{idx}", disabled=True)
                                c2.text_input("Material", value=str(row.get("material_transportado", "") or ""), key=f"chat_maq_mat_{idx}", disabled=True)
                                c3, c4 = st.columns(2)
                                c3.metric("m³", f"{row.get('volumen_m3', 0):.1f}")
                                c4.metric("Viajes", f"{row.get('numero_viajes', 0)}")
                                obs = row.get("observaciones", "")
                                if str(obs) and str(obs) != "nan":
                                    st.caption(f"📝 {obs}")

            col_b1, col_b2 = st.columns(2)
            with col_b2:
                if st.button("❌ Cerrar", use_container_width=True, key="btn_close_chat_maq"):
                    st.session_state.chat_mode = None
                    st.rerun()

    # ═══ MATERIALES ═══
    elif st.session_state.chat_mode == "materiales_tabla":
        df_mat = get_materiales(supabase, PA)
        if df_mat.empty:
            st.info("📭 No hay solicitudes de materiales")
        else:
            if "estado" in df_mat.columns:
                filtro_est = st.selectbox("Estado:", ["Todos"] + df_mat["estado"].dropna().unique().tolist(), key="chat_mat_estado")
                df_mf = df_mat.copy()
                if filtro_est != "Todos":
                    df_mf = df_mf[df_mf["estado"] == filtro_est]
            else:
                df_mf = df_mat.copy()

            if not df_mf.empty:
                st.markdown("---")
                card_items = list(df_mf.iterrows())
                rows = [card_items[i:i+2] for i in range(0, len(card_items), 2)]
                for row_pair in rows:
                    left_col, right_col = st.columns(2)
                    for col_idx, (idx, row) in enumerate(row_pair):
                        current_col = left_col if col_idx == 0 else right_col
                        with current_col:
                            estado = row.get("estado", "")
                            req = row.get("requerimiento", "")
                            fecha = row.get("fecha", "")
                            usuario_mat = row.get("usuario", "")
                            preview = f"{_badge_text(estado)} **{str(req)[:50]}{'...' if len(str(req))>50 else ''}**"
                            with st.expander(preview):
                                st.markdown(_badge(estado), unsafe_allow_html=True)
                                c1, c2 = st.columns(2)
                                c1.text_input("Fecha", value=str(fecha), key=f"chat_mat_fecha_{idx}", disabled=True)
                                c2.text_input("Usuario", value=str(usuario_mat), key=f"chat_mat_usr_{idx}", disabled=True)
                                new_estado = st.selectbox("Estado", ["Solicitado", "En proceso", "Entregado", "Cancelado"],
                                                          index=["Solicitado", "En proceso", "Entregado", "Cancelado"].index(estado) if estado in ["Solicitado", "En proceso", "Entregado", "Cancelado"] else 0,
                                                          key=f"chat_mat_est_{idx}")
                                if st.button("💾 Guardar", use_container_width=True, key=f"chat_mat_save_{idx}"):
                                    try:
                                        update_record(supabase, "materiales", "id", row["id"], {"estado": new_estado})
                                        st.success(f"✅ Estado actualizado a {new_estado}")
                                        st.cache_data.clear()
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"❌ Error: {e}")

            col_b1, col_b2 = st.columns(2)
            with col_b2:
                if st.button("❌ Cerrar", use_container_width=True, key="btn_close_chat_mat"):
                    st.session_state.chat_mode = None
                    st.rerun()

    # ═══ CHAT LIBRE ═══
    if st.session_state.chat_mode is None:
        st.divider()
        with st.expander("💬 Historial", expanded=False):
            for msg in st.session_state.chat_historial.get(PA, []):
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])

        if prompt := st.chat_input("Escribe un comando o mensaje..."):
            st.session_state.chat_historial[PA].append({"role": "user", "content": prompt})
            respuesta = procesar_mensaje(prompt, PA, usuario, supabase)
            st.session_state.chat_historial[PA].append({"role": "assistant", "content": respuesta})
            st.rerun()