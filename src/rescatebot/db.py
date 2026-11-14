"""Acceso a la base de datos SQLite del prototipo."""
import sqlite3
from pathlib import Path
from flask import current_app, g
from werkzeug.security import generate_password_hash

ESQUEMA = Path(__file__).with_name("schema.sql")


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(_exc=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    """Crea las tablas y carga datos de demostración (ficticios)."""
    db = get_db()
    db.executescript(ESQUEMA.read_text(encoding="utf-8"))
    usuarios = [
        ("Operador Demo", "operador@rescatebot.bo", "operador", "Operador123"),
        ("Supervisor Demo", "supervisor@rescatebot.bo", "supervisor", "Supervisor123"),
    ]
    for nombre, correo, rol, clave in usuarios:
        db.execute(
            "INSERT INTO usuario (nombre, correo, rol, clave_hash) VALUES (?,?,?,?)",
            (nombre, correo, rol, generate_password_hash(clave, method="pbkdf2:sha256")),
        )
    db.execute("INSERT INTO robot (codigo, modelo) VALUES ('ROB-001','Chasis 4WD + ESP32 + ESP32-CAM')")
    db.execute("INSERT INTO robot (codigo, modelo) VALUES ('ROB-002','Chasis 2WD de pruebas')")
    db.commit()
