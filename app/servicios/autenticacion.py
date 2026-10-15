"""Persistencia para inicio de sesión y contraseñas."""

from contextlib import closing
import os
from pathlib import Path
import sqlite3

from app.seguridad import hashear_password

CORREO_ADMIN_DEMO = "admin@salsamentaria.com"
CORREO_VENDEDOR_DEMO = "ventas@salsamentaria.com"


def buscar_cuenta_por_email(ruta: Path, email: str) -> dict | None:
    with closing(sqlite3.connect(ruta)) as conexion:
        conexion.row_factory = sqlite3.Row
        fila = conexion.execute(
            """
            SELECT u.id_usuario, u.nombre, u.email, u.password_hash, u.activo,
                   r.nombre AS rol
            FROM usuarios AS u
            JOIN roles AS r ON r.id_rol = u.id_rol
            WHERE lower(u.email) = lower(?)
            """,
            (email.strip(),),
        ).fetchone()
    return _como_cuenta(fila)


def obtener_usuario_activo(ruta: Path, id_usuario: int) -> dict | None:
    with closing(sqlite3.connect(ruta)) as conexion:
        conexion.row_factory = sqlite3.Row
        fila = conexion.execute(
            """
            SELECT u.id_usuario, u.nombre, u.email, u.password_hash, u.activo,
                   r.nombre AS rol
            FROM usuarios AS u
            JOIN roles AS r ON r.id_rol = u.id_rol
            WHERE u.id_usuario = ? AND u.activo = 1
            """,
            (id_usuario,),
        ).fetchone()
    return _como_cuenta(fila)


def actualizar_password(ruta: Path, id_usuario: int, hash_nuevo: str) -> bool:
    with closing(sqlite3.connect(ruta)) as conexion, conexion:
        cursor = conexion.execute(
            "UPDATE usuarios SET password_hash = ? WHERE id_usuario = ?",
            (hash_nuevo, id_usuario),
        )
        return cursor.rowcount > 0


def actualizar_password_por_email(ruta: Path, email: str, hash_nuevo: str) -> bool:
    with closing(sqlite3.connect(ruta)) as conexion, conexion:
        cursor = conexion.execute(
            "UPDATE usuarios SET password_hash = ? WHERE lower(email) = lower(?)",
            (hash_nuevo, email.strip()),
        )
        return cursor.rowcount > 0


def crear_usuario_con_password(ruta: Path, datos: dict, hash_password: str) -> int:
    with closing(sqlite3.connect(ruta)) as conexion, conexion:
        conexion.execute("PRAGMA foreign_keys = ON")
        cursor = conexion.execute(
            """
            INSERT INTO usuarios (nombre, email, password_hash, id_rol, activo)
            VALUES (:nombre, :email, :password_hash, :id_rol, 1)
            """,
            {**datos, "password_hash": hash_password},
        )
        return cursor.lastrowid


def aplicar_passwords_desde_entorno(ruta: Path) -> None:
    """Cambia las contraseñas de demostración si hay variables de entorno.

    ADMIN_PASSWORD y VENDEDOR_PASSWORD permiten desplegar con contraseñas
    propias sin dejar las de demostración (admin123 / ventas123) activas.
    """
    for variable, correo in (
        ("ADMIN_PASSWORD", CORREO_ADMIN_DEMO),
        ("VENDEDOR_PASSWORD", CORREO_VENDEDOR_DEMO),
    ):
        password = os.getenv(variable)
        if password:
            actualizar_password_por_email(ruta, correo, hashear_password(password))


def _como_cuenta(fila: sqlite3.Row | None) -> dict | None:
    if fila is None:
        return None
    cuenta = dict(fila)
    cuenta["activo"] = bool(cuenta["activo"])
    return cuenta
