import sys, os, random, uuid
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

import psycopg2
from datetime import date, timedelta
today = date.today()

PROYECTOS = ["Edificio Colombo Americana", "Torres del Parque", "Centro Comercial Los Alpes"]
def _d(offset=0): return (today - timedelta(days=offset)).isoformat()

def get_conn():
    try:
        import streamlit as st
        url = st.secrets["database"]["DATABASE_URL"]
    except Exception:
        try:
            import tomllib
            path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".streamlit", "secrets.toml")
            with open(path, "rb") as f:
                cfg = tomllib.load(f)
            url = cfg["database"]["DATABASE_URL"]
        except Exception:
            url = input("DATABASE_URL: ").strip()
    return psycopg2.connect(url)

def run_schema(cur):
    schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
    with open(schema_path, "r", encoding="utf-8") as f:
        cur.execute(f.read())
    print("Schema OK")

def seed_usuarios(cur):
    rows = [
        ("director1","1234","Director",True,"Carlos Mendoza",None,"carlos.mendoza@almagan.com"),
        ("residente1","1234","Residente",True,"Ana Lopez",None,"ana.lopez@almagan.com"),
        ("almacenista1","1234","Almacenista",True,"Pedro Gomez",None,"pedro.gomez@almagan.com"),
        ("controlador1","1234","Controlador",True,"Luis Ramirez",None,"luis.ramirez@almagan.com"),
    ]
    for r in rows:
        cur.execute("INSERT INTO usuarios (usuario,clave,rol,activo,nombre_visible,foto_perfil,email) VALUES (%s,%s,%s,%s,%s,%s,%s) ON CONFLICT (usuario) DO NOTHING", r)
    print(f"  {len(rows)} usuarios")

def seed_trabajadores(cur):
    rows = [
        ("Carlos Ramirez","Maestro de obra",True,"carlos.ramirez@almagan.com"),
        ("Jose Martinez","Albanil",True,"jose.martinez@almagan.com"),
        ("Miguel Torres","Ayudante general",True,"miguel.torres@almagan.com"),
        ("Pedro Gomez","Herrero",True,"pedro.gomez@almagan.com"),
        ("Luis Hernandez","Electricista",True,"luis.hernandez@almagan.com"),
        ("Andres Lopez","Plomero",True,"andres.lopez@almagan.com"),
        ("Roberto Diaz","Carpintero",True,"roberto.diaz@almagan.com"),
        ("Fernando Vargas","Pintor",True,"fernando.vargas@almagan.com"),
        ("Diego Morales","Ayudante general",True,"diego.morales@almagan.com"),
        ("Javier Castillo","Operador de maquinaria",True,"javier.castillo@almagan.com"),
        ("Raul Pena","Maestro de obra",True,"raul.pena@almagan.com"),
        ("Sandra Munoz","Auxiliar de obra",True,"sandra.munoz@almagan.com"),
        ("Nicolas Rios","Ayudante",False,"nicolas.rios@almagan.com"),
        ("Carmen Flores","Oficial de obra",True,"carmen.flores@almagan.com"),
    ]
    for r in rows:
        cur.execute("INSERT INTO trabajadores (nombre,cargo,activo,email) VALUES (%s,%s,%s,%s) ON CONFLICT DO NOTHING", r)
    print(f"  {len(rows)} trabajadores")

