"""Operaciones de negocio y persistencia de roles."""

from contextlib import closing
from pathlib import Path
import sqlite3


def listar_roles(ruta: Path) -> list[dict]:
    with closing(sqlite3.connect(ruta)) as conexion:
        conexion.row_factory = sqlite3.Row
        filas = conexion.execute(
            "SELECT id_rol, nombre FROM roles ORDER BY nombre"
        ).fetchall()
    return [dict(fila) for fila in filas]


def obtener_rol(ruta: Path, id_rol: int) -> dict | None:
    with closing(sqlite3.connect(ruta)) as conexion:
        conexion.row_factory = sqlite3.Row
        fila = conexion.execute(
            "SELECT id_rol, nombre FROM roles WHERE id_rol = ?",
            (id_rol,),
        ).fetchone()
    return dict(fila) if fila else None


def crear_rol(ruta: Path, rol: dict) -> dict:
    with closing(sqlite3.connect(ruta)) as conexion, conexion:
        cursor = conexion.execute(
            "INSERT INTO roles (nombre) VALUES (:nombre)",
            rol,
        )
        id_rol = cursor.lastrowid
    resultado = obtener_rol(ruta, id_rol)
    if resultado is None:
        raise RuntimeError("No se pudo volver a leer el rol recién creado")
    return resultado


def actualizar_rol(ruta: Path, id_rol: int, rol: dict) -> dict | None:
    with closing(sqlite3.connect(ruta)) as conexion, conexion:
        cursor = conexion.execute(
            "UPDATE roles SET nombre = :nombre WHERE id_rol = :id_rol",
            {**rol, "id_rol": id_rol},
        )
        if cursor.rowcount == 0:
            return None
    return obtener_rol(ruta, id_rol)


def eliminar_rol(ruta: Path, id_rol: int) -> bool:
    with closing(sqlite3.connect(ruta)) as conexion, conexion:
        conexion.execute("PRAGMA foreign_keys = ON")
        cursor = conexion.execute(
            "DELETE FROM roles WHERE id_rol = ?",
            (id_rol,),
        )
        return cursor.rowcount > 0
