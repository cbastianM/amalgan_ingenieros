# utils/seed_data.py
import streamlit as st
import random
from datetime import date, timedelta, datetime

def seed_inventario(supabase, proyecto, usuario="director1"):
    inserted = 0
    movimientos = [
        {"proyecto": proyecto, "fecha": (date.today() - timedelta(days=5)).isoformat(), "hora": "07:30:00", "tipo_movimiento": "Entrada", "material": "Cemento", "cantidad": 200, "unidad": "bultos", "responsable": "Carlos Ramírez", "observaciones": "Entrega Cementos Argos", "usuario": usuario},
        {"proyecto": proyecto, "fecha": (date.today() - timedelta(days=5)).isoformat(), "hora": "08:15:00", "tipo_movimiento": "Entrada", "material": "Arena", "cantidad": 15, "unidad": "m3", "responsable": "Carlos Ramírez", "observaciones": "Volqueta 3 cargas", "usuario": usuario},
        {"proyecto": proyecto, "fecha": (date.today() - timedelta(days=4)).isoformat(), "hora": "07:45:00", "tipo_movimiento": "Entrada", "material": "Varilla", "cantidad": 500, "unidad": "varillas", "responsable": "José Martínez", "observaciones": "Varilla 1/2 y 3/8", "usuario": usuario},
        {"proyecto": proyecto, "fecha": (date.today() - timedelta(days=4)).isoformat(), "hora": "09:00:00", "tipo_movimiento": "Entrada", "material": "Grava", "cantidad": 12, "unidad": "m3", "responsable": "José Martínez", "observaciones": "", "usuario": usuario},
        {"proyecto": proyecto, "fecha": (date.today() - timedelta(days=3)).isoformat(), "hora": "10:30:00", "tipo_movimiento": "Salida", "material": "Cemento", "cantidad": 80, "unidad": "bultos", "responsable": "Miguel Torres", "observaciones": "Para viga Piso 4", "usuario": usuario},
        {"proyecto": proyecto, "fecha": (date.today() - timedelta(days=3)).isoformat(), "hora": "11:00:00", "tipo_movimiento": "Salida", "material": "Arena", "cantidad": 5, "unidad": "m3", "responsable": "Miguel Torres", "observaciones": "Para mezcla columnas", "usuario": usuario},
        {"proyecto": proyecto, "fecha": (date.today() - timedelta(days=2)).isoformat(), "hora": "07:20:00", "tipo_movimiento": "Entrada", "material": "Ladrillo", "cantidad": 5000, "unidad": "und", "responsable": "Carlos Ramírez", "observaciones": "Bloque cerámico 10cm", "usuario": usuario},
        {"proyecto": proyecto, "fecha": (date.today() - timedelta(days=2)).isoformat(), "hora": "14:00:00", "tipo_movimiento": "Salida", "material": "Cemento", "cantidad": 50, "unidad": "bultos", "responsable": "Pedro Gómez", "observaciones": "Para muros Piso 3", "usuario": usuario},
        {"proyecto": proyecto, "fecha": (date.today() - timedelta(days=1)).isoformat(), "hora": "07:00:00", "tipo_movimiento": "Entrada", "material": "Piedra", "cantidad": 10, "unidad": "m3", "responsable": "Carlos Ramírez", "observaciones": "Para relleno", "usuario": usuario},
        {"proyecto": proyecto, "fecha": (date.today() - timedelta(days=1)).isoformat(), "hora": "13:00:00", "tipo_movimiento": "Salida", "material": "Varilla", "cantidad": 200, "unidad": "varillas", "responsable": "Pedro Gómez", "observaciones": "Refuerzo columnas P5", "usuario": usuario},
        {"proyecto": proyecto, "fecha": date.today().isoformat(), "hora": "07:15:00", "tipo_movimiento": "Entrada", "material": "Cemento", "cantidad": 150, "unidad": "bultos", "responsable": "Carlos Ramírez", "observaciones": "Pedido urgente Argos", "usuario": usuario},
        {"proyecto": proyecto, "fecha": date.today().isoformat(), "hora": "08:30:00", "tipo_movimiento": "Entrada", "material": "Arena", "cantidad": 8, "unidad": "m3", "responsable": "Diego Morales", "observaciones": "", "usuario": usuario},
    ]
    for m in movimientos:
        try:
            data = {**m, "timestamp": datetime.now().isoformat()}
            existing = supabase.table("control_inventario").select("id").eq("proyecto", proyecto).eq("fecha", m["fecha"]).eq("material", m["material"]).eq("tipo_movimiento", m["tipo_movimiento"]).execute()
            if not existing.data:
                supabase.table("control_inventario").insert(data).execute()
                inserted += 1
        except Exception:
            pass
    return inserted