def seed_actividades(cur):
    rows = [
        ("1.1.01","OBRA CIVIL","CIMENTACION","Excavacion para cimentacion","m3",450,28500,12825000),
        ("1.1.02","OBRA CIVIL","CIMENTACION","Relleno y compactacion","m3",280,18500,5180000),
        ("1.1.03","OBRA CIVIL","CIMENTACION","Concreto de cimentacion fc=3000 psi","m3",180,485000,87300000),
        ("1.1.04","OBRA CIVIL","CIMENTACION","Acero de refuerzo cimentacion","kg",12500,4200,52500000),
        ("1.2.01","OBRA CIVIL","ESTRUCTURA","Concreto columnas fc=4000 psi","m3",320,520000,166400000),
        ("1.2.02","OBRA CIVIL","ESTRUCTURA","Acero de refuerzo columnas","kg",28000,4300,120400000),
        ("1.2.03","OBRA CIVIL","ESTRUCTURA","Concreto vigas y losas fc=3000 psi","m3",540,495000,267300000),
        ("1.2.04","OBRA CIVIL","ESTRUCTURA","Encofrado columnas y vigas","m2",3800,35000,133000000),
        ("2.1.01","MAMPOSTERIA","DIVISIONES","Muro en bloque ceramico e=10cm","m2",2500,58000,145000000),
        ("2.1.02","MAMPOSTERIA","DIVISIONES","Muro en bloque ceramico e=15cm","m2",1800,72000,129600000),
        ("2.2.01","MAMPOSTERIA","REVESTIMIENTOS","Estuco interior muros","m2",3200,18500,59200000),
        ("2.2.02","MAMPOSTERIA","REVESTIMIENTOS","Estuco exterior fachada","m2",1600,22000,35200000),
        ("3.1.01","INSTALACIONES","ELECTRICA","Instalacion red electrica provisional","gl",1,12500000,12500000),
        ("3.1.02","INSTALACIONES","ELECTRICA","Instalacion red electrica definitiva","gl",1,89000000,89000000),
        ("3.2.01","INSTALACIONES","HIDRAULICA","Instalacion red hidraulica","gl",1,65000000,65000000),
        ("3.2.02","INSTALACIONES","HIDRAULICA","Instalacion red sanitaria","gl",1,58000000,58000000),
        ("4.1.01","ACABADOS","PISOS","Piso ceramico interior 60x60","m2",3500,68000,238000000),
        ("4.1.02","ACABADOS","PISOS","Piso porcelanato zonas comunes","m2",800,95000,76000000),
        ("4.2.01","ACABADOS","PINTURA","Pintura interior vinilo 2 manos","m2",4800,12000,57600000),
        ("4.2.02","ACABADOS","PINTURA","Pintura exterior impermeabilizante","m2",1800,18000,32400000),
    ]
    for r in rows:
        cur.execute("INSERT INTO actividades (codigo,componente,capitulo,descripcion,unidad,cantidad_total,valor_unitario,valor_total) VALUES (%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT (codigo) DO NOTHING", r)
    print(f"  {len(rows)} actividades")

def seed_proveedores(cur):
    rows = [
        ("900123456-1","Cementos Argos S.A.","Andres Bermudez","3104567890","Materiales","Cra 54 #72-120, Medellin","Proveedor principal de cemento gris"),
        ("900987654-2","Aceros Paz del Rio","Maria Lopez","3156789012","Acero","Calle 80 #15-40, Bogota","Varilla y acero estructural"),
        ("800456789-3","Concretos del Caribe","Jorge Pardo","3001234567","Concreto","Via 40 #58-30, Barranquilla","Concreto premezclado fc=3000 y 4000 psi"),
        ("900345678-4","Ferreteria Industrial El Puerto","Ana Gomez","3215678901","Ferreteria","Calle 35 #20-15, Cartagena","Herramientas y ferreteria general"),
        ("900567890-5","Transportes Rapidos S.A.","Hugo Castillo","3109876543","Transporte","Cra 10 #45-60, Barranquilla","Volquetas y transporte de materiales"),
        ("900678901-6","Electro Materiales Caribe","Patricia Ruiz","3204561234","Servicios","Calle 52 #30-18, Barranquilla","Material electrico y cableado"),
        ("900789012-7","Ladrillera Santander","Felipe Ortega","3112345678","Materiales","Km 5 Via Barbosa, Bucaramanga","Ladrillo ceramico y bloque estructural"),
        ("900890123-8","Equipos del Atlantico","Raul Mercado","3158765432","Equipos","Zona Industrial Mamonal, Cartagena","Alquiler de maquinaria pesada"),
    ]
    for r in rows:
        cur.execute("INSERT INTO proveedores (nit,nombre,contacto,telefono,categoria,direccion,notas) VALUES (%s,%s,%s,%s,%s,%s,%s) ON CONFLICT (nit) DO NOTHING", r)
    print(f"  {len(rows)} proveedores")

