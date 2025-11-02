CREATE TABLE IF NOT EXISTS empresas (
    id SERIAL PRIMARY KEY,
    razon_social VARCHAR(255) NOT NULL,
    cuit VARCHAR(13) NOT NULL UNIQUE,
    activa BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS convenios (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(255) NOT NULL,
    codigo VARCHAR(50) NOT NULL UNIQUE,
    descripcion TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS conceptos (
    id SERIAL PRIMARY KEY,
    codigo VARCHAR(50) NOT NULL UNIQUE,
    nombre VARCHAR(255) NOT NULL,
    tipo VARCHAR(20) NOT NULL CHECK (tipo IN ('remunerativo', 'no_remunerativo', 'deduccion')),
    es_comun BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS empleados (
    id SERIAL PRIMARY KEY,
    empresa_id INTEGER REFERENCES empresas(id),
    convenio_id INTEGER REFERENCES convenios(id),
    cuil VARCHAR(13) NOT NULL,
    nombre VARCHAR(100) NOT NULL,
    apellido VARCHAR(100) NOT NULL,
    legajo VARCHAR(50),
    cbu VARCHAR(22),
    fecha_ingreso DATE,
    activo BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(empresa_id, cuil)
);

CREATE TABLE IF NOT EXISTS liquidaciones (
    id SERIAL PRIMARY KEY,
    empresa_id INTEGER REFERENCES empresas(id),
    empleado_id INTEGER REFERENCES empleados(id),
    periodo VARCHAR(7) NOT NULL,
    estado VARCHAR(20) NOT NULL CHECK (estado IN ('pendiente', 'procesando', 'completada', 'error')),
    sueldo_bruto DECIMAL(12,2),
    sueldo_neto DECIMAL(12,2),
    cargas_sociales DECIMAL(12,2),
    procesado_por VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS tareas (
    id SERIAL PRIMARY KEY,
    tipo VARCHAR(50) NOT NULL,
    payload JSONB NOT NULL,
    estado VARCHAR(20) NOT NULL CHECK (estado IN ('pendiente', 'procesando', 'completada', 'error')),
    resultado JSONB,
    error_mensaje TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_liquidaciones_empresa ON liquidaciones(empresa_id);
CREATE INDEX idx_liquidaciones_periodo ON liquidaciones(periodo);
CREATE INDEX idx_empleados_empresa ON empleados(empresa_id);
CREATE INDEX idx_tareas_estado ON tareas(estado);

INSERT INTO convenios (nombre, codigo, descripcion) VALUES
    ('Comercio', 'CCT130', 'Convenio Colectivo de Trabajo 130/75 - Empleados de Comercio'),
    ('Metalurgico', 'CCT260', 'Convenio Colectivo de Trabajo 260/75 - Metalurgicos'),
    ('Construccion', 'CCT076', 'Convenio Colectivo de Trabajo 76/75 - Construccion');

INSERT INTO conceptos (codigo, nombre, tipo, es_comun) VALUES
    ('00001', 'Sueldo Basico', 'remunerativo', true),
    ('000100', 'Antiguedad', 'remunerativo', true),
    ('000200', 'Presentismo', 'remunerativo', true),
    ('00300', 'Horas Extra 50%', 'remunerativo', true),
    ('010000', 'Sueldo Anual Complementario', 'remunerativo', true),
    ('03000', 'Jubilacion 11%', 'deduccion', true),
    ('03002', 'Ley 19032 3%', 'deduccion', true),
    ('03010', 'Obra Social 3%', 'deduccion', true),
    ('03500', 'Aporte Sindical 2.5%', 'deduccion', false);