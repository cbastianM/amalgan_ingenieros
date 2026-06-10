CREATE TABLE IF NOT EXISTS config (
    id SERIAL PRIMARY KEY,
    proyecto VARCHAR UNIQUE NOT NULL,
    total_costo_directo NUMERIC DEFAULT 0,
    total_costo_suministros NUMERIC DEFAULT 0,
    costo_total_obra NUMERIC DEFAULT 0,
    costo_total_proyecto NUMERIC DEFAULT 0
);

CREATE TABLE IF NOT EXISTS usuarios (
    id SERIAL PRIMARY KEY,
    usuario VARCHAR UNIQUE NOT NULL,
    clave VARCHAR NOT NULL,
    rol VARCHAR NOT NULL,
    activo BOOLEAN DEFAULT TRUE,
    nombre_visible VARCHAR,
    foto_perfil TEXT,
    email VARCHAR
);

CREATE TABLE IF NOT EXISTS actividades (
    id SERIAL PRIMARY KEY,
    codigo VARCHAR UNIQUE NOT NULL,
    componente VARCHAR,
    capitulo VARCHAR,
    descripcion TEXT,
    unidad VARCHAR,
    cantidad_total NUMERIC DEFAULT 0,
    valor_unitario NUMERIC DEFAULT 0,
    valor_total NUMERIC DEFAULT 0
);

CREATE TABLE IF NOT EXISTS avances (
    id SERIAL PRIMARY KEY,
    proyecto VARCHAR NOT NULL,
    fecha DATE,
    id_item VARCHAR NOT NULL,
    cantidad NUMERIC DEFAULT 0,
    usuario VARCHAR,
    timestamp TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS tareas (
    id SERIAL PRIMARY KEY,
    id_tarea VARCHAR NOT NULL,
    proyecto VARCHAR NOT NULL,
    descripcion TEXT,
    fecha_limite DATE,
    prioridad VARCHAR DEFAULT 'Media',
    estado VARCHAR DEFAULT 'Pendiente',
    asignado_a VARCHAR,
    notas TEXT,
    creado_por VARCHAR,
    timestamp TIMESTAMP DEFAULT NOW(),
    UNIQUE(proyecto, id_tarea)
);

CREATE TABLE IF NOT EXISTS control_inventario (
    id SERIAL PRIMARY KEY,
    proyecto VARCHAR NOT NULL,
    fecha DATE,
    hora TIME,
    tipo_movimiento VARCHAR,
    material VARCHAR,
    cantidad NUMERIC DEFAULT 0,
    unidad VARCHAR,
    responsable VARCHAR,
    observaciones TEXT,
    usuario VARCHAR,
    timestamp TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS proveedores (
    id SERIAL PRIMARY KEY,
    nit VARCHAR UNIQUE,
    nombre VARCHAR,
    contacto VARCHAR,
    telefono VARCHAR,
    categoria VARCHAR,
    direccion TEXT,
    notas TEXT
);

CREATE TABLE IF NOT EXISTS control_maquinas (
    id SERIAL PRIMARY KEY,
    proyecto VARCHAR NOT NULL,
    fecha DATE,
    tipo_equipo VARCHAR,
    placa VARCHAR,
    operador VARCHAR,
    hora_inicio TIME,
    hora_fin TIME,
    horas_trabajadas NUMERIC DEFAULT 0,
    material_transportado VARCHAR,
    volumen_m3 NUMERIC DEFAULT 0,
    numero_viajes INTEGER DEFAULT 0,
    observaciones TEXT,
    usuario VARCHAR,
    timestamp TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS asistencia (
    id SERIAL PRIMARY KEY,
    proyecto VARCHAR NOT NULL,
    fecha DATE,
    trabajador VARCHAR,
    cargo VARCHAR,
    estado VARCHAR,
    usuario VARCHAR
);

CREATE TABLE IF NOT EXISTS nomina (
    id SERIAL PRIMARY KEY,
    proyecto VARCHAR NOT NULL,
    fecha DATE,
    trabajador VARCHAR,
    tipo VARCHAR,
    valor NUMERIC DEFAULT 0,
    notas TEXT
);

CREATE TABLE IF NOT EXISTS materiales (
    id SERIAL PRIMARY KEY,
    proyecto VARCHAR NOT NULL,
    fecha DATE,
    material VARCHAR,
    cantidad NUMERIC DEFAULT 0,
    unidad VARCHAR,
    requerimiento TEXT,
    estado VARCHAR DEFAULT 'Solicitado',
    usuario VARCHAR
);

CREATE TABLE IF NOT EXISTS trabajadores (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR,
    cargo VARCHAR,
    activo BOOLEAN DEFAULT TRUE,
    email VARCHAR
);