def seed_config(cur):
    rows = [
        ("Edificio Colombo Americana",1450000000,320000000,1770000000,2100000000),
        ("Torres del Parque",2100000000,480000000,2580000000,3000000000),
        ("Centro Comercial Los Alpes",3200000000,650000000,3850000000,4500000000),
    ]
    for r in rows:
        cur.execute("INSERT INTO config (proyecto,total_costo_directo,total_costo_suministros,costo_total_obra,costo_total_proyecto) VALUES (%s,%s,%s,%s,%s) ON CONFLICT (proyecto) DO NOTHING", r)
    print(f"  {len(rows)} configuraciones de proyecto")

def seed_avances(cur):
    avances_config = [
        ("Edificio Colombo Americana", [0.90,0.85,0.70,0.75,0.45,0.35,0.25,0.15,0.10,0.05,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0]),
        ("Torres del Parque",          [0.15,0.10,0.05,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0]),
        ("Centro Comercial Los Alpes", [1.0,1.0,1.0,1.0,0.95,0.80,0.75,0.70,0.60,0.55,0.50,0.40,0.90,0.85,0.80,0.75,0.30,0.20,0.15,0.10]),
    ]
    codigos = ["1.1.01","1.1.02","1.1.03","1.1.04","1.2.01","1.2.02","1.2.03","1.2.04",
               "2.1.01","2.1.02","2.2.01","2.2.02","3.1.01","3.1.02","3.2.01","3.2.02",
               "4.1.01","4.1.02","4.2.01","4.2.02"]
    totales = {"1.1.01":450,"1.1.02":280,"1.1.03":180,"1.1.04":12500,"1.2.01":320,"1.2.02":28000,"1.2.03":540,"1.2.04":3800,
               "2.1.01":2500,"2.1.02":1800,"2.2.01":3200,"2.2.02":1600,"3.1.01":1,"3.1.02":1,"3.2.01":1,"3.2.02":1,
               "4.1.01":3500,"4.1.02":800,"4.2.01":4800,"4.2.02":1800}
    count = 0
    for proyecto, pcts in avances_config:
        for i, aid in enumerate(codigos):
            p = pcts[i]
            if p > 0:
                total = totales[aid]
                cant = round(total * p, 1)
                hist_dias = [45,30,25,20,18,15,12,10,8,5,3,2,30,25,20,15,10,5,3,1]
                dia = hist_dias[i]
                cur.execute(
                    "INSERT INTO avances (proyecto,fecha,id_item,cantidad,usuario,timestamp) VALUES (%s,%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING",
                    (proyecto, _d(dia), aid, cant, "director1", _d(dia)+"T08:00:00")
                )
                count += 1
    print(f"  {count} avances (entre 3 proyectos)")