def seed_proveedores_data(supabase):
    inserted = 0
    proveedores = [
        {"nit": "900123456-1", "nombre": "Cementos Argos S.A.", "contacto": "Andrés Bermúdez", "telefono": "3104567890", "categoria": "Materiales", "direccion": "Cra 54 # 72-120, Medellín", "notas": "Proveedor principal de cemento"},
        {"nit": "900987654-2", "nombre": "Aceros Paz del Rio", "contacto": "María López", "telefono": "3156789012", "categoria": "Acero", "direccion": "Calle 80 # 15-40, Bogotá", "notas": "Varilla y acero estructural"},
        {"nit": "800456789-3", "nombre": "Concretos del Caribe", "contacto": "Jorge Pardo", "telefono": "3001234567", "categoria": "Concreto", "direccion": "Vía 40 # 58-30, Barranquilla", "notas": "Concreto premezclado"},
        {"nit": "900345678-4", "nombre": "Ferretería Industrial El Puerto", "contacto": "Ana Gómez", "telefono": "3215678901", "categoria": "Ferretería", "direccion": "Calle 35 # 20-15, Cartagena", "notas": "Herramientas y ferretería"},
        {"nit": "900567890-5", "nombre": "Transportes Rápidos S.A.", "contacto": "Hugo Castillo", "telefono": "3109876543", "categoria": "Transporte", "direccion": "Cra 10 # 45-60, Barranquilla", "notas": "Volquetas y transporte de materiales"},
        {"nit": "900678901-6", "nombre": "Electro Materiales Caribe", "contacto": "Patricia Ruiz", "telefono": "3204561234", "categoria": "Servicios", "direccion": "Calle 52 # 30-18, Barranquilla", "notas": "Material eléctrico"},
        {"nit": "900789012-7", "nombre": "Ladrillera Santander", "contacto": "Felipe Ortega", "telefono": "3112345678", "categoria": "Materiales", "direccion": "Km 5 Vía Barbosa, Bucaramanga", "notas": "Ladrillo cerámico y bloque"},
        {"nit": "900890123-8", "nombre": "Equipos del Atlántico", "contacto": "Raúl Mercado", "telefono": "3158765432", "categoria": "Equipos", "direccion": "Zona Industrial, Mamonal, Cartagena", "notas": "Alquiler de maquinaria pesada"},
    ]
    for p in proveedores:
        try:
            existing = supabase.table("proveedores").select("nit").eq("nit", p["nit"]).execute()
            if not existing.data:
                supabase.table("proveedores").insert(p).execute()
                inserted += 1
        except Exception:
            pass
    return inserted

