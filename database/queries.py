# database/queries.py
import streamlit as st
import pandas as pd
from supabase import Client
from datetime import date, datetime
from typing import List, Dict, Optional, Any
from utils.formatting import parsear_moneda

# ═══════════════════════════════════════════════════════════
# READ OPERATIONS
# Note: In DEMO mode, caching is disabled because data lives in session_state
# and changes need to be reflected immediately.
# ═══════════════════════════════════════════════════════════

def get_config(_supabase, _ttl=300):
    response = _supabase.table("config").select("*").limit(1).execute()
    if response.data:
        return {k.lower().replace(" ", "_"): v for k, v in response.data[0].items()}
    return {}

def get_actividades(_supabase):
    response = _supabase.table("actividades").select("*").execute()
    if response.data:
        df = pd.DataFrame(response.data)
        for col in ["valor_unitario", "cantidad_total", "valor_total"]:
            if col in df.columns:
                df[col] = df[col].apply(lambda x: parsear_moneda(x) if pd.notna(x) else 0)
        return df
    return pd.DataFrame()

def get_trabajadores(_supabase):
    response = _supabase.table("trabajadores").select("*").eq("activo", True).execute()
    return response.data if response.data else []

def get_avances(_supabase, proyecto: str, fecha: date = None):
    query = _supabase.table("avances").select("*").eq("proyecto", proyecto)
    if fecha:
        query = query.eq("fecha", fecha.isoformat())
    response = query.execute()
    return pd.DataFrame(response.data) if response.data else pd.DataFrame()

def get_materiales(_supabase, proyecto: str):
    response = _supabase.table("materiales").select("*").eq("proyecto", proyecto).execute()
    return pd.DataFrame(response.data) if response.data else pd.DataFrame()

def get_asistencia(_supabase, proyecto: str, fecha: date = None):
    query = _supabase.table("asistencia").select("*").eq("proyecto", proyecto)
    if fecha:
        query = query.eq("fecha", fecha.isoformat())
    response = query.execute()
    return pd.DataFrame(response.data) if response.data else pd.DataFrame()

def get_nomina(_supabase, proyecto: str):
    response = _supabase.table("nomina").select("*").eq("proyecto", proyecto).execute()
    return pd.DataFrame(response.data) if response.data else pd.DataFrame()

def get_tareas(_supabase, proyecto: str = None):
    query = _supabase.table("tareas").select("*")
    if proyecto:
        query = query.eq("proyecto", proyecto)
    response = query.execute()
    return pd.DataFrame(response.data) if response.data else pd.DataFrame()

def get_proveedores(_supabase):
    response = _supabase.table("proveedores").select("*").execute()
    return pd.DataFrame(response.data) if response.data else pd.DataFrame()

# ═══════════════════════════════════════════════════════════
# WRITE OPERATIONS
# ═══════════════════════════════════════════════════════════

def insert_avance(_supabase, data: Dict[str, Any]):
    data["timestamp"] = datetime.now().isoformat()
    response = _supabase.table("avances").insert(data).execute()
    return response.data[0] if response.data else None

def insert_avances_bulk(_supabase, rows: List[Dict[str, Any]]):
    for row in rows:
        row["timestamp"] = datetime.now().isoformat()
    response = _supabase.table("avances").insert(rows).execute()
    return response.data or []

def replace_asistencia_dia(_supabase, proyecto: str, fecha: date, nuevas_filas: List[Dict[str, Any]]):
    _supabase.table("asistencia").delete().eq("proyecto", proyecto).eq("fecha", fecha.isoformat()).execute()
    for row in nuevas_filas:
        row["timestamp"] = datetime.now().isoformat()
    response = _supabase.table("asistencia").insert(nuevas_filas).execute()
    return response.data is not None

def update_tarea_estado(_supabase, id_tarea: str, nuevo_estado: str, notas: str = None):
    update_data = {"estado": nuevo_estado}
    if notas is not None:
        update_data["notas"] = notas
    response = _supabase.table("tareas").update(update_data).eq("id_tarea", id_tarea).execute()
    return response.data is not None

# ═══════════════════════════════════════════════════════════
# UTILITIES
# ═══════════════════════════════════════════════════════════

def generar_id_tarea(_supabase, proyecto: str):
    response = _supabase.table("tareas").select("id_tarea").eq("proyecto", proyecto).execute()
    if not response.data:
        return "T-001"
    import re
    numeros = []
    for item in response.data:
        match = re.search(r'(\d+)', item["id_tarea"])
        if match:
            numeros.append(int(match.group(1)))
    siguiente = max(numeros) + 1 if numeros else 1
    return f"T-{siguiente:03d}"

# ═══════════════════════════════════════════════════════════
# GENERIC CRUD
# ═══════════════════════════════════════════════════════════

def insert_record(_supabase, table: str, data: Dict[str, Any]):
    response = _supabase.table(table).insert(data).execute()
    return response.data[0] if response.data else None

def update_record(_supabase, table: str, id_column: str, id_value: Any, data: Dict[str, Any]):
    response = _supabase.table(table).update(data).eq(id_column, id_value).execute()
    return response.data is not None

def delete_record(_supabase, table: str, id_column: str, id_value: Any):
    response = _supabase.table(table).delete().eq(id_column, id_value).execute()
    return response.data is not None

def insert_tarea(_supabase, data: Dict[str, Any]):
    data["timestamp"] = datetime.now().isoformat()
    response = _supabase.table("tareas").insert(data).execute()
    return response.data[0] if response.data else None

def insertproveedor(_supabase, data: Dict[str, Any]):
    response = _supabase.table("proveedores").insert(data).execute()
    return response.data[0] if response.data else None

def insert_control_inventario(_supabase, data: Dict[str, Any]):
    data["timestamp"] = datetime.now().isoformat()
    response = _supabase.table("control_inventario").insert(data).execute()
    return response.data[0] if response.data else None

def insert_control_maquinas(_supabase, data: Dict[str, Any]):
    data["timestamp"] = datetime.now().isoformat()
    response = _supabase.table("control_maquinas").insert(data).execute()
    return response.data[0] if response.data else None