def seed_tareas(cur):
    todos = [
        ("T-001","Edificio Colombo Americana","Revision de planos estructurales Piso 5",_d(-4),"Alta","En progreso","director1","Priorizar revision de cargas sismicas","director1"),
        ("T-002","Edificio Colombo Americana","Pedir cotizacion de acero para vigas",_d(-1),"Alta","Pendiente","residente1","Minimo 3 cotizaciones formales","director1"),
        ("T-003","Edificio Colombo Americana","Coordinar entrega de concreto Piso 4",_d(2),"Media","Completada","residente1","Concretos del Caribe confirmado","director1"),
        ("T-004","Edificio Colombo Americana","Inspeccion de soldadura columnas P3",_d(-7),"Alta","Pendiente","director1","Curaduria requiere firma de inspeccion","director1"),
        ("T-005","Edificio Colombo Americana","Levantamiento topografico lote norte",_d(-2),"Media","En progreso","residente1","","director1"),
        ("T-006","Edificio Colombo Americana","Revision instalaciones electricas Piso 3",_d(-10),"Media","Pendiente","director1","Esperando planos actualizados de diseno","director1"),
        ("T-007","Edificio Colombo Americana","Verificacion de niveles losa entrepiso P4",_d(-5),"Baja","Pendiente","residente1","","director1"),
        ("T-008","Edificio Colombo Americana","Cotizar materiales de acabados pisos",_d(-14),"Baja","Pendiente","residente1","Incluir porcelanato y ceramica 60x60","director1"),
        ("T-001","Torres del Parque","Solicitar permiso de construccion ante Curaduria",_d(-30),"Alta","En progreso","director1","Documentos completos faltan 2 firmas","director1"),
        ("T-002","Torres del Parque","Estudio de suelos lote A-1",_d(-15),"Alta","Pendiente","residente1","Contratar laboratorio certificado","director1"),
        ("T-003","Torres del Parque","Cerramiento perimetral del lote",_d(-8),"Media","Pendiente","residente1","Presupuesto aprobado, iniciar tramite","director1"),
        ("T-004","Torres del Parque","Contratacion maestro de obra general",_d(-5),"Alta","En progreso","director1","Entrevistas programadas esta semana","director1"),
        ("T-005","Torres del Parque","Solicitar conexion provisional de servicios",_d(-20),"Media","Pendiente","residente1","Agua, luz y alcantarillado","director1"),
        ("T-006","Torres del Parque","Compra de poliza Todo Riesgo Construccion",_d(-10),"Alta","Completada","director1","Poliza emitida por Seguros Bolivar","director1"),
        ("T-001","Centro Comercial Los Alpes","Recibo final de obra civil estructura",_d(-3),"Alta","En progreso","director1","Acta de entrega pendiente de firma interventoria","director1"),
        ("T-002","Centro Comercial Los Alpes","Pruebas hidraulicas red contra incendios",_d(-5),"Alta","Pendiente","residente1","Coordinado con Bomberos para inspeccion","director1"),
        ("T-003","Centro Comercial Los Alpes","Instalacion de ascensores torre B",_d(-15),"Media","En progreso","residente1","Equipos Otis en importacion","director1"),
        ("T-004","Centro Comercial Los Alpes","Pintura zonas comunes Piso 2",_d(-7),"Media","Completada","residente1","","director1"),
        ("T-005","Centro Comercial Los Alpes","Instalacion luminarias parqueaderos",_d(-20),"Media","Pendiente","director1","Pedido de 250 luminarias LED a proveedor","director1"),
        ("T-006","Centro Comercial Los Alpes","Entrega locales comerciales fase 1",_d(-30),"Alta","Pendiente","director1","12 locales para entrega a propietarios","director1"),
        ("T-007","Centro Comercial Los Alpes","Pruebas de carga red electrica general",_d(-10),"Baja","Pendiente","residente1","","director1"),
        ("T-008","Centro Comercial Los Alpes","Siembra de zonas verdes y jardineria",_d(-25),"Baja","Pendiente","residente1","Cotizar 200 arboles y 500 arbustos","director1"),
    ]
    for (tid,p,desc,flim,pri,est,asig,notas,creado) in todos:
        cur.execute(
            "INSERT INTO tareas (id_tarea,proyecto,descripcion,fecha_limite,prioridad,estado,asignado_a,notas,creado_por,timestamp) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,NOW()) ON CONFLICT (proyecto, id_tarea) DO NOTHING",
            (tid,p,desc,flim,pri,est,asig,notas,creado)
        )
    print(f"  {len(todos)} tareas (entre 3 proyectos)")