def seed_maquinas_data(supabase, proyecto, usuario="controlador1"):
    inserted = 0
    registros = [
        {"proyecto": proyecto, "fecha": (date.today() - timedelta(days=3)).isoformat(), "tipo_equipo": "Volqueta", "placa": "ZTX-421", "operador": "Javier Castillo", "hora_inicio": "06:30:00", "hora_fin": "16:30:00", "horas_trabajadas": 10.0, "material_transportado": "Arena", "volumen_m3": 18.0, "numero_viajes": 6, "observaciones": "3 cargas de la cantera", "usuario": usuario},
        {"proyecto": proyecto, "fecha": (date.today() - timedelta(days=3)).isoformat(), "tipo_equipo": "Retroexcavadora", "placa": "KLM-890", "operador": "Raúl Peña", "hora_inicio": "07:00:00", "hora_fin": "17:00:00", "horas_trabajadas": 10.0, "material_transportado": None, "volumen_m3": 0, "numero_viajes": 0, "observaciones": "Excavación zona norte", "usuario": usuario},
        {"proyecto": proyecto, "fecha": (date.today() - timedelta(days=2)).isoformat(), "tipo_equipo": "Volqueta", "placa": "BQR-156", "operador": "Diego Morales", "hora_inicio": "06:00:00", "hora_fin": "14:00:00", "horas_trabajadas": 8.0, "material_transportado": "Gravilla", "volumen_m3": 24.0, "numero_viajes": 8, "observaciones": "Concreto Piso 4", "usuario": usuario},
        {"proyecto": proyecto, "fecha": (date.today() - timedelta(days=2)).isoformat(), "tipo_equipo": "Grúa", "placa": "GHI-789", "operador": "Roberto Díaz", "hora_inicio": "07:00:00", "hora_fin": "15:30:00", "horas_trabajadas": 8.5, "material_transportado": None, "volumen_m3": 0, "numero_viajes": 0, "observaciones": "Izaje vigas Piso 5", "usuario": usuario},
        {"proyecto": proyecto, "fecha": (date.today() - timedelta(days=1)).isoformat(), "tipo_equipo": "Volqueta", "placa": "ZTX-421", "operador": "Javier Castillo", "hora_inicio": "06:30:00", "hora_fin": "15:30:00", "horas_trabajadas": 9.0, "material_transportado": "Tierra", "volumen_m3": 27.0, "numero_viajes": 9, "observaciones": "Retiro escombros", "usuario": usuario},
        {"proyecto": proyecto, "fecha": (date.today() - timedelta(days=1)).isoformat(), "tipo_equipo": "Mototrac", "placa": "MNC-234", "operador": "Raúl Peña", "hora_inicio": "07:00:00", "hora_fin": "12:00:00", "horas_trabajadas": 5.0, "material_transportado": None, "volumen_m3": 0, "numero_viajes": 0, "observaciones": "Compactación terreno", "usuario": usuario},
        {"proyecto": proyecto, "fecha": date.today().isoformat(), "tipo_equipo": "Retroexcavadora", "placa": "KLM-890", "operador": "Raúl Peña", "hora_inicio": "07:00:00", "hora_fin": "16:00:00", "horas_trabajadas": 9.0, "material_transportado": None, "volumen_m3": 0, "numero_viajes": 0, "observaciones": "Zanja para redes hidráulicas", "usuario": usuario},
        {"proyecto": proyecto, "fecha": date.today().isoformat(), "tipo_equipo": "Volqueta", "placa": "BQR-156", "operador": "Diego Morales", "hora_inicio": "06:00:00", "hora_fin": "14:00:00", "horas_trabajadas": 8.0, "material_transportado": "Piedra", "volumen_m3": 15.0, "numero_viajes": 5, "observaciones": "Material para relleno", "usuario": usuario},
    ]
    for r in registros:
        try:
            data = {**r, "timestamp": datetime.now().isoformat()}
            existing = supabase.table("control_maquinas").select("id").eq("proyecto", proyecto).eq("placa", r["placa"]).eq("fecha", r["fecha"]).execute()
            if not existing.data:
                supabase.table("control_maquinas").insert(data).execute()
                inserted += 1
        except Exception:
            pass
    return inserted

def seed_tareas_data(supabase, proyecto, director="director1", residente="residente1"):
    inserted = 0
    tareas = [
        {"id_tarea": "T-001", "proyecto": proyecto, "descripcion": "Revisión de planos estructurales Piso 5", "fecha_limite": (date.today() + timedelta(days=4)).isoformat(), "prioridad": "Alta", "estado": "En progreso", "asignado_a": director, "notas": "Priorizar revisión de cargas", "creado_por": director},
        {"id_tarea": "T-002", "proyecto": proyecto, "descripcion": "Pedir cotización de acero para vigas", "fecha_limite": (date.today() + timedelta(days=1)).isoformat(), "prioridad": "Alta", "estado": "Pendiente", "asignado_a": residente, "notas": "Mínimo 3 cotizaciones"},
        {"id_tarea": "T-003", "proyecto": proyecto, "descripcion": "Coordinar entrega de concreto Piso 4", "fecha_limite": (date.today() - timedelta(days=1)).isoformat(), "prioridad": "Media", "estado": "Completada", "asignado_a": residente, "notas": "Concretos del Caribe confirmado"},
        {"id_tarea": "T-004", "proyecto": proyecto, "descripcion": "Inspección de soldadura columnas P3", "fecha_limite": (date.today() + timedelta(days=7)).isoformat(), "prioridad": "Alta", "estado": "Pendiente", "asignado_a": director, "notas": "Curaduría requiere firma"},
        {"id_tarea": "T-005", "proyecto": proyecto, "descripcion": "Levantamiento topográfico lote norte", "fecha_limite": (date.today() + timedelta(days=2)).isoformat(), "prioridad": "Media", "estado": "En progreso", "asignado_a": residente, "notas": ""},
        {"id_tarea": "T-006", "proyecto": proyecto, "descripcion": "Revisión instalaciones eléctricas Piso 3", "fecha_limite": (date.today() + timedelta(days=10)).isoformat(), "prioridad": "Media", "estado": "Pendiente", "asignado_a": director, "notas": "Esperando planos actualizados"},
        {"id_tarea": "T-007", "proyecto": proyecto, "descripcion": "Verificación de niveles losa entrepiso P4", "fecha_limite": (date.today() + timedelta(days=5)).isoformat(), "prioridad": "Baja", "estado": "Pendiente", "asignado_a": residente, "notas": ""},
        {"id_tarea": "T-008", "proyecto": proyecto, "descripcion": "Cotizar materiales de acabados pisos", "fecha_limite": (date.today() + timedelta(days=14)).isoformat(), "prioridad": "Baja", "estado": "Pendiente", "asignado_a": residente, "notas": "Incluir porcelanato y cerámica"},
    ]
    for t in tareas:
        try:
            existing = supabase.table("tareas").select("id_tarea").eq("id_tarea", t["id_tarea"]).execute()
            if not existing.data:
                data = {**t, "timestamp": datetime.now().isoformat()}
                supabase.table("tareas").insert(data).execute()
                inserted += 1
        except Exception:
            pass
    return inserted

