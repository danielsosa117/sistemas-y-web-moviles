"""Operaciones de negocio y persistencia de proveedores."""

from contextlib import closing
from pathlib import Path
import sqlite3


def listar_proveedores(ruta: Path) -> list[dict]:
    with closing(sqlite3.connect(ruta)) as conexion:
        conexion.row_factory = sqlite3.Row
        filas = conexion.execute(
            """
            SELECT id_proveedor, nombre, telefono, email
            FROM proveedores
            ORDER BY nombre
            """
        ).fetchall()
    return [dict(fila) for fila in filas]


def obtener_proveedor(ruta: Path, id_proveedor: int) -> dict | None:
    with closing(sqlite3.connect(ruta)) as conexion:
        conexion.row_factory = sqlite3.Row
        fila = conexion.execute(
            """
            SELECT id_proveedor, nombre, telefono, email
            FROM proveedores
            WHERE id_proveedor = ?
            """,
            (id_proveedor,),
        ).fetchone()
    return dict(fila) if fila else None


def crear_proveedor(ruta: Path, proveedor: dict) -> dict:
    with closing(sqlite3.connect(ruta)) as conexion, conexion:
        cursor = conexion.execute(
            """
            INSERT INTO proveedores (nombre, telefono, email)
            VALUES (:nombre, :telefono, :email)
            """,
            proveedor,
        )
        id_proveedor = cursor.lastrowid
    resultado = obtener_proveedor(ruta, id_proveedor)
    if resultado is None:
        raise RuntimeError("No se pudo volver a leer el proveedor recién creado")
    return resultado


def actualizar_proveedor(
    ruta: Path,
    id_proveedor: int,
    proveedor: dict,
) -> dict | None:
    with closing(sqlite3.connect(ruta)) as conexion, conexion:
        cursor = conexion.execute(
            """
            UPDATE proveedores
            SET nombre = :nombre, telefono = :telefono, email = :email
            WHERE id_proveedor = :id_proveedor
            """,
            {**proveedor, "id_proveedor": id_proveedor},
        )
        if cursor.rowcount == 0:
            return None
    return obtener_proveedor(ruta, id_proveedor)


def eliminar_proveedor(ruta: Path, id_proveedor: int) -> bool:
    with closing(sqlite3.connect(ruta)) as conexion, conexion:
        conexion.execute("PRAGMA foreign_keys = ON")
        cursor = conexion.execute(
            "DELETE FROM proveedores WHERE id_proveedor = ?",
            (id_proveedor,),
        )
        return cursor.rowcount > 0