def seed_inventario(cur):
    movs = [
        ("Edificio Colombo Americana",_d(7),"07:30:00","Entrada","Cemento Gris Portland Tipo I",200,"bultos","Carlos Ramirez","Entrega Cementos Argos - Pedido #A-4521","director1"),
        ("Edificio Colombo Americana",_d(7),"08:15:00","Entrada","Arena Lavada Granulada",15,"m3","Carlos Ramirez","Volqueta 3 cargas cantera El Cerro","director1"),
        ("Edificio Colombo Americana",_d(6),"07:45:00","Entrada","Varilla de Acero Corrugada 1/2\"",350,"varillas","Jose Martinez","Aceros Paz del Rio - factura F-8821","director1"),
        ("Edificio Colombo Americana",_d(6),"09:00:00","Entrada","Grava de 3/4 Pulgada",12,"m3","Jose Martinez","","director1"),
        ("Edificio Colombo Americana",_d(5),"10:30:00","Salida","Cemento Gris Portland Tipo I",80,"bultos","Miguel Torres","Vaciado viga Piso 4 eje B-C","director1"),
        ("Edificio Colombo Americana",_d(5),"11:00:00","Salida","Arena Lavada Granulada",5,"m3","Miguel Torres","Mezcla para columnas Piso 3","director1"),
        ("Edificio Colombo Americana",_d(3),"07:20:00","Entrada","Bloque Ceramico Estructural 15x20x30 cm",5000,"unidades","Carlos Ramirez","Ladrillera Santander - guia G-334","director1"),
        ("Edificio Colombo Americana",_d(2),"14:00:00","Salida","Cemento Gris Portland Tipo I",50,"bultos","Pedro Gomez","Muros Piso 3","director1"),
        ("Edificio Colombo Americana",_d(1),"07:00:00","Entrada","Piedra de Relleno",10,"m3","Carlos Ramirez","Para relleno zona sur","director1"),
        ("Edificio Colombo Americana",_d(1),"13:00:00","Salida","Varilla de Acero Corrugada 1/2\"",120,"varillas","Pedro Gomez","Refuerzo columnas P5","director1"),
        ("Edificio Colombo Americana",_d(0),"07:15:00","Entrada","Cemento Gris Portland Tipo I",150,"bultos","Carlos Ramirez","Pedido urgente - losa entrepiso","director1"),
        ("Edificio Colombo Americana",_d(0),"08:30:00","Entrada","Arena Lavada Granulada",8,"m3","Diego Morales","","director1"),
        ("Torres del Parque",_d(45),"08:00:00","Entrada","Cemento Gris Portland Tipo I",50,"bultos","Raul Pena","Inicio de obra - materiales basicos","director1"),
        ("Torres del Parque",_d(40),"07:30:00","Entrada","Malla Electrosoldada 6x6 calibre 10/10",4,"rollos","Raul Pena","","director1"),
        ("Torres del Parque",_d(35),"09:00:00","Salida","Cemento Gris Portland Tipo I",20,"bultos","Carmen Flores","Cimentacion perimetral lote","director1"),
        ("Torres del Parque",_d(15),"10:00:00","Entrada","Tubo PVC Sanitario 3 pulgadas",50,"tubos","Diego Morales","Instalaciones preliminares","director1"),
        ("Centro Comercial Los Alpes",_d(90),"06:30:00","Entrada","Piso Ceramico Interior 60x60 cm",1200,"m2","Carlos Ramirez","Corona - entrega programada","controlador1"),
        ("Centro Comercial Los Alpes",_d(85),"07:00:00","Entrada","Porcelanato Zonas Comunes 80x80 cm",400,"m2","Carlos Ramirez","Alfa - zonas comunes P1 y P2","controlador1"),
        ("Centro Comercial Los Alpes",_d(80),"14:00:00","Salida","Pintura Vinilo Interior Dos Manos",80,"galones","Fernando Vargas","Pintura locales comerciales","director1"),
        ("Centro Comercial Los Alpes",_d(60),"08:00:00","Entrada","Estuco Interior para Muros",200,"bultos","Carlos Ramirez","Acabados torre A","director1"),
        ("Centro Comercial Los Alpes",_d(30),"10:00:00","Entrada","Cable Electrico THW Calibre 10",500,"m","Diego Morales","Red electrica parqueaderos","controlador1"),
        ("Centro Comercial Los Alpes",_d(10),"09:30:00","Salida","Pintura Impermeabilizante Exterior",60,"galones","Fernando Vargas","Fachada principal","director1"),
    ]
    for (proj,fecha,hora,tipo,mat,cant,unid,resp,obs,usr) in movs:
        cur.execute(
            "INSERT INTO control_inventario (proyecto,fecha,hora,tipo_movimiento,material,cantidad,unidad,responsable,observaciones,usuario,timestamp) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,NOW()) ON CONFLICT DO NOTHING",
            (proj,fecha,hora,tipo,mat,cant,unid,resp,obs,usr)
        )
    print(f"  {len(movs)} movimientos de inventario (entre 3 proyectos)")

