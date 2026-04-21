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
from utils.seed_data import render_seed_button, seed_inventario, seed_proveedores_data, seed_maquinas_data, seed_tareas_data, seed_actividades_data, seed_avances_data, seed_asistencia_data, seed_nomina_data, seed_materiales_data
from modules.dashboard import calcular_avances

MATERIALES_RAPIDOS = [
    ("🧱 Cemento", "Cemento", "bultos"),
    ("🏔️ Arena", "Arena", "m3"),
    ("🪨 Grava", "Grava", "m3"),
    ("🔩 Varilla", "Varilla", "varillas"),
    ("🧱 Ladrillo", "Ladrillo", "und"),
    ("💧 Piedra", "Piedra", "m3"),
]

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
            if not df_act.empty and id_item in df_act["id"].values:
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
    <div style="background:#075e54;padding:18px 28px;border-radius:12px;margin-bottom:24px;display:flex;align-items:center;gap:16px">
        <div style="background:#dfe5e7;border-radius:50%;width:50px;height:50px;display:flex;align-items:center;justify-content:center;font-size:24px">💬</div>
        <div>
            <div style="color:#fff;font-size:20px;font-weight:700">Chat de Obra</div>
            <div style="color:#b2dfdb;font-size:13px">{PA}  •  {usuario}</div>
        </div>
    </div>
    ''', unsafe_allow_html=True)

    # ═══ ACCESOS RÁPIDOS (role-based) ═══
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
    ncols = min(len(botones), 4)
    if ncols > 0:
        rows = [botones[i:i+ncols] for i in range(0, len(botones), ncols)]
        for row in rows:
            cols = st.columns(ncols)
            for idx, (label, mode) in enumerate(row):
                with cols[idx]:
                    if st.button(label, use_container_width=True, key=f"btn_chat_{mode}"):
                        st.session_state.chat_mode = mode
                        st.rerun()

    # ═══ TABLA DE AVANCES ═══
    if st.session_state.chat_mode == "avances_tabla":
        st.info("💡 Escriba la cantidad en la columna **➕ Nuevo Avance** y presione **💾 Guardar Avances**")

        df_act = get_actividades(supabase)
        df_av = get_avances(supabase, PA)
        df_ca = calcular_avances(df_act, df_av)

        if df_ca.empty:
            st.warning("⚠️ No hay actividades cargadas")
        else:
            col_f1, col_f2, col_f3 = st.columns(3)
            with col_f1:
                componentes = df_ca["componente"].unique().tolist() if "componente" in df_ca.columns else []
                filtro_comp = st.multiselect("Componente:", componentes, key="chat_av_comp")
            with col_f2:
                capitulos = df_ca["capitulo"].unique().tolist() if "capitulo" in df_ca.columns else []
                filtro_cap = st.multiselect("Capítulo:", capitulos, key="chat_av_cap")
            with col_f3:
                buscar_av = st.text_input("Buscar actividad:", key="chat_av_buscar")

            df_f = df_ca.copy()
            if filtro_comp and "componente" in df_f.columns:
                df_f = df_f[df_f["componente"].isin(filtro_comp)]
            if filtro_cap and "capitulo" in df_f.columns:
                df_f = df_f[df_f["capitulo"].isin(filtro_cap)]
            if buscar_av and "descripcion" in df_f.columns:
                df_f = df_f[df_f["descripcion"].str.contains(buscar_av, case=False, na=False)]

            if not df_f.empty:
                total_ejec = df_f["valor_ejecutado"].sum() if "valor_ejecutada" in df_f.columns else 0
                total_val = df_f["valor_total"].sum() if "valor_total" in df_f.columns else 0
                pct = round(df_f["pct_avance"].mean(), 1) if "pct_avance" in df_f.columns else 0
                k1, k2, k3 = st.columns(3)
                k1.metric("Actividades", len(df_f))
                k2.metric("% Avance Prom.", f"{pct}%")
                k3.metric("$ Ejecutado", fmt_cop(df_f["valor_ejecutado"].sum() if "valor_ejecutado" in df_f.columns else 0))

                df_tabla = df_f.copy()
                df_tabla["nuevo_avance"] = 0.0

                cols = [c for c in ["id", "capitulo", "componente", "descripcion", "unidad", "cantidad_total", "cantidad_ejecutada", "pct_avance", "nuevo_avance"] if c in df_tabla.columns]
                config = {
                    "id": st.column_config.TextColumn("ID", disabled=True, width="small"),
                    "capitulo": st.column_config.TextColumn("Cap.", disabled=True, width="small"),
                    "componente": st.column_config.TextColumn("Componente", disabled=True, width="medium"),
                    "descripcion": st.column_config.TextColumn("Descripción", disabled=True, width="large"),
                    "unidad": st.column_config.TextColumn("Und", disabled=True, width="small"),
                    "cantidad_total": st.column_config.NumberColumn("Cant. Total", disabled=True, format="%.2f"),
                    "cantidad_ejecutada": st.column_config.NumberColumn("Cant. Ejec.", disabled=True, format="%.2f"),
                    "pct_avance": st.column_config.NumberColumn("% Avance", disabled=True, format="%.1f %%"),
                    "nuevo_avance": st.column_config.NumberColumn("➕ Nuevo Avance", format="%.2f", step=0.5),
                }
                config_f = {k: v for k, v in config.items() if k in cols}

                df_edit = st.data_editor(df_tabla[cols], column_config=config_f, hide_index=True, use_container_width=True, key="editor_chat_avances")

                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    if st.button("💾 Guardar Avances", type="primary", use_container_width=True, key="btn_save_chat_av"):
                        cambios = 0
                        for idx, row in df_edit.iterrows():
                            nuevo = row.get("nuevo_avance", 0)
                            if nuevo and float(nuevo) > 0 and "id" in row:
                                data = {
                                    "proyecto": PA,
                                    "fecha": datetime.date.today().isoformat(),
                                    "id_item": str(row["id"]),
                                    "cantidad": float(nuevo),
                                    "usuario": usuario
                                }
                                try:
                                    insert_avance(supabase, data)
                                    cambios += 1
                                except Exception:
                                    pass
                        if cambios > 0:
                            msg = f"✅ {cambios} avance(s) registrado(s)"
                            st.session_state.chat_historial[PA].append({"role": "user", "content": f"Registré {cambios} avance(s)"})
                            st.session_state.chat_historial[PA].append({"role": "assistant", "content": msg})
                            st.success(msg)
                            st.cache_data.clear()
                            st.rerun()
                        else:
                            st.info("ℹ️ No se encontraron avances nuevos. Ingrese valores en la columna ➕ Nuevo Avance")
                with col_btn2:
                    if st.button("❌ Cerrar", use_container_width=True, key="btn_close_chat_av"):
                        st.session_state.chat_mode = None
                        st.rerun()

    # ═══ TABLA DE INVENTARIO ═══
    elif st.session_state.chat_mode == "inventario_tabla":
        response = supabase.table("control_inventario").select("*").eq("proyecto", PA).execute()

        if not response.data:
            st.info("📭 No hay movimientos registrados")
        else:
            df = pd.DataFrame(response.data)
            col_f1, col_f2, col_f3 = st.columns(3)
            with col_f1:
                filtro_tipo = st.selectbox("Tipo:", ["Todos", "Entrada", "Salida"], key="chat_inv_tipo")
            with col_f2:
                materiales_lista = ["Todos"] + sorted(df["material"].dropna().unique().tolist()) if "material" in df.columns else ["Todos"]
                filtro_material = st.selectbox("Material:", materiales_lista, key="chat_inv_mat")
            with col_f3:
                filtro_fecha = st.date_input("Fecha:", value=None, key="chat_inv_fecha")

            df_f = df.copy()
            if filtro_tipo != "Todos" and "tipo_movimiento" in df_f.columns:
                df_f = df_f[df_f["tipo_movimiento"] == filtro_tipo]
            if filtro_material != "Todos" and "material" in df_f.columns:
                df_f = df_f[df_f["material"] == filtro_material]
            if filtro_fecha and "fecha" in df_f.columns:
                df_f = df_f[df_f["fecha"] == filtro_fecha.isoformat()]

            if not df_f.empty:
                ent = len(df_f[df_f["tipo_movimiento"] == "Entrada"]) if "tipo_movimiento" in df_f.columns else 0
                sal = len(df_f[df_f["tipo_movimiento"] == "Salida"]) if "tipo_movimiento" in df_f.columns else 0
                k1, k2, k3 = st.columns(3)
                k1.metric("Total", len(df_f))
                k2.metric("Entradas", ent)
                k3.metric("Salidas", sal)

                cols_inv = [c for c in ["id", "fecha", "tipo_movimiento", "material", "cantidad", "unidad", "responsable", "observaciones"] if c in df_f.columns]
                config_inv = {
                    "id": st.column_config.TextColumn("ID", disabled=True),
                    "fecha": st.column_config.TextColumn("Fecha", disabled=True),
                    "tipo_movimiento": st.column_config.TextColumn("Tipo", disabled=True),
                    "material": st.column_config.TextColumn("Material", width="medium"),
                    "cantidad": st.column_config.NumberColumn("Cantidad", step=0.1),
                    "unidad": st.column_config.SelectboxColumn("Unidad", options=["bultos", "m3", "kg", "ton", "und", "varillas", "pies2", "galones"]),
                    "responsable": st.column_config.TextColumn("Responsable", width="medium"),
                    "observaciones": st.column_config.TextColumn("Obs.", width="large"),
                }
                config_f = {k: v for k, v in config_inv.items() if k in cols_inv}
                df_edit = st.data_editor(df_f.sort_values(["fecha", "hora"] if "hora" in df_f.columns else ["fecha"], ascending=False)[cols_inv], column_config=config_f, hide_index=True, use_container_width=True, key="editor_chat_inv")

                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    if st.button("💾 Guardar Cambios", type="primary", use_container_width=True, key="btn_save_chat_inv"):
                        cambios = 0
                        df_orig = df_f.sort_values(["fecha", "hora"] if "hora" in df_f.columns else ["fecha"], ascending=False)[cols_inv]
                        for idx, row in df_edit.iterrows():
                            orig = df_orig.loc[idx]
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
                    if st.button("❌ Cerrar", use_container_width=True, key="btn_close_chat_inv"):
                        st.session_state.chat_mode = None
                        st.rerun()

    # ═══ TABLA DE ASISTENCIA ═══
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
                k1, k2, k3 = st.columns(3)
                k1.metric("Presentes", pres)
                k2.metric("Ausentes", aus)
                k3.metric("Permisos", perm)

            if not df_ast.empty:
                cols_ast = [c for c in ["id", "fecha", "trabajador", "cargo", "estado"] if c in df_ast.columns]
                config_ast = {
                    "id": st.column_config.TextColumn("ID", disabled=True),
                    "fecha": st.column_config.TextColumn("Fecha", disabled=True),
                    "trabajador": st.column_config.TextColumn("Trabajador", width="medium"),
                    "cargo": st.column_config.TextColumn("Cargo", width="medium"),
                    "estado": st.column_config.SelectboxColumn("Estado", options=["Presente", "Ausente", "Permiso", "Vacaciones"]),
                }
                config_f = {k: v for k, v in config_ast.items() if k in cols_ast}
                df_edit = st.data_editor(df_ast[cols_ast], column_config=config_ast if all(k in cols_ast for k in config_ast) else {k: v for k, v in config_ast.items() if k in cols_ast}, hide_index=True, use_container_width=True, key="editor_chat_ast")

                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    if st.button("💾 Guardar Cambios", type="primary", use_container_width=True, key="btn_save_chat_ast"):
                        cambios = 0
                        df_orig = df_ast[cols_ast]
                        for idx, row in df_edit.iterrows():
                            orig = df_orig.loc[idx]
                            if "id" in row and not row.equals(orig):
                                update_data = {}
                                for col in cols_ast:
                                    if col not in ["id", "fecha"] and col in row.index and row[col] != orig.get(col):
                                        update_data[col] = row[col]
                                if update_data:
                                    try:
                                        update_record(supabase, "asistencia", "id", row["id"], update_data)
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
                    if st.button("❌ Cerrar", use_container_width=True, key="btn_close_chat_ast"):
                        st.session_state.chat_mode = None
                        st.rerun()

    # ═══ TABLA DE TAREAS ═══
    elif st.session_state.chat_mode == "tareas_tabla":
        df_tareas = get_tareas(supabase, PA)

        if df_tareas.empty:
            st.info("📭 No hay tareas registradas")
        else:
            col_f1, col_f2, col_f3 = st.columns(3)
            with col_f1:
                filtro_estado = st.selectbox("Estado:", ["Todos", "Pendiente", "En progreso", "Completada"], key="chat_tar_est")
            with col_f2:
                filtro_prioridad = st.selectbox("Prioridad:", ["Todas", "Alta", "Media", "Baja"], key="chat_tar_pri")
            with col_f3:
                filtro_buscar = st.text_input("Buscar:", key="chat_tar_buscar")

            df_f = df_tareas.copy()
            if filtro_estado != "Todos" and "estado" in df_f.columns:
                df_f = df_f[df_f["estado"] == filtro_estado]
            if filtro_prioridad != "Todas" and "prioridad" in df_f.columns:
                df_f = df_f[df_f["prioridad"] == filtro_prioridad]
            if filtro_buscar and "descripcion" in df_f.columns:
                df_f = df_f[df_f["descripcion"].str.contains(filtro_buscar, case=False, na=False)]

            if not df_f.empty:
                cols = [c for c in ["id_tarea", "descripcion", "fecha_limite", "prioridad", "estado", "asignado_a", "notas"] if c in df_f.columns]
                config = {
                    "id_tarea": st.column_config.TextColumn("ID", disabled=True, width="small"),
                    "descripcion": st.column_config.TextColumn("Descripción", width="large"),
                    "fecha_limite": st.column_config.TextColumn("Fecha Límite", disabled=True, width="small"),
                    "prioridad": st.column_config.SelectboxColumn("Prioridad", options=["Alta", "Media", "Baja"]),
                    "estado": st.column_config.SelectboxColumn("Estado", options=["Pendiente", "En progreso", "Completada"]),
                    "asignado_a": st.column_config.TextColumn("Asignado", width="medium"),
                    "notas": st.column_config.TextColumn("Notas", width="medium"),
                }
                config_f = {k: v for k, v in config.items() if k in cols}
                df_edit = st.data_editor(df_f[cols], column_config=config_f, hide_index=True, use_container_width=True, key="editor_chat_tar")

                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    if st.button("💾 Guardar Cambios", type="primary", use_container_width=True, key="btn_save_chat_tar"):
                        cambios = 0
                        for idx, row in df_edit.iterrows():
                            if "id_tarea" in row and "estado" in row:
                                try:
                                    update_tarea_estado(supabase, row["id_tarea"], row["estado"], row.get("notas", ""))
                                    cambios += 1
                                except Exception:
                                    pass
                        if cambios > 0:
                            st.success(f"✅ {cambios} tarea(s) actualizada(s)")
                            st.cache_data.clear()
                            st.rerun()
                        else:
                            st.info("ℹ️ No se detectaron cambios")
                with col_btn2:
                    if st.button("❌ Cerrar", use_container_width=True, key="btn_close_chat_tar"):
                        st.session_state.chat_mode = None
                        st.rerun()

    # ═══ TABLA DE NÓMINA ═══
    elif st.session_state.chat_mode == "nomina_tabla":
        dfn = get_nomina(supabase, PA)

        if dfn.empty:
            st.info("📭 Sin movimientos de nómina")
        else:
            col_f1, col_f2 = st.columns(2)
            with col_f1:
                filtro_tipo = st.selectbox("Tipo:", ["Todos"] + dfn["tipo"].unique().tolist() if "tipo" in dfn.columns else ["Todos"], key="chat_nom_tipo")
            with col_f2:
                filtro_buscar = st.text_input("Buscar:", key="chat_nom_buscar")

            df_nf = dfn.copy()
            if filtro_tipo != "Todos" and "tipo" in df_nf.columns:
                df_nf = df_nf[df_nf["tipo"] == filtro_tipo]
            if filtro_buscar and "trabajador" in df_nf.columns:
                df_nf = df_nf[df_nf["trabajador"].str.contains(filtro_buscar, case=False, na=False)]

            if not df_nf.empty and "tipo" in df_nf.columns and "valor" in df_nf.columns:
                ing = df_nf[df_nf["tipo"].isin(["Mensual", "Quincenal", "Jornal diario", "Bonificacion"])]["valor"].sum()
                pre = df_nf[df_nf["tipo"].isin(["Prestamo", "Anticipo"])]["valor"].sum()
                ded = df_nf[df_nf["tipo"] == "Deduccion"]["valor"].sum() if "Deduccion" in df_nf["tipo"].values else 0
                k1, k2, k3 = st.columns(3)
                k1.metric("Pago Bruto", fmt_cop(ing))
                k2.metric("Préstamos", fmt_cop(pre))
                k3.metric("Deducciones", fmt_cop(ded))

            if not df_nf.empty:
                cols_nom = [c for c in ["id", "fecha", "trabajador", "tipo", "valor", "notas"] if c in df_nf.columns]
                config_nom = {
                    "id": st.column_config.TextColumn("ID", disabled=True),
                    "fecha": st.column_config.TextColumn("Fecha", disabled=True),
                    "trabajador": st.column_config.TextColumn("Trabajador", width="medium"),
                    "tipo": st.column_config.SelectboxColumn("Tipo", options=["Mensual", "Quincenal", "Jornal diario", "Bonificacion", "Prestamo", "Anticipo", "Deduccion"]),
                    "valor": st.column_config.NumberColumn("Valor", format="$ %,.0f", step=1000),
                    "notas": st.column_config.TextColumn("Notas", width="medium"),
                }
                config_f = {k: v for k, v in config_nom.items() if k in cols_nom}
                df_edit = st.data_editor(df_nf[cols_nom].sort_values("fecha", ascending=False) if "fecha" in df_nf.columns else df_nf[cols_nom], column_config=config_f, hide_index=True, use_container_width=True, key="editor_chat_nom")

                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    if st.button("💾 Guardar Cambios", type="primary", use_container_width=True, key="btn_save_chat_nom"):
                        cambios = 0
                        df_orig = df_nf[cols_nom].sort_values("fecha", ascending=False) if "fecha" in df_nf.columns else df_nf[cols_nom]
                        for idx, row in df_edit.iterrows():
                            orig = df_orig.loc[idx]
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
                    if st.button("❌ Cerrar", use_container_width=True, key="btn_close_chat_nom"):
                        st.session_state.chat_mode = None
                        st.rerun()

    # ═══ TABLA DE PROVEEDORES ═══
    elif st.session_state.chat_mode == "proveedores_tabla":
        response = supabase.table("proveedores").select("*").execute()

        if not response.data:
            st.info("📭 No hay proveedores registrados")
        else:
            df_prov = pd.DataFrame(response.data)
            col_f1, col_f2 = st.columns(2)
            with col_f1:
                categorias = ["Todas"] + sorted(df_prov["categoria"].dropna().unique().tolist()) if "categoria" in df_prov.columns else ["Todas"]
                cat_sel = st.selectbox("Categoría:", categorias, key="chat_prov_cat")
            with col_f2:
                buscar_prov = st.text_input("Buscar:", key="chat_prov_buscar")

            df_pf = df_prov.copy()
            if cat_sel != "Todas" and "categoria" in df_pf.columns:
                df_pf = df_pf[df_pf["categoria"] == cat_sel]
            if buscar_prov and "nombre" in df_pf.columns:
                df_pf = df_pf[df_pf["nombre"].str.contains(buscar_prov, case=False, na=False)]

            if not df_pf.empty:
                cols_prov = [c for c in ["id", "nit", "nombre", "contacto", "telefono", "categoria", "direccion", "notas"] if c in df_pf.columns]
                config_prov = {
                    "id": st.column_config.TextColumn("ID", disabled=True),
                    "nit": st.column_config.TextColumn("NIT", width="small"),
                    "nombre": st.column_config.TextColumn("Nombre", width="medium"),
                    "contacto": st.column_config.TextColumn("Contacto", width="medium"),
                    "telefono": st.column_config.TextColumn("Teléfono", width="small"),
                    "categoria": st.column_config.SelectboxColumn("Categoría", options=["Materiales", "Equipos", "Transporte", "Mano de obra", "Servicios", "Ferretería", "Concreto", "Acero", "Otro"]),
                    "direccion": st.column_config.TextColumn("Dirección", width="medium"),
                    "notas": st.column_config.TextColumn("Notas", width="large"),
                }
                config_f = {k: v for k, v in config_prov.items() if k in cols_prov}
                df_edit = st.data_editor(df_pf[cols_prov], column_config=config_f, hide_index=True, use_container_width=True, key="editor_chat_prov")

                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    if st.button("💾 Guardar Cambios", type="primary", use_container_width=True, key="btn_save_chat_prov"):
                        cambios = 0
                        df_orig = df_pf[cols_prov]
                        for idx, row in df_edit.iterrows():
                            orig = df_orig.loc[idx]
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
                    if st.button("❌ Cerrar", use_container_width=True, key="btn_close_chat_prov"):
                        st.session_state.chat_mode = None
                        st.rerun()

    # ═══ TABLA DE MÁQUINAS ═══
    elif st.session_state.chat_mode == "maquinas_tabla":
        fecha_default = datetime.date.today()
        filtro_fecha_maq = st.date_input("Fecha:", value=fecha_default, key="chat_maq_fecha")
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
                k1, k2, k3 = st.columns(3)
                k1.metric("Registros", len(df_mf))
                k2.metric("Horas", f"{total_h:.1f}h")
                k3.metric("Volumen", f"{total_m3:.1f} m³")

                cols_maq = [c for c in ["id", "hora_inicio", "hora_fin", "tipo_equipo", "placa", "operador", "horas_trabajadas", "material_transportado", "volumen_m3", "numero_viajes", "observaciones"] if c in df_mf.columns]
                config_maq = {
                    "id": st.column_config.TextColumn("ID", disabled=True),
                    "hora_inicio": st.column_config.TextColumn("H. Inicio", disabled=True, width="small"),
                    "hora_fin": st.column_config.TextColumn("H. Fin", disabled=True, width="small"),
                    "tipo_equipo": st.column_config.SelectboxColumn("Tipo", options=["Volqueta", "Retroexcavadora", "Mototrac", "Grúa", "Compactador", "Mixer", "Otro"]),
                    "placa": st.column_config.TextColumn("Placa", width="small"),
                    "operador": st.column_config.TextColumn("Operador", width="medium"),
                    "horas_trabajadas": st.column_config.NumberColumn("Horas", step=0.5, format="%.1f"),
                    "material_transportado": st.column_config.TextColumn("Material", width="medium"),
                    "volumen_m3": st.column_config.NumberColumn("m³", step=0.5, format="%.1f"),
                    "numero_viajes": st.column_config.NumberColumn("Viajes", step=1),
                    "observaciones": st.column_config.TextColumn("Obs.", width="medium"),
                }
                config_f = {k: v for k, v in config_maq.items() if k in cols_maq}
                df_edit = st.data_editor(df_mf.sort_values("hora_inicio")[cols_maq] if "hora_inicio" in df_mf.columns else df_mf[cols_maq], column_config=config_f, hide_index=True, use_container_width=True, key="editor_chat_maq")

                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    if st.button("💾 Guardar Cambios", type="primary", use_container_width=True, key="btn_save_chat_maq"):
                        cambios = 0
                        df_orig = df_mf.sort_values("hora_inicio")[cols_maq] if "hora_inicio" in df_mf.columns else df_mf[cols_maq]
                        for idx, row in df_edit.iterrows():
                            orig = df_orig.loc[idx]
                            if "id" in row and not row.equals(orig):
                                update_data = {}
                                for col in cols_maq:
                                    if col not in ["id", "hora_inicio", "hora_fin"] and col in row.index and row[col] != orig.get(col):
                                        update_data[col] = row[col]
                                if update_data:
                                    try:
                                        update_record(supabase, "control_maquinas", "id", row["id"], update_data)
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
                    if st.button("❌ Cerrar", use_container_width=True, key="btn_close_chat_maq"):
                        st.session_state.chat_mode = None
                        st.rerun()

    # ═══ TABLA DE MATERIALES (Solicitudes) ═══
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

            cols_mat = [c for c in ["id", "fecha", "requerimiento", "estado", "usuario"] if c in df_mf.columns]
            config_mat = {
                "id": st.column_config.TextColumn("ID", disabled=True),
                "fecha": st.column_config.TextColumn("Fecha", disabled=True),
                "requerimiento": st.column_config.TextColumn("Requerimiento", width="large"),
                "estado": st.column_config.SelectboxColumn("Estado", options=["Solicitado", "En proceso", "Entregado", "Cancelado"]),
                "usuario": st.column_config.TextColumn("Usuario", disabled=True),
            }
            config_f = {k: v for k, v in config_mat.items() if k in cols_mat}
            if not df_mf.empty:
                df_edit = st.data_editor(df_mf[cols_mat], column_config=config_f, hide_index=True, use_container_width=True, key="editor_chat_mat")

                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    if st.button("💾 Guardar Cambios", type="primary", use_container_width=True, key="btn_save_chat_mat"):
                        cambios = 0
                        df_orig = df_mf[cols_mat]
                        for idx, row in df_edit.iterrows():
                            orig = df_orig.loc[idx]
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

    def seed_all_chat(supabase, proyecto):
        total = 0
        total += seed_actividades_data(supabase)
        total += seed_avances_data(supabase, proyecto)
        total += seed_inventario(supabase, proyecto)
        total += seed_proveedores_data(supabase)
        total += seed_maquinas_data(supabase, proyecto)
        total += seed_tareas_data(supabase, proyecto)
        total += seed_asistencia_data(supabase, proyecto)
        total += seed_nomina_data(supabase, proyecto)
        total += seed_materiales_data(supabase, proyecto)
        return total

    render_seed_button(supabase, PA, "Todos los Datos", seed_all_chat, key_prefix="chat")