"""Operaciones de negocio y persistencia de usuarios y roles."""

from contextlib import closing
from pathlib import Path
import sqlite3


def listar_usuarios(ruta: Path) -> list[dict]:
    with closing(sqlite3.connect(ruta)) as conexion:
        conexion.row_factory = sqlite3.Row
        filas = conexion.execute(_consulta_usuarios() + " ORDER BY u.nombre").fetchall()
    return [dict(fila) for fila in filas]


def obtener_usuario(ruta: Path, id_usuario: int) -> dict | None:
    with closing(sqlite3.connect(ruta)) as conexion:
        conexion.row_factory = sqlite3.Row
        fila = conexion.execute(
            _consulta_usuarios() + " WHERE u.id_usuario = ?",
            (id_usuario,),
        ).fetchone()
    return dict(fila) if fila else None


def actualizar_usuario(
    ruta: Path,
    id_usuario: int,
    usuario: dict,
) -> dict | None:
    with closing(sqlite3.connect(ruta)) as conexion, conexion:
        conexion.execute("PRAGMA foreign_keys = ON")
        cursor = conexion.execute(
            """
            UPDATE usuarios
            SET nombre = :nombre,
                email = :email,
                id_rol = :id_rol,
                activo = :activo
            WHERE id_usuario = :id_usuario
            """,
            {
                **usuario,
                "activo": int(usuario["activo"]),
                "id_usuario": id_usuario,
            },
        )
        if cursor.rowcount == 0:
            return None
    return obtener_usuario(ruta, id_usuario)


def _consulta_usuarios() -> str:
    return """
        SELECT u.id_usuario, u.nombre, u.email, u.id_rol,
               u.requiere_cambio_password,
               r.nombre AS rol, u.activo
        FROM usuarios AS u
        JOIN roles AS r ON r.id_rol = u.id_rol
    """