def seed_maquinas(cur):
    regs = [
        ("Edificio Colombo Americana",_d(5),"Volqueta","ZTX-421","Javier Castillo","06:30","16:30",10.0,"Arena",18.0,6,"3 cargas cantera El Cerro","controlador1"),
        ("Edificio Colombo Americana",_d(5),"Retroexcavadora","KLM-890","Raul Pena","07:00","17:00",10.0,None,0,0,"Excavacion zona norte cimentacion","controlador1"),
        ("Edificio Colombo Americana",_d(4),"Volqueta","BQR-156","Diego Morales","06:00","14:00",8.0,"Gravilla",24.0,8,"Concreto Piso 4","controlador1"),
        ("Edificio Colombo Americana",_d(4),"Grua","GHI-789","Roberto Diaz","07:00","15:30",8.5,None,0,0,"Izaje vigas metalicas Piso 5","controlador1"),
        ("Edificio Colombo Americana",_d(3),"Volqueta","ZTX-421","Javier Castillo","06:30","15:30",9.0,"Tierra",27.0,9,"Retiro escombros zona este","controlador1"),
        ("Edificio Colombo Americana",_d(3),"Mototrac","MNC-234","Raul Pena","07:00","12:00",5.0,None,0,0,"Compactacion terreno","controlador1"),
        ("Edificio Colombo Americana",_d(1),"Retroexcavadora","KLM-890","Raul Pena","07:00","16:00",9.0,None,0,0,"Zanja redes hidraulicas","controlador1"),
        ("Edificio Colombo Americana",_d(1),"Volqueta","BQR-156","Diego Morales","06:00","14:00",8.0,"Piedra",15.0,5,"Material para relleno","controlador1"),
        ("Torres del Parque",_d(40),"Retroexcavadora","KLM-890","Raul Pena","07:00","16:00",9.0,None,0,0,"Desmonte y limpieza lote","controlador1"),
        ("Torres del Parque",_d(38),"Volqueta","BQR-156","Diego Morales","06:00","13:00",7.0,"Tierra vegetal",21.0,7,"Retiro capa vegetal","controlador1"),
        ("Centro Comercial Los Alpes",_d(60),"Grua","GHI-789","Roberto Diaz","07:00","17:00",10.0,None,0,0,"Montaje estructura metalica cubierta","controlador1"),
        ("Centro Comercial Los Alpes",_d(55),"Mixer","ABC-123","Carlos Ramirez","08:00","16:00",8.0,"Concreto Premezclado",32.0,4,"Vaciado losa parqueaderos","controlador1"),
        ("Centro Comercial Los Alpes",_d(30),"Compactador","CMP-456","Raul Pena","06:00","11:00",5.0,None,0,0,"Compactacion vias internas","controlador1"),
        ("Centro Comercial Los Alpes",_d(7),"Volqueta","ZTX-421","Javier Castillo","06:00","15:00",9.0,"Escombros",30.0,10,"Retiro final escombros","controlador1"),
    ]
    for (proj,fecha,tipo,placa,oper,hi,hf,ht,mat,vol,viajes,obs,usr) in regs:
        cur.execute(
            "INSERT INTO control_maquinas (proyecto,fecha,tipo_equipo,placa,operador,hora_inicio,hora_fin,horas_trabajadas,material_transportado,volumen_m3,numero_viajes,observaciones,usuario,timestamp) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,NOW()) ON CONFLICT DO NOTHING",
            (proj,fecha,tipo,placa,oper,hi,hf,ht,mat,vol,viajes,obs,usr)
        )
    print(f"  {len(regs)} registros de maquinas (entre 3 proyectos)")

