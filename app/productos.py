from contextlib import closing
from pathlib import Path
import sqlite3


class UnidadProductoInmutable(Exception):
    pass


def listar_productos(ruta: Path) -> list[dict]:
    with closing(sqlite3.connect(ruta)) as conexion:
        conexion.row_factory = sqlite3.Row
        filas = conexion.execute(_consulta_productos() + " ORDER BY p.nombre").fetchall()
    return [dict(fila) for fila in filas]


def obtener_producto(ruta: Path, id_producto: int) -> dict | None:
    with closing(sqlite3.connect(ruta)) as conexion:
        conexion.row_factory = sqlite3.Row
        fila = conexion.execute(
            _consulta_productos() + " WHERE p.id_producto = ?",
            (id_producto,),
        ).fetchone()
    return dict(fila) if fila else None


def crear_producto(ruta: Path, producto: dict) -> dict:
    with closing(sqlite3.connect(ruta)) as conexion, conexion:
        conexion.execute("PRAGMA foreign_keys = ON")
        cursor = conexion.execute(
            """
            INSERT INTO productos (
                nombre, id_categoria, id_proveedor, unidad, precio_venta,
                stock_actual, stock_minimo, activo
            ) VALUES (
                :nombre, :id_categoria, :id_proveedor, :unidad, :precio_venta,
                0, :stock_minimo, :activo
            )
            """,
            {**producto, "activo": int(producto["activo"])},
        )
        id_producto = cursor.lastrowid
    result = obtener_producto(ruta, id_producto)
    if result is None:
        raise RuntimeError("No se pudo volver a leer el producto recién creado")
    return result


def actualizar_producto(ruta: Path, id_producto: int, producto: dict) -> dict | None:
    with closing(sqlite3.connect(ruta)) as conexion, conexion:
        conexion.execute("PRAGMA foreign_keys = ON")
        conexion.execute("BEGIN IMMEDIATE")
        actual = conexion.execute(
            """
            SELECT p.unidad, p.stock_actual,
                   EXISTS(
                       SELECT 1 FROM movimientos m
                       WHERE m.id_producto = p.id_producto
                   ) AS tiene_movimientos
            FROM productos p
            WHERE p.id_producto = ?
            """,
            (id_producto,),
        ).fetchone()
        if actual is None:
            return None
        if producto["unidad"] != actual[0] and (actual[1] > 0 or actual[2]):
            raise UnidadProductoInmutable
        cursor = conexion.execute(
            """
            UPDATE productos
            SET nombre = :nombre,
                id_categoria = :id_categoria,
                id_proveedor = :id_proveedor,
                unidad = :unidad,
                precio_venta = :precio_venta,
                stock_minimo = :stock_minimo,
                activo = :activo
            WHERE id_producto = :id_producto
            """,
            {
                **producto,
                "activo": int(producto["activo"]),
                "id_producto": id_producto,
            },
        )
        if cursor.rowcount == 0:
            return None
    return obtener_producto(ruta, id_producto)


def eliminar_producto(ruta: Path, id_producto: int) -> bool:
    with closing(sqlite3.connect(ruta)) as conexion, conexion:
        conexion.execute("PRAGMA foreign_keys = ON")
        cursor = conexion.execute(
            "DELETE FROM productos WHERE id_producto = ?", (id_producto,)
        )
        return cursor.rowcount > 0


def listar_catalogos(ruta: Path) -> dict[str, list[dict]]:
    with closing(sqlite3.connect(ruta)) as conexion:
        conexion.row_factory = sqlite3.Row
        categorias = conexion.execute(
            "SELECT id_categoria, nombre FROM categorias ORDER BY nombre"
        ).fetchall()
        proveedores = conexion.execute(
            "SELECT id_proveedor, nombre FROM proveedores ORDER BY nombre"
        ).fetchall()
        usuarios = conexion.execute(
            """
            SELECT id_usuario, nombre
            FROM usuarios
            WHERE activo = 1
            ORDER BY nombre
            """
        ).fetchall()
    return {
        "categorias": [dict(fila) for fila in categorias],
        "proveedores": [dict(fila) for fila in proveedores],
        "usuarios": [dict(fila) for fila in usuarios],
    }


def _consulta_productos() -> str:
    return """
        SELECT p.id_producto, p.nombre,
               p.id_categoria, c.nombre AS categoria,
               p.id_proveedor, pr.nombre AS proveedor,
               p.unidad, p.precio_venta, p.stock_actual, p.stock_minimo,
               p.activo
        FROM productos AS p
        JOIN categorias AS c ON c.id_categoria = p.id_categoria
        JOIN proveedores AS pr ON pr.id_proveedor = p.id_proveedor
    """
