import streamlit as st
from database.supabase_client import get_supabase
from datetime import datetime

st.set_page_config(page_title="Datos de Prueba", page_icon="🧪", layout="wide")

if "usuario_actual" not in st.session_state or st.session_state.usuario_actual is None:
    st.warning("⚠️ Debes iniciar sesión primero")
    st.switch_page("main.py")

PROYECTO = st.session_state.get("nombre_proyecto", "Edificio Colombo Americana")

st.markdown(f'''
<div style="background:#e65100;padding:18px 28px;border-radius:12px;margin-bottom:24px;display:flex;align-items:center;gap:16px">
    <span style="font-size:32px">🧪</span>
    <div>
        <div style="color:#fff;font-size:20px;font-weight:700">Datos de Prueba — Demo</div>
        <div style="color:#ffcc80;font-size:13px">Proyecto: {PROYECTO}</div>
    </div>
</div>
<div style="background:linear-gradient(90deg,#C9A227,#E8D48B,#C9A227);color:#fff;padding:10px;border-radius:6px;text-align:center;font-weight:700;margin-bottom:20px">
    🧪 MODO DEMO — Los datos se almacenan en la sesión actual
</div>
''', unsafe_allow_html=True)

st.info("💡 Los datos ya están precargados automáticamente. Usa los botones abajo para reiniciar o limpiar.")

supabase = get_supabase()

with st.expander("🔍 Estado actual de las tablas (en memoria)", expanded=True):
    tables_check = [
        ("config", None),
        ("actividades", None),
        ("avances", "proyecto"),
        ("tareas", "proyecto"),
        ("control_inventario", "proyecto"),
        ("control_maquinas", "proyecto"),
        ("asistencia", "proyecto"),
        ("nomina", "proyecto"),
        ("materiales", "proyecto"),
        ("proveedores", None),
        ("trabajadores", None),
        ("usuarios", None),
    ]
    for table, filter_col in tables_check:
        try:
            if filter_col and PROYECTO:
                resp = supabase.table(table).select("*").eq(filter_col, PROYECTO).execute()
            else:
                resp = supabase.table(table).select("*").execute()
            total = len(resp.data) if resp.data else 0
            label = f"filtrado por proyecto" if filter_col else "sin filtro"
            st.write(f"✅ `{table}`: **{total}** registros ({label})")
        except Exception as e:
            st.write(f"❌ `{table}`: Error - {str(e)[:80]}")

st.divider()

st.markdown("### 🔄 Reiniciar Datos de Prueba")
st.write("Esto limpiará los datos en memoria y los volverá a cargar desde cero.")

if st.button("🔄 Reiniciar Todos los Datos", type="primary", use_container_width=True):
    keys_to_remove = [k for k in st.session_state._demo_db.keys()]
    for k in keys_to_remove:
        del st.session_state._demo_db[k]
    st.cache_data.clear()
    st.success("✅ Datos reiniciados. Los datos se recargarán automáticamente al navegar.")
    st.rerun()

st.divider()

st.markdown("### 🗑️ Limpiar Todos los Datos")
st.warning("⚠️ Esto eliminará TODOS los datos en memoria. Las tablas estarán vacías hasta que reinicies.")

if st.button("🗑️ Limpiar Todos los Datos", type="secondary", use_container_width=True):
    st.session_state._demo_db = {}
    st.success("🗑️ Datos eliminados. Haz clic en 🔄 Recargar en el sidebar o navega a otra página para que se regeneren.")
    st.cache_data.clear()
    st.rerun()