def seed_asistencia(cur):
    trabajadores_asis = [
        ("Carlos Ramirez","Maestro de obra"),("Jose Martinez","Albanil"),("Miguel Torres","Ayudante general"),
        ("Pedro Gomez","Herrero"),("Luis Hernandez","Electricista"),("Andres Lopez","Plomero"),
        ("Roberto Diaz","Carpintero"),("Fernando Vargas","Pintor"),("Diego Morales","Ayudante general"),
        ("Javier Castillo","Operador"),("Raul Pena","Maestro de obra"),("Sandra Munoz","Auxiliar"),
    ]
    for proyecto in PROYECTOS:
        if proyecto == "Torres del Parque":
            dias = 7
        elif proyecto == "Centro Comercial Los Alpes":
            dias = 30
        else:
            dias = 15
        for d in range(dias):
            fecha = _d(d)
            for nombre, cargo in trabajadores_asis:
                if proyecto == "Torres del Parque" and random.random() < 0.5:
                    continue
                estado = random.choice(["Presente","Presente","Presente","Presente","Presente","Ausente","Permiso"])
                cur.execute(
                    "INSERT INTO asistencia (proyecto,fecha,trabajador,cargo,estado,usuario) VALUES (%s,%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING",
                    (proyecto,fecha,nombre,cargo,estado,"director1")
                )
    print(f"  Asistencia: 15dias x 12trab x 3proy = hasta 540 registros")

def seed_nomina(cur):
    regs = [
        ("Edificio Colombo Americana",_d(30),"Carlos Ramirez","Mensual",3200000,"Salario mes mayo"),
        ("Edificio Colombo Americana",_d(30),"Jose Martinez","Mensual",2800000,"Salario mes mayo"),
        ("Edificio Colombo Americana",_d(30),"Miguel Torres","Jornal diario",640000,"8 dias @ 80.000 - mayo"),
        ("Edificio Colombo Americana",_d(30),"Pedro Gomez","Mensual",2900000,"Salario mes mayo"),
        ("Edificio Colombo Americana",_d(30),"Luis Hernandez","Mensual",3100000,"Salario mes mayo"),
        ("Edificio Colombo Americana",_d(15),"Carlos Ramirez","Quincenal",1600000,"Quincena 1 junio"),
        ("Edificio Colombo Americana",_d(15),"Jose Martinez","Quincenal",1400000,"Quincena 1 junio"),
        ("Edificio Colombo Americana",_d(10),"Pedro Gomez","Prestamo",500000,"Prestamo personal - descuento 2 quincenas"),
        ("Edificio Colombo Americana",_d(10),"Andres Lopez","Quincenal",1350000,"Quincena 1 junio"),
        ("Edificio Colombo Americana",_d(5),"Roberto Diaz","Bonificacion",400000,"Bono productividad - avance Piso 4"),
        ("Edificio Colombo Americana",_d(3),"Fernando Vargas","Jornal diario",720000,"9 dias @ 80.000"),
        ("Edificio Colombo Americana",_d(2),"Carlos Ramirez","Quincenal",1600000,"Quincena 2 junio"),
        ("Edificio Colombo Americana",_d(2),"Pedro Gomez","Deduccion",200000,"Descuento cuota prestamo"),
        ("Torres del Parque",_d(30),"Raul Pena","Mensual",2800000,"Salario mes mayo - maestro general"),
        ("Torres del Parque",_d(30),"Carmen Flores","Mensual",1900000,"Salario mes mayo - oficial"),
        ("Torres del Parque",_d(30),"Diego Morales","Jornal diario",400000,"5 dias @ 80.000 - mayo"),
        ("Centro Comercial Los Alpes",_d(30),"Carlos Ramirez","Mensual",3500000,"Salario mes mayo + bono antiguedad"),
        ("Centro Comercial Los Alpes",_d(30),"Pedro Gomez","Mensual",3100000,"Salario mes mayo"),
        ("Centro Comercial Los Alpes",_d(30),"Fernando Vargas","Mensual",2600000,"Salario mes mayo"),
        ("Centro Comercial Los Alpes",_d(15),"Carlos Ramirez","Quincenal",1750000,"Quincena 1 junio"),
        ("Centro Comercial Los Alpes",_d(15),"Pedro Gomez","Quincenal",1550000,"Quincena 1 junio"),
        ("Centro Comercial Los Alpes",_d(15),"Sandra Munoz","Quincenal",1200000,"Quincena 1 junio"),
        ("Centro Comercial Los Alpes",_d(5),"Carlos Ramirez","Bonificacion",800000,"Bono entrega fase 1 estructura"),
        ("Centro Comercial Los Alpes",_d(2),"Pedro Gomez","Prestamo",1000000,"Prestamo calamidad domestica"),
    ]
    for (proj,fecha,trab,tipo,val,notas) in regs:
        cur.execute(
            "INSERT INTO nomina (proyecto,fecha,trabajador,tipo,valor,notas) VALUES (%s,%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING",
            (proj,fecha,trab,tipo,val,notas)
        )
    print(f"  {len(regs)} movimientos de nomina (entre 3 proyectos)")