def seed_actividades_data(supabase):
    inserted = 0
    actividades = [
        {"id": "1.1.01", "componente": "OBRA CIVIL", "capitulo": "CIMENTACION", "descripcion": "Excavación para cimentación", "unidad": "m3", "cantidad_total": 450, "valor_unitario": 28500, "valor_total": 12825000},
        {"id": "1.1.02", "componente": "OBRA CIVIL", "capitulo": "CIMENTACION", "descripcion": "Relleno y compactación", "unidad": "m3", "cantidad_total": 280, "valor_unitario": 18500, "valor_total": 5180000},
        {"id": "1.1.03", "componente": "OBRA CIVIL", "capitulo": "CIMENTACION", "descripcion": "Concreto de cimentación f'c=3000 psi", "unidad": "m3", "cantidad_total": 180, "valor_unitario": 485000, "valor_total": 87300000},
        {"id": "1.1.04", "componente": "OBRA CIVIL", "capitulo": "CIMENTACION", "descripcion": "Acero de refuerzo cimentación", "unidad": "kg", "cantidad_total": 12500, "valor_unitario": 4200, "valor_total": 52500000},
        {"id": "1.2.01", "componente": "OBRA CIVIL", "capitulo": "ESTRUCTURA", "descripcion": "Concreto columnas f'c=4000 psi", "unidad": "m3", "cantidad_total": 320, "valor_unitario": 520000, "valor_total": 166400000},
        {"id": "1.2.02", "componente": "OBRA CIVIL", "capitulo": "ESTRUCTURA", "descripcion": "Acero de refuerzo columnas", "unidad": "kg", "cantidad_total": 28000, "valor_unitario": 4300, "valor_total": 120400000},
        {"id": "1.2.03", "componente": "OBRA CIVIL", "capitulo": "ESTRUCTURA", "descripcion": "Concreto vigas y losas f'c=3000 psi", "unidad": "m3", "cantidad_total": 540, "valor_unitario": 495000, "valor_total": 267300000},
        {"id": "1.2.04", "componente": "OBRA CIVIL", "capitulo": "ESTRUCTURA", "descripcion": "Encofrado columnas y vigas", "unidad": "m2", "cantidad_total": 3800, "valor_unitario": 35000, "valor_total": 133000000},
        {"id": "2.1.01", "componente": "MAMPOSTERIA", "capitulo": "DIVISIONES", "descripcion": "Muro en bloque cerámico e=10cm", "unidad": "m2", "cantidad_total": 2500, "valor_unitario": 58000, "valor_total": 145000000},
        {"id": "2.1.02", "componente": "MAMPOSTERIA", "capitulo": "DIVISIONES", "descripcion": "Muro en bloque cerámico e=15cm", "unidad": "m2", "cantidad_total": 1800, "valor_unitario": 72000, "valor_total": 129600000},
        {"id": "2.2.01", "componente": "MAMPOSTERIA", "capitulo": "REVESTIMIENTOS", "descripcion": "Estuco interior muros", "unidad": "m2", "cantidad_total": 3200, "valor_unitario": 18500, "valor_total": 59200000},
        {"id": "2.2.02", "componente": "MAMPOSTERIA", "capitulo": "REVESTIMIENTOS", "descripcion": "Estuco exterior fachada", "unidad": "m2", "cantidad_total": 1600, "valor_unitario": 22000, "valor_total": 35200000},
        {"id": "3.1.01", "componente": "INSTALACIONES", "capitulo": "ELECTRICA", "descripcion": "Instalación red eléctrica provisional", "unidad": "gl", "cantidad_total": 1, "valor_unitario": 12500000, "valor_total": 12500000},
        {"id": "3.1.02", "componente": "INSTALACIONES", "capitulo": "ELECTRICA", "descripcion": "Instalación red eléctrica definitiva", "unidad": "gl", "cantidad_total": 1, "valor_unitario": 89000000, "valor_total": 89000000},
        {"id": "3.2.01", "componente": "INSTALACIONES", "capitulo": "HIDRAULICA", "descripcion": "Instalación red hidráulica", "unidad": "gl", "cantidad_total": 1, "valor_unitario": 65000000, "valor_total": 65000000},
        {"id": "3.2.02", "componente": "INSTALACIONES", "capitulo": "HIDRAULICA", "descripcion": "Instalación red sanitaria", "unidad": "gl", "cantidad_total": 1, "valor_unitario": 58000000, "valor_total": 58000000},
        {"id": "4.1.01", "componente": "ACABADOS", "capitulo": "PISOS", "descripcion": "Piso cerámico interior 60x60", "unidad": "m2", "cantidad_total": 3500, "valor_unitario": 68000, "valor_total": 238000000},
        {"id": "4.1.02", "componente": "ACABADOS", "capitulo": "PISOS", "descripcion": "Piso porcelanato zonas comunes", "unidad": "m2", "cantidad_total": 800, "valor_unitario": 95000, "valor_total": 76000000},
        {"id": "4.2.01", "componente": "ACABADOS", "capitulo": "PINTURA", "descripcion": "Pintura interior vinilo 2 manos", "unidad": "m2", "cantidad_total": 4800, "valor_unitario": 12000, "valor_total": 57600000},
        {"id": "4.2.02", "componente": "ACABADOS", "capitulo": "PINTURA", "descripcion": "Pintura exterior impermeabilizante", "unidad": "m2", "cantidad_total": 1800, "valor_unitario": 18000, "valor_total": 32400000},
    ]
    for a in actividades:
        try:
            existing = supabase.table("actividades").select("id").eq("id", a["id"]).execute()
            if not existing.data:
                supabase.table("actividades").insert(a).execute()
                inserted += 1
        except Exception:
            pass
    return inserted

