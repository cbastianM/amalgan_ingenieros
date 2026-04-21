# database/demo_data.py
# Pre-loaded demo data for the ALMAGAN INGENIEROS app.
# Called by DemoClient to lazily populate tables on first access.
from datetime import date, timedelta
import copy

PROYECTO = "Edificio Colombo Americana"

MATERIALES_APROBADOS = [
    {"material": "Cemento Gris Portland Tipo I", "unidad": "bultos", "categoria": "Cementantes"},
    {"material": "Cemento Gris Portland Tipo III", "unidad": "bultos", "categoria": "Cementantes"},
    {"material": "Arena Lavada Granulada", "unidad": "m3", "categoria": "Agregados"},
    {"material": "Arena de Río", "unidad": "m3", "categoria": "Agregados"},
    {"material": "Grava de 1/2 Pulgada", "unidad": "m3", "categoria": "Agregados"},
    {"material": "Grava de 3/4 Pulgada", "unidad": "m3", "categoria": "Agregados"},
    {"material": "Piedra de Relleno", "unidad": "m3", "categoria": "Agregados"},
    {"material": "Concreto Premezclado f'c=3000 psi", "unidad": "m3", "categoria": "Concretos"},
    {"material": "Concreto Premezclado f'c=4000 psi", "unidad": "m3", "categoria": "Concretos"},
    {"material": "Mortero de Pegue Premezclado", "unidad": "bultos", "categoria": "Cementantes"},
    {"material": "Varilla de Acero Corrugada 3/8\"", "unidad": "varillas", "categoria": "Acero"},
    {"material": "Varilla de Acero Corrugada 1/2\"", "unidad": "varillas", "categoria": "Acero"},
    {"material": "Varilla de Acero Corrugada 5/8\"", "unidad": "varillas", "categoria": "Acero"},
    {"material": "Malla Electrosoldada 6x6 calibre 10/10", "unidad": "rollos", "categoria": "Acero"},
    {"material": "Bloque Cerámico Estructural 15x20x30 cm", "unidad": "unidades", "categoria": "Mampostería"},
    {"material": "Bloque Cerámico Divisorio 10x20x30 cm", "unidad": "unidades", "categoria": "Mampostería"},
    {"material": "Ladrillo Cerámico Hueco 12x20x30 cm", "unidad": "unidades", "categoria": "Mampostería"},
    {"material": "Estuco Interior para Muros", "unidad": "bultos", "categoria": "Acabados"},
    {"material": "Pintura Vinilo Interior Dos Manos", "unidad": "galones", "categoria": "Acabados"},
    {"material": "Pintura Impermeabilizante Exterior", "unidad": "galones", "categoria": "Acabados"},
    {"material": "Piso Cerámico Interior 60x60 cm", "unidad": "m2", "categoria": "Acabados"},
    {"material": "Porcelanato Zonas Comunes 80x80 cm", "unidad": "m2", "categoria": "Acabados"},
    {"material": "Tubo PVC Hidráulico 4 pulgadas", "unidad": "tubos", "categoria": "Instalaciones"},
    {"material": "Tubo PVC Sanitario 3 pulgadas", "unidad": "tubos", "categoria": "Instalaciones"},
    {"material": "Cable Eléctrico THW Calibre 10", "unidad": "m", "categoria": "Instalaciones"},
    {"material": "Cable Eléctrico THW Calibre 12", "unidad": "m", "categoria": "Instalaciones"},
    {"material": "Madera Pino Estructura 2x4\"", "unidad": "piezas", "categoria": "Encofrados"},
    {"material": "Plywood Fenólico 18mm", "unidad": "planchas", "categoria": "Encofrados"},
]


def _today(offset=0):
    return (date.today() - timedelta(days=offset)).isoformat()


def init_demo_data(store: dict, key: str, table_name: str):
    if key in store and store[key]:
        return
    filler = _FILLERS.get(table_name)
    if filler:
        store[key] = copy.deepcopy(filler())
    else:
        store[key] = []


def _fill_config():
    return [
        {
            "id": "cfg-001",
            "proyecto": PROYECTO,
            "total_costo_directo": 1450000000,
            "total_costo_suministros": 320000000,
            "costo_total_obra": 1770000000,
            "costo_total_proyecto": 2100000000,
        }
    ]