def seed_materiales(cur):
    regs = [
        ("Edificio Colombo Americana",_d(10),"120 bultos de Cemento Tipo I para vigas Piso 5","Entregado","residente1"),
        ("Edificio Colombo Americana",_d(8),"8 m3 de Arena Lavada para acabados muros P3","En proceso","residente1"),
        ("Edificio Colombo Americana",_d(5),"300 varillas de Acero 1/2 para columnas P3","Solicitado","residente1"),
        ("Edificio Colombo Americana",_d(3),"[URGENTE] 5 m3 de Concreto fc=4000 psi para losa P4","Solicitado","director1"),
        ("Edificio Colombo Americana",_d(1),"2 rollos de Malla Electrosoldada 6x6/10-10","Solicitado","residente1"),
        ("Torres del Parque",_d(42),"100 bultos de Cemento Tipo III para cimentacion","Entregado","residente1"),
        ("Torres del Parque",_d(30),"50 m3 de Piedra de Relleno para base","En proceso","residente1"),
        ("Torres del Parque",_d(7),"1000 varillas de Acero Corrugado 5/8 para zapatas","Solicitado","director1"),
        ("Centro Comercial Los Alpes",_d(60),"800 m2 de Porcelanato 80x80 zonas comunes","Entregado","residente1"),
        ("Centro Comercial Los Alpes",_d(45),"200 galones de Pintura Vinilo Interior blanca","Entregado","residente1"),
        ("Centro Comercial Los Alpes",_d(20),"50 galones de Impermeabilizante para cubierta","En proceso","director1"),
        ("Centro Comercial Los Alpes",_d(12),"500 m de Cable THW Calibre 10 para iluminacion","Solicitado","residente1"),
        ("Centro Comercial Los Alpes",_d(5),"[URGENTE] 12 luminarias LED emergencia para escaleras","Solicitado","director1"),
    ]
    for (proj,fecha,req,estado,usr) in regs:
        cur.execute(
            "INSERT INTO materiales (proyecto,fecha,requerimiento,estado,usuario) VALUES (%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING",
            (proj,fecha,req,estado,usr)
        )
    print(f"  {len(regs)} solicitudes de materiales (entre 3 proyectos)")

def main():
    print("=" * 60)
    print("  MIGRACION ALMAGAN INGENIEROS -> Render PostgreSQL")
    print("=" * 60)
    print("\nConectando...")
    conn = get_conn()
    cur = conn.cursor()
    try:
        print("\n[1/10] Schema...")
        run_schema(cur); conn.commit()

        print("[2/10] Usuarios...")
        seed_usuarios(cur); conn.commit()

        print("[3/10] Trabajadores...")
        seed_trabajadores(cur); conn.commit()

        print("[4/10] Actividades (catalogo)...")
        seed_actividades(cur); conn.commit()

        print("[5/10] Proveedores...")
        seed_proveedores(cur); conn.commit()

        print("[6/10] Configuracion (3 proyectos)...")
        seed_config(cur); conn.commit()

        print("[7/10] Avances...")
        seed_avances(cur); conn.commit()

        print("[8/10] Tareas...")
        seed_tareas(cur); conn.commit()

        print("[9/10] Inventario + Maquinas + Asistencia + Nomina + Materiales...")
        seed_inventario(cur)
        seed_maquinas(cur)
        seed_asistencia(cur)
        seed_nomina(cur)
        seed_materiales(cur)
        conn.commit()

        print("\n" + "=" * 60)
        print("  MIGRACION COMPLETADA - 3 PROYECTOS LISTOS")
        print("  - Edificio Colombo Americana (45% avance)")
        print("  - Torres del Parque (10% avance - inicio)")
        print("  - Centro Comercial Los Alpes (75% avance)")
        print("=" * 60)
    except Exception as e:
        conn.rollback()
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    main()