def seed_avances_data(supabase, proyecto, usuario="director1"):
    inserted = seed_actividades_data(supabase)
    porcentajes = [0.75, 0.30, 0.60, 0.45, 0.25, 0.15, 0.10, 0.05, 0.50, 0.35, 0.20, 0.80, 0.40, 0.55, 0.10, 0.0, 0.0, 0.0, 0.0, 0.0]
    act_data = [
        {"id": "1.1.01", "cantidad_total": 450}, {"id": "1.1.02", "cantidad_total": 280}, {"id": "1.1.03", "cantidad_total": 180},
        {"id": "1.1.04", "cantidad_total": 12500}, {"id": "1.2.01", "cantidad_total": 320}, {"id": "1.2.02", "cantidad_total": 28000},
        {"id": "1.2.03", "cantidad_total": 540}, {"id": "1.2.04", "cantidad_total": 3800}, {"id": "2.1.01", "cantidad_total": 2500},
        {"id": "2.1.02", "cantidad_total": 1800}, {"id": "2.2.01", "cantidad_total": 3200}, {"id": "2.2.02", "cantidad_total": 1600},
        {"id": "3.1.01", "cantidad_total": 1}, {"id": "3.1.02", "cantidad_total": 1}, {"id": "3.2.01", "cantidad_total": 1},
        {"id": "3.2.02", "cantidad_total": 1}, {"id": "4.1.01", "cantidad_total": 3500}, {"id": "4.1.02", "cantidad_total": 800},
        {"id": "4.2.01", "cantidad_total": 4800}, {"id": "4.2.02", "cantidad_total": 1800},
    ]
    for i, a in enumerate(act_data):
        if porcentajes[i] > 0:
            cant = round(a["cantidad_total"] * porcentajes[i], 1)
            data = {
                "proyecto": proyecto,
                "fecha": (date.today() - timedelta(days=random.randint(1, 30))).isoformat(),
                "id_item": a["id"],
                "cantidad": cant,
                "usuario": usuario,
            }
            try:
                supabase.table("avances").insert(data).execute()
                inserted += 1
            except Exception:
                pass
    return inserted