def _fill_usuarios():
    return [
        {"id": "u1", "usuario": "director1", "clave": "1234", "rol": "Director", "activo": True, "nombre_visible": "Carlos Mendoza", "foto_perfil": None},
        {"id": "u2", "usuario": "residente1", "clave": "1234", "rol": "Residente", "activo": True, "nombre_visible": "Ana López", "foto_perfil": None},
        {"id": "u3", "usuario": "almacenista1", "clave": "1234", "rol": "Almacenista", "activo": True, "nombre_visible": "Pedro Gómez", "foto_perfil": None},
        {"id": "u4", "usuario": "controlador1", "clave": "1234", "rol": "Controlador", "activo": True, "nombre_visible": "Luis Ramírez", "foto_perfil": None},
    ]


def _fill_actividades():
    return [
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


def _fill_avances():
    pcts = [0.75, 0.30, 0.60, 0.45, 0.25, 0.15, 0.10, 0.05, 0.50, 0.35, 0.20, 0.80, 0.40, 0.55, 0.10, 0.0, 0.0, 0.0, 0.0, 0.0]
    acts = [
        ("1.1.01", 450), ("1.1.02", 280), ("1.1.03", 180), ("1.1.04", 12500),
        ("1.2.01", 320), ("1.2.02", 28000), ("1.2.03", 540), ("1.2.04", 3800),
        ("2.1.01", 2500), ("2.1.02", 1800), ("2.2.01", 3200), ("2.2.02", 1600),
        ("3.1.01", 1), ("3.1.02", 1), ("3.2.01", 1), ("3.2.02", 1),
        ("4.1.01", 3500), ("4.1.02", 800), ("4.2.01", 4800), ("4.2.02", 1800),
    ]
    rows = []
    import uuid
    for i, (aid, total) in enumerate(acts):
        if pcts[i] > 0:
            rows.append({
                "id": str(uuid.uuid4())[:8],
                "proyecto": PROYECTO,
                "fecha": _today(random_offset()),
                "id_item": aid,
                "cantidad": round(total * pcts[i], 1),
                "usuario": "director1",
                "timestamp": _today(0) + "T08:00:00",
            })
    return rows


def random_offset():
    import random
    return random.randint(1, 20)


def _fill_tareas():
    return [
        {"id_tarea": "T-001", "proyecto": PROYECTO, "descripcion": "Revisión de planos estructurales Piso 5", "fecha_limite": _today(4), "prioridad": "Alta", "estado": "En progreso", "asignado_a": "director1", "notas": "Priorizar revisión de cargas", "creado_por": "director1", "timestamp": _today(0) + "T08:00:00"},
        {"id_tarea": "T-002", "proyecto": PROYECTO, "descripcion": "Pedir cotización de acero para vigas", "fecha_limite": _today(1), "prioridad": "Alta", "estado": "Pendiente", "asignado_a": "residente1", "notas": "Mínimo 3 cotizaciones", "creado_por": "director1", "timestamp": _today(0) + "T08:00:00"},
        {"id_tarea": "T-003", "proyecto": PROYECTO, "descripcion": "Coordinar entrega de concreto Piso 4", "fecha_limite": _today(-1), "prioridad": "Media", "estado": "Completada", "asignado_a": "residente1", "notas": "Concretos del Caribe confirmado", "creado_por": "director1", "timestamp": _today(0) + "T08:00:00"},
        {"id_tarea": "T-004", "proyecto": PROYECTO, "descripcion": "Inspección de soldadura columnas P3", "fecha_limite": _today(7), "prioridad": "Alta", "estado": "Pendiente", "asignado_a": "director1", "notas": "Curaduría requiere firma", "creado_por": "director1", "timestamp": _today(0) + "T08:00:00"},
        {"id_tarea": "T-005", "proyecto": PROYECTO, "descripcion": "Levantamiento topográfico lote norte", "fecha_limite": _today(2), "prioridad": "Media", "estado": "En progreso", "asignado_a": "residente1", "notas": "", "creado_por": "director1", "timestamp": _today(0) + "T08:00:00"},
        {"id_tarea": "T-006", "proyecto": PROYECTO, "descripcion": "Revisión instalaciones eléctricas Piso 3", "fecha_limite": _today(10), "prioridad": "Media", "estado": "Pendiente", "asignado_a": "director1", "notas": "Esperando planos actualizados", "creado_por": "director1", "timestamp": _today(0) + "T08:00:00"},
        {"id_tarea": "T-007", "proyecto": PROYECTO, "descripcion": "Verificación de niveles losa entrepiso P4", "fecha_limite": _today(5), "prioridad": "Baja", "estado": "Pendiente", "asignado_a": "residente1", "notas": "", "creado_por": "director1", "timestamp": _today(0) + "T08:00:00"},
        {"id_tarea": "T-008", "proyecto": PROYECTO, "descripcion": "Cotizar materiales de acabados pisos", "fecha_limite": _today(14), "prioridad": "Baja", "estado": "Pendiente", "asignado_a": "residente1", "notas": "Incluir porcelanato y cerámica", "creado_por": "director1", "timestamp": _today(0) + "T08:00:00"},
    ]


def _fill_inventario():
    return [
        {"id": "inv-001", "proyecto": PROYECTO, "fecha": _today(5), "hora": "07:30:00", "tipo_movimiento": "Entrada", "material": "Cemento", "cantidad": 200, "unidad": "bultos", "responsable": "Carlos Ramírez", "observaciones": "Entrega Cementos Argos", "usuario": "director1", "timestamp": _today(5) + "T07:30:00"},
        {"id": "inv-002", "proyecto": PROYECTO, "fecha": _today(5), "hora": "08:15:00", "tipo_movimiento": "Entrada", "material": "Arena", "cantidad": 15, "unidad": "m3", "responsable": "Carlos Ramírez", "observaciones": "Volqueta 3 cargas", "usuario": "director1", "timestamp": _today(5) + "T08:15:00"},
        {"id": "inv-003", "proyecto": PROYECTO, "fecha": _today(4), "hora": "07:45:00", "tipo_movimiento": "Entrada", "material": "Varilla", "cantidad": 500, "unidad": "varillas", "responsable": "José Martínez", "observaciones": "Varilla 1/2 y 3/8", "usuario": "director1", "timestamp": _today(4) + "T07:45:00"},
        {"id": "inv-004", "proyecto": PROYECTO, "fecha": _today(4), "hora": "09:00:00", "tipo_movimiento": "Entrada", "material": "Grava", "cantidad": 12, "unidad": "m3", "responsable": "José Martínez", "observaciones": "", "usuario": "director1", "timestamp": _today(4) + "T09:00:00"},
        {"id": "inv-005", "proyecto": PROYECTO, "fecha": _today(3), "hora": "10:30:00", "tipo_movimiento": "Salida", "material": "Cemento", "cantidad": 80, "unidad": "bultos", "responsable": "Miguel Torres", "observaciones": "Para viga Piso 4", "usuario": "director1", "timestamp": _today(3) + "T10:30:00"},
        {"id": "inv-006", "proyecto": PROYECTO, "fecha": _today(3), "hora": "11:00:00", "tipo_movimiento": "Salida", "material": "Arena", "cantidad": 5, "unidad": "m3", "responsable": "Miguel Torres", "observaciones": "Para mezcla columnas", "usuario": "director1", "timestamp": _today(3) + "T11:00:00"},
        {"id": "inv-007", "proyecto": PROYECTO, "fecha": _today(2), "hora": "07:20:00", "tipo_movimiento": "Entrada", "material": "Ladrillo", "cantidad": 5000, "unidad": "und", "responsable": "Carlos Ramírez", "observaciones": "Bloque cerámico 10cm", "usuario": "director1", "timestamp": _today(2) + "T07:20:00"},
        {"id": "inv-008", "proyecto": PROYECTO, "fecha": _today(2), "hora": "14:00:00", "tipo_movimiento": "Salida", "material": "Cemento", "cantidad": 50, "unidad": "bultos", "responsable": "Pedro Gómez", "observaciones": "Para muros Piso 3", "usuario": "director1", "timestamp": _today(2) + "T14:00:00"},
        {"id": "inv-009", "proyecto": PROYECTO, "fecha": _today(1), "hora": "07:00:00", "tipo_movimiento": "Entrada", "material": "Piedra", "cantidad": 10, "unidad": "m3", "responsable": "Carlos Ramírez", "observaciones": "Para relleno", "usuario": "director1", "timestamp": _today(1) + "T07:00:00"},
        {"id": "inv-010", "proyecto": PROYECTO, "fecha": _today(1), "hora": "13:00:00", "tipo_movimiento": "Salida", "material": "Varilla", "cantidad": 200, "unidad": "varillas", "responsable": "Pedro Gómez", "observaciones": "Refuerzo columnas P5", "usuario": "director1", "timestamp": _today(1) + "T13:00:00"},
        {"id": "inv-011", "proyecto": PROYECTO, "fecha": _today(0), "hora": "07:15:00", "tipo_movimiento": "Entrada", "material": "Cemento", "cantidad": 150, "unidad": "bultos", "responsable": "Carlos Ramírez", "observaciones": "Pedido urgente Argos", "usuario": "director1", "timestamp": _today(0) + "T07:15:00"},
        {"id": "inv-012", "proyecto": PROYECTO, "fecha": _today(0), "hora": "08:30:00", "tipo_movimiento": "Entrada", "material": "Arena", "cantidad": 8, "unidad": "m3", "responsable": "Diego Morales", "observaciones": "", "usuario": "director1", "timestamp": _today(0) + "T08:30:00"},
    ]


def _fill_proveedores():
    return [
        {"id": "prov-001", "nit": "900123456-1", "nombre": "Cementos Argos S.A.", "contacto": "Andrés Bermúdez", "telefono": "3104567890", "categoria": "Materiales", "direccion": "Cra 54 # 72-120, Medellín", "notas": "Proveedor principal de cemento"},
        {"id": "prov-002", "nit": "900987654-2", "nombre": "Aceros Paz del Rio", "contacto": "María López", "telefono": "3156789012", "categoria": "Acero", "direccion": "Calle 80 # 15-40, Bogotá", "notas": "Varilla y acero estructural"},
        {"id": "prov-003", "nit": "800456789-3", "nombre": "Concretos del Caribe", "contacto": "Jorge Pardo", "telefono": "3001234567", "categoria": "Concreto", "direccion": "Vía 40 # 58-30, Barranquilla", "notas": "Concreto premezclado"},
        {"id": "prov-004", "nit": "900345678-4", "nombre": "Ferretería Industrial El Puerto", "contacto": "Ana Gómez", "telefono": "3215678901", "categoria": "Ferretería", "direccion": "Calle 35 # 20-15, Cartagena", "notas": "Herramientas y ferretería"},
        {"id": "prov-005", "nit": "900567890-5", "nombre": "Transportes Rápidos S.A.", "contacto": "Hugo Castillo", "telefono": "3109876543", "categoria": "Transporte", "direccion": "Cra 10 # 45-60, Barranquilla", "notas": "Volquetas y transporte de materiales"},
        {"id": "prov-006", "nit": "900678901-6", "nombre": "Electro Materiales Caribe", "contacto": "Patricia Ruiz", "telefono": "3204561234", "categoria": "Servicios", "direccion": "Calle 52 # 30-18, Barranquilla", "notas": "Material eléctrico"},
        {"id": "prov-007", "nit": "900789012-7", "nombre": "Ladrillera Santander", "contacto": "Felipe Ortega", "telefono": "3112345678", "categoria": "Materiales", "direccion": "Km 5 Vía Barbosa, Bucaramanga", "notas": "Ladrillo cerámico y bloque"},
        {"id": "prov-008", "nit": "900890123-8", "nombre": "Equipos del Atlántico", "contacto": "Raúl Mercado", "telefono": "3158765432", "categoria": "Equipos", "direccion": "Zona Industrial, Mamonal, Cartagena", "notas": "Alquiler de maquinaria pesada"},
    ]


def _fill_maquinas():
    return [
        {"id": "maq-001", "proyecto": PROYECTO, "fecha": _today(3), "tipo_equipo": "Volqueta", "placa": "ZTX-421", "operador": "Javier Castillo", "hora_inicio": "06:30:00", "hora_fin": "16:30:00", "horas_trabajadas": 10.0, "material_transportado": "Arena", "volumen_m3": 18.0, "numero_viajes": 6, "observaciones": "3 cargas de la cantera", "usuario": "controlador1", "timestamp": _today(3) + "T06:30:00"},
        {"id": "maq-002", "proyecto": PROYECTO, "fecha": _today(3), "tipo_equipo": "Retroexcavadora", "placa": "KLM-890", "operador": "Raúl Peña", "hora_inicio": "07:00:00", "hora_fin": "17:00:00", "horas_trabajadas": 10.0, "material_transportado": None, "volumen_m3": 0, "numero_viajes": 0, "observaciones": "Excavación zona norte", "usuario": "controlador1", "timestamp": _today(3) + "T07:00:00"},
        {"id": "maq-003", "proyecto": PROYECTO, "fecha": _today(2), "tipo_equipo": "Volqueta", "placa": "BQR-156", "operador": "Diego Morales", "hora_inicio": "06:00:00", "hora_fin": "14:00:00", "horas_trabajadas": 8.0, "material_transportado": "Gravilla", "volumen_m3": 24.0, "numero_viajes": 8, "observaciones": "Concreto Piso 4", "usuario": "controlador1", "timestamp": _today(2) + "T06:00:00"},
        {"id": "maq-004", "proyecto": PROYECTO, "fecha": _today(2), "tipo_equipo": "Grúa", "placa": "GHI-789", "operador": "Roberto Díaz", "hora_inicio": "07:00:00", "hora_fin": "15:30:00", "horas_trabajadas": 8.5, "material_transportado": None, "volumen_m3": 0, "numero_viajes": 0, "observaciones": "Izaje vigas Piso 5", "usuario": "controlador1", "timestamp": _today(2) + "T07:00:00"},
        {"id": "maq-005", "proyecto": PROYECTO, "fecha": _today(1), "tipo_equipo": "Volqueta", "placa": "ZTX-421", "operador": "Javier Castillo", "hora_inicio": "06:30:00", "hora_fin": "15:30:00", "horas_trabajadas": 9.0, "material_transportado": "Tierra", "volumen_m3": 27.0, "numero_viajes": 9, "observaciones": "Retiro escombros", "usuario": "controlador1", "timestamp": _today(1) + "T06:30:00"},
        {"id": "maq-006", "proyecto": PROYECTO, "fecha": _today(1), "tipo_equipo": "Mototrac", "placa": "MNC-234", "operador": "Raúl Peña", "hora_inicio": "07:00:00", "hora_fin": "12:00:00", "horas_trabajadas": 5.0, "material_transportado": None, "volumen_m3": 0, "numero_viajes": 0, "observaciones": "Compactación terreno", "usuario": "controlador1", "timestamp": _today(1) + "T07:00:00"},
        {"id": "maq-007", "proyecto": PROYECTO, "fecha": _today(0), "tipo_equipo": "Retroexcavadora", "placa": "KLM-890", "operador": "Raúl Peña", "hora_inicio": "07:00:00", "hora_fin": "16:00:00", "horas_trabajadas": 9.0, "material_transportado": None, "volumen_m3": 0, "numero_viajes": 0, "observaciones": "Zanja para redes hidráulicas", "usuario": "controlador1", "timestamp": _today(0) + "T07:00:00"},
        {"id": "maq-008", "proyecto": PROYECTO, "fecha": _today(0), "tipo_equipo": "Volqueta", "placa": "BQR-156", "operador": "Diego Morales", "hora_inicio": "06:00:00", "hora_fin": "14:00:00", "horas_trabajadas": 8.0, "material_transportado": "Piedra", "volumen_m3": 15.0, "numero_viajes": 5, "observaciones": "Material para relleno", "usuario": "controlador1", "timestamp": _today(0) + "T06:00:00"},
    ]


def _fill_asistencia():
    import random
    import uuid
    trabajadores = [
        ("Carlos Ramírez", "Maestro de obra"), ("José Martínez", "Albañil"), ("Miguel Torres", "Ayudante general"),
        ("Pedro Gómez", "Herrero"), ("Luis Hernández", "Electricista"), ("Andrés López", "Plomero"),
        ("Roberto Díaz", "Carpintero"), ("Fernando Vargas", "Pintor"), ("Diego Morales", "Ayudante general"),
        ("Javier Castillo", "Operador"), ("Raúl Peña", "Maestro de obra"), ("Sandra Muñoz", "Auxiliar"),
    ]
    estados = ["Presente", "Presente", "Presente", "Presente", "Presente", "Ausente", "Permiso"]
    rows = []
    for i in range(7):
        fecha = _today(i)
        for nombre, cargo in trabajadores:
            rows.append({
                "id": str(uuid.uuid4())[:8],
                "proyecto": PROYECTO,
                "fecha": fecha,
                "trabajador": nombre,
                "cargo": cargo,
                "estado": random.choice(estados),
                "usuario": "director1",
            })
    return rows


def _fill_nomina():
    return [
        {"id": "nom-001", "proyecto": PROYECTO, "fecha": _today(30), "trabajador": "Carlos Ramírez", "tipo": "Mensual", "valor": 3200000, "notas": "Salario mes marzo"},
        {"id": "nom-002", "proyecto": PROYECTO, "fecha": _today(30), "trabajador": "José Martínez", "tipo": "Mensual", "valor": 2800000, "notas": "Salario mes marzo"},
        {"id": "nom-003", "proyecto": PROYECTO, "fecha": _today(30), "trabajador": "Miguel Torres", "tipo": "Jornal diario", "valor": 640000, "notas": "8 días @ 80000"},
        {"id": "nom-004", "proyecto": PROYECTO, "fecha": _today(30), "trabajador": "Pedro Gómez", "tipo": "Mensual", "valor": 2900000, "notas": "Salario mes marzo"},
        {"id": "nom-005", "proyecto": PROYECTO, "fecha": _today(30), "trabajador": "Luis Hernández", "tipo": "Mensual", "valor": 3100000, "notas": "Salario mes marzo"},
        {"id": "nom-006", "proyecto": PROYECTO, "fecha": _today(15), "trabajador": "Carlos Ramírez", "tipo": "Quincenal", "valor": 1600000, "notas": "Quincena 1 abril"},
        {"id": "nom-007", "proyecto": PROYECTO, "fecha": _today(15), "trabajador": "José Martínez", "tipo": "Quincenal", "valor": 1400000, "notas": "Quincena 1 abril"},
        {"id": "nom-008", "proyecto": PROYECTO, "fecha": _today(10), "trabajador": "Pedro Gómez", "tipo": "Prestamo", "valor": 500000, "notas": "Préstamo personal"},
        {"id": "nom-009", "proyecto": PROYECTO, "fecha": _today(10), "trabajador": "Andrés López", "tipo": "Quincenal", "valor": 1350000, "notas": "Quincena 1 abril"},
        {"id": "nom-010", "proyecto": PROYECTO, "fecha": _today(5), "trabajador": "Roberto Díaz", "tipo": "Bonificacion", "valor": 400000, "notas": "Bono productividad"},
        {"id": "nom-011", "proyecto": PROYECTO, "fecha": _today(3), "trabajador": "Fernando Vargas", "tipo": "Jornal diario", "valor": 720000, "notas": "9 días @ 80000"},
        {"id": "nom-012", "proyecto": PROYECTO, "fecha": _today(2), "trabajador": "Carlos Ramírez", "tipo": "Quincenal", "valor": 1600000, "notas": "Quincena 2 abril"},
        {"id": "nom-013", "proyecto": PROYECTO, "fecha": _today(2), "trabajador": "Pedro Gómez", "tipo": "Deduccion", "valor": 200000, "notas": "Descuento préstamo"},
        {"id": "nom-014", "proyecto": PROYECTO, "fecha": _today(0), "trabajador": "José Martínez", "tipo": "Quincenal", "valor": 1400000, "notas": "Quincena 2 abril"},
        {"id": "nom-015", "proyecto": PROYECTO, "fecha": _today(0), "trabajador": "Miguel Torres", "tipo": "Jornal diario", "valor": 480000, "notas": "6 días @ 80000"},
    ]


def _fill_materiales():
    return [
        {"id": "mat-001", "proyecto": PROYECTO, "fecha": _today(7), "material": "Cemento Gris Portland Tipo I", "cantidad": 120, "unidad": "bultos", "requerimiento": "120 bultos de Cemento Gris Portland Tipo I para vigas Piso 5", "estado": "Entregado", "usuario": "residente1"},
        {"id": "mat-002", "proyecto": PROYECTO, "fecha": _today(5), "material": "Arena Lavada Granulada", "cantidad": 8, "unidad": "m3", "requerimiento": "8 m3 de Arena Lavada Granulada para acabados", "estado": "En proceso", "usuario": "residente1"},
        {"id": "mat-003", "proyecto": PROYECTO, "fecha": _today(3), "material": "Varilla de Acero Corrugada 1/2\"", "cantidad": 300, "unidad": "varillas", "requerimiento": "300 varillas de Varilla de Acero Corrugada 1/2\" para columna P3", "estado": "Solicitado", "usuario": "residente1"},
        {"id": "mat-004", "proyecto": PROYECTO, "fecha": _today(2), "material": "Concreto Premezclado f'c=4000 psi", "cantidad": 5, "unidad": "m3", "requerimiento": "[Urgente] 5 m3 de Concreto Premezclado f'c=4000 psi para losa P4", "estado": "Solicitado", "usuario": "director1"},
        {"id": "mat-005", "proyecto": PROYECTO, "fecha": _today(0), "material": "Malla Electrosoldada 6x6 calibre 10/10", "cantidad": 2, "unidad": "rollos", "requerimiento": "2 rollos de Malla Electrosoldada 6x6 calibre 10/10 para losa", "estado": "Solicitado", "usuario": "residente1"},
    ]


def _fill_trabajadores():
    return [
        {"id": "trab-001", "nombre": "Carlos Ramírez", "cargo": "Maestro de obra", "activo": True},
        {"id": "trab-002", "nombre": "José Martínez", "cargo": "Albañil", "activo": True},
        {"id": "trab-003", "nombre": "Miguel Torres", "cargo": "Ayudante general", "activo": True},
        {"id": "trab-004", "nombre": "Pedro Gómez", "cargo": "Herrero", "activo": True},
        {"id": "trab-005", "nombre": "Luis Hernández", "cargo": "Electricista", "activo": True},
        {"id": "trab-006", "nombre": "Andrés López", "cargo": "Plomero", "activo": True},
        {"id": "trab-007", "nombre": "Roberto Díaz", "cargo": "Carpintero", "activo": True},
        {"id": "trab-008", "nombre": "Fernando Vargas", "cargo": "Pintor", "activo": True},
        {"id": "trab-009", "nombre": "Diego Morales", "cargo": "Ayudante general", "activo": True},
        {"id": "trab-010", "nombre": "Javier Castillo", "cargo": "Operador de maquinaria", "activo": True},
        {"id": "trab-011", "nombre": "Raúl Peña", "cargo": "Maestro de obra", "activo": True},
        {"id": "trab-012", "nombre": "Sandra Muñoz", "cargo": "Auxiliar de obra", "activo": True},
        {"id": "trab-013", "nombre": "Nicolás Ríos", "cargo": "Ayudante", "activo": False},
        {"id": "trab-014", "nombre": "Carmen Flores", "cargo": "Oficial de obra", "activo": True},
    ]


_FILLERS = {
    "config": _fill_config,
    "usuarios": _fill_usuarios,
    "actividades": _fill_actividades,
    "avances": _fill_avances,
    "tareas": _fill_tareas,
    "control_inventario": _fill_inventario,
    "proveedores": _fill_proveedores,
    "control_maquinas": _fill_maquinas,
    "asistencia": _fill_asistencia,
    "nomina": _fill_nomina,
    "materiales": _fill_materiales,
    "trabajadores": _fill_trabajadores,
}