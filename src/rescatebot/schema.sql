-- Esquema del prototipo (SQLite). Misma estructura y reglas que rescatebot.sql (PostgreSQL).
PRAGMA foreign_keys = ON;
CREATE TABLE usuario (
  id_usuario INTEGER PRIMARY KEY AUTOINCREMENT,
  nombre TEXT NOT NULL,
  correo TEXT NOT NULL UNIQUE,
  rol TEXT NOT NULL DEFAULT 'operador' CHECK (rol IN ('operador','supervisor','administrador')),
  clave_hash TEXT NOT NULL,
  intentos_fallidos INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE robot (
  id_robot INTEGER PRIMARY KEY AUTOINCREMENT,
  codigo TEXT NOT NULL UNIQUE CHECK (codigo GLOB 'ROB-[0-9][0-9][0-9]'),
  modelo TEXT NOT NULL
);
CREATE TABLE sesion (
  id_sesion INTEGER PRIMARY KEY AUTOINCREMENT,
  id_usuario INTEGER NOT NULL REFERENCES usuario(id_usuario),
  id_robot INTEGER NOT NULL REFERENCES robot(id_robot),
  escenario TEXT NOT NULL CHECK (length(trim(escenario)) >= 3),
  inicio TEXT NOT NULL DEFAULT (datetime('now','localtime')),
  fin TEXT
);
CREATE UNIQUE INDEX ux_sesion_activa_por_robot ON sesion(id_robot) WHERE fin IS NULL;
CREATE TABLE lectura (
  id_lectura INTEGER PRIMARY KEY AUTOINCREMENT,
  id_sesion INTEGER NOT NULL REFERENCES sesion(id_sesion) ON DELETE CASCADE,
  variable TEXT NOT NULL CHECK (variable IN ('distancia','temp_objeto','gas_rel','bateria')),
  valor REAL,
  unidad TEXT NOT NULL,
  valida INTEGER NOT NULL CHECK (valida = (valor IS NOT NULL)),
  fecha_hora TEXT NOT NULL DEFAULT (datetime('now','localtime'))
);
CREATE TABLE deteccion (
  id_deteccion INTEGER PRIMARY KEY AUTOINCREMENT,
  id_sesion INTEGER NOT NULL REFERENCES sesion(id_sesion) ON DELETE CASCADE,
  nro_cuadro INTEGER NOT NULL CHECK (nro_cuadro >= 0),
  confianza REAL NOT NULL CHECK (confianza BETWEEN 0 AND 1),
  sector TEXT,
  decision TEXT NOT NULL DEFAULT 'pendiente' CHECK (decision IN ('pendiente','confirmado','descartado','no_concluyente')),
  revisado_por INTEGER REFERENCES usuario(id_usuario),
  CHECK (decision = 'pendiente' OR revisado_por IS NOT NULL)
);
CREATE TABLE alerta (
  id_alerta INTEGER PRIMARY KEY AUTOINCREMENT,
  id_sesion INTEGER NOT NULL REFERENCES sesion(id_sesion) ON DELETE CASCADE,
  origen TEXT NOT NULL CHECK (origen IN ('ambiental','tecnica','visual')),
  descripcion TEXT NOT NULL,
  fecha_hora TEXT NOT NULL DEFAULT (datetime('now','localtime'))
);