def seed_asistencia_data(supabase, proyecto, usuario="director1"):
    inserted = 0
    trabajadores = [
        "Carlos Ramírez", "José Martínez", "Miguel Torres", "Pedro Gómez",
        "Luis Hernández", "Andrés López", "Roberto Díaz", "Fernando Vargas",
        "Diego Morales", "Javier Castillo", "Raúl Peña", "Sandra Muñoz"
    ]
    cargos = ["Maestro de obra", "Albañil", "Ayudante general", "Herrero", "Electricista", "Plomero", "Carpintero", "Pintor", "Ayudante general", "Operador", "Maestro de obra", "Auxiliar"]
    estados = ["Presente", "Presente", "Presente", "Presente", "Presente", "Ausente", "Permiso"]
    for i in range(7):
        fecha = (date.today() - timedelta(days=i)).isoformat()
        for j, nombre in enumerate(trabajadores):
            estado = random.choice(estados)
            data = {"proyecto": proyecto, "fecha": fecha, "trabajador": nombre, "cargo": cargos[j], "estado": estado, "usuario": usuario}
            try:
                existing = supabase.table("asistencia").select("id").eq("proyecto", proyecto).eq("fecha", fecha).eq("trabajador", nombre).execute()
                if not existing.data:
                    supabase.table("asistencia").insert(data).execute()
                    inserted += 1
            except Exception:
                pass
    return inserted

def seed_nomina_data(supabase, proyecto):
    inserted = 0
    movimientos = [
        {"proyecto": proyecto, "fecha": (date.today() - timedelta(days=30)).isoformat(), "trabajador": "Carlos Ramírez", "tipo": "Mensual", "valor": 3200000, "notas": "Salario mes marzo"},
        {"proyecto": proyecto, "fecha": (date.today() - timedelta(days=30)).isoformat(), "trabajador": "José Martínez", "tipo": "Mensual", "valor": 2800000, "notas": "Salario mes marzo"},
        {"proyecto": proyecto, "fecha": (date.today() - timedelta(days=30)).isoformat(), "trabajador": "Miguel Torres", "tipo": "Jornal diario", "valor": 640000, "notas": "8 días @ 80000"},
        {"proyecto": proyecto, "fecha": (date.today() - timedelta(days=30)).isoformat(), "trabajador": "Pedro Gómez", "tipo": "Mensual", "valor": 2900000, "notas": "Salario mes marzo"},
        {"proyecto": proyecto, "fecha": (date.today() - timedelta(days=30)).isoformat(), "trabajador": "Luis Hernández", "tipo": "Mensual", "valor": 3100000, "notas": "Salario mes marzo"},
        {"proyecto": proyecto, "fecha": (date.today() - timedelta(days=15)).isoformat(), "trabajador": "Carlos Ramírez", "tipo": "Quincenal", "valor": 1600000, "notas": "Quincena 1 abril"},
        {"proyecto": proyecto, "fecha": (date.today() - timedelta(days=15)).isoformat(), "trabajador": "José Martínez", "tipo": "Quincenal", "valor": 1400000, "notas": "Quincena 1 abril"},
        {"proyecto": proyecto, "fecha": (date.today() - timedelta(days=10)).isoformat(), "trabajador": "Pedro Gómez", "tipo": "Prestamo", "valor": 500000, "notas": "Préstamo personal"},
        {"proyecto": proyecto, "fecha": (date.today() - timedelta(days=10)).isoformat(), "trabajador": "Andrés López", "tipo": "Quincenal", "valor": 1350000, "notas": "Quincena 1 abril"},
        {"proyecto": proyecto, "fecha": (date.today() - timedelta(days=5)).isoformat(), "trabajador": "Roberto Díaz", "tipo": "Bonificacion", "valor": 400000, "notas": "Bono productividad"},
        {"proyecto": proyecto, "fecha": (date.today() - timedelta(days=3)).isoformat(), "trabajador": "Fernando Vargas", "tipo": "Jornal diario", "valor": 720000, "notas": "9 días @ 80000"},
        {"proyecto": proyecto, "fecha": (date.today() - timedelta(days=2)).isoformat(), "trabajador": "Carlos Ramírez", "tipo": "Quincenal", "valor": 1600000, "notas": "Quincena 2 abril"},
        {"proyecto": proyecto, "fecha": (date.today() - timedelta(days=2)).isoformat(), "trabajador": "Pedro Gómez", "tipo": "Deduccion", "valor": 200000, "notas": "Descuento préstamo"},
        {"proyecto": proyecto, "fecha": date.today().isoformat(), "trabajador": "José Martínez", "tipo": "Quincenal", "valor": 1400000, "notas": "Quincena 2 abril"},
        {"proyecto": proyecto, "fecha": date.today().isoformat(), "trabajador": "Miguel Torres", "tipo": "Jornal diario", "valor": 480000, "notas": "6 días @ 80000"},
    ]
    for m in movimientos:
        try:
            supabase.table("nomina").insert(m).execute()
            inserted += 1
        except Exception:
            pass
    return inserted

