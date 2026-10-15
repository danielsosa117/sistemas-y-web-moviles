"""Operaciones de negocio y persistencia de categorías."""

from contextlib import closing
from pathlib import Path
import sqlite3


def listar_categorias(ruta: Path) -> list[dict]:
    with closing(sqlite3.connect(ruta)) as conexion:
        conexion.row_factory = sqlite3.Row
        filas = conexion.execute(
            "SELECT id_categoria, nombre FROM categorias ORDER BY nombre"
        ).fetchall()
    return [dict(fila) for fila in filas]


def obtener_categoria(ruta: Path, id_categoria: int) -> dict | None:
    with closing(sqlite3.connect(ruta)) as conexion:
        conexion.row_factory = sqlite3.Row
        fila = conexion.execute(
            "SELECT id_categoria, nombre FROM categorias WHERE id_categoria = ?",
            (id_categoria,),
        ).fetchone()
    return dict(fila) if fila else None


def crear_categoria(ruta: Path, categoria: dict) -> dict:
    with closing(sqlite3.connect(ruta)) as conexion, conexion:
        cursor = conexion.execute(
            "INSERT INTO categorias (nombre) VALUES (:nombre)",
            categoria,
        )
        id_categoria = cursor.lastrowid
    resultado = obtener_categoria(ruta, id_categoria)
    if resultado is None:
        raise RuntimeError("No se pudo volver a leer la categoría recién creada")
    return resultado


def actualizar_categoria(
    ruta: Path,
    id_categoria: int,
    categoria: dict,
) -> dict | None:
    with closing(sqlite3.connect(ruta)) as conexion, conexion:
        cursor = conexion.execute(
            "UPDATE categorias SET nombre = :nombre WHERE id_categoria = :id_categoria",
            {**categoria, "id_categoria": id_categoria},
        )
        if cursor.rowcount == 0:
            return None
    return obtener_categoria(ruta, id_categoria)


def eliminar_categoria(ruta: Path, id_categoria: int) -> bool:
    with closing(sqlite3.connect(ruta)) as conexion, conexion:
        conexion.execute("PRAGMA foreign_keys = ON")
        cursor = conexion.execute(
            "DELETE FROM categorias WHERE id_categoria = ?",
            (id_categoria,),
        )
        return cursor.rowcount > 0