def seed_materiales_data(supabase, proyecto, usuario="residente1"):
    inserted = 0
    solicitudes = [
        {"proyecto": proyecto, "fecha": (date.today() - timedelta(days=7)).isoformat(), "requerimiento": "120 bultos de cemento para vigas Piso 5", "estado": "Entregado", "usuario": usuario},
        {"proyecto": proyecto, "fecha": (date.today() - timedelta(days=5)).isoformat(), "requerimiento": "8 m3 de arena lavada para acabados", "estado": "En proceso", "usuario": usuario},
        {"proyecto": proyecto, "fecha": (date.today() - timedelta(days=3)).isoformat(), "requerimiento": "300 varillas de acero 1/2 pulgada", "estado": "Solicitado", "usuario": usuario},
        {"proyecto": proyecto, "fecha": (date.today() - timedelta(days=2)).isoformat(), "requerimiento": "[Urgente] 5 m3 de concreto premezclado f'c=4000", "estado": "Solicitado", "usuario": "director1"},
        {"proyecto": proyecto, "fecha": date.today().isoformat(), "requerimiento": "2 rollos de malla electrosoldada para losa", "estado": "Solicitado", "usuario": usuario},
    ]
    for s in solicitudes:
        try:
            supabase.table("materiales").insert(s).execute()
            inserted += 1
        except Exception:
            pass
    return inserted

def seed_config_data(supabase, proyecto):
    try:
        existing = supabase.table("config").select("*").execute()
        if existing.data and len(existing.data) > 0:
            supabase.table("config").update({
                "proyecto": proyecto,
                "total_costo_directo": 1450000000,
                "total_costo_suministros": 320000000,
                "costo_total_obra": 1770000000,
                "costo_total_proyecto": 2100000000,
            }).eq("id", existing.data[0]["id"]).execute()
            return 0
        else:
            supabase.table("config").insert({
                "proyecto": proyecto,
                "total_costo_directo": 1450000000,
                "total_costo_suministros": 320000000,
                "costo_total_obra": 1770000000,
                "costo_total_proyecto": 2100000000,
            }).execute()
            return 1
    except Exception:
        try:
            supabase.table("config").insert({
                "proyecto": proyecto,
                "total_costo_directo": 1450000000,
                "total_costo_suministros": 320000000,
                "costo_total_obra": 1770000000,
                "costo_total_proyecto": 2100000000,
            }).execute()
            return 1
        except Exception:
            return 0


def render_seed_button(supabase, proyecto, section, seed_fn, key_prefix="seed"):
    es_dir = st.session_state.get("rol_actual") == "Director"
    if not es_dir:
        return
    with st.expander("🧪 Agregar datos de prueba", expanded=False):
        proj_display = proyecto if proyecto else "Global"
        st.caption(f"Inserta datos de ejemplo para **{section}** | Proyecto: `{proj_display}`")
        if st.button(f"📥 Insertar datos de {section}", key=f"{key_prefix}_{section}", use_container_width=True):
            try:
                count = seed_fn(supabase, proyecto) if callable(seed_fn) and seed_fn.__code__.co_argcount > 1 else seed_fn(supabase)
                st.success(f"✅ {count} registro(s) insertado(s) para {section}")
                st.cache_data.clear()
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error: {str(e)[:100]}")