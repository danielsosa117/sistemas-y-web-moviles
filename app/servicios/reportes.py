"""Consultas de los reportes consolidados (solo lectura).

Las cantidades se agrupan por unidad (KG o UND) para no sumar kilos con unidades.
"""

from contextlib import closing
from pathlib import Path
import sqlite3


def _consultar(ruta: Path, sql: str, parametros: dict | None = None) -> list[dict]:
    with closing(sqlite3.connect(ruta)) as conexion:
        conexion.execute("PRAGMA query_only = ON")
        conexion.row_factory = sqlite3.Row
        filas = conexion.execute(sql, parametros or {}).fetchall()
    return [dict(fila) for fila in filas]


def inventario_por_categoria(ruta: Path) -> list[dict]:
    return _consultar(
        ruta,
        """
        SELECT c.nombre AS categoria,
               COUNT(p.id_producto) AS productos,
               COALESCE(SUM(CASE WHEN p.stock_actual <= p.stock_minimo THEN 1 END), 0)
                   AS bajo_minimo,
               COALESCE(SUM(p.stock_actual * p.precio_venta), 0) AS valor_inventario
        FROM categorias AS c
        LEFT JOIN productos AS p
               ON p.id_categoria = c.id_categoria AND p.activo = 1
        GROUP BY c.id_categoria
        ORDER BY valor_inventario DESC, c.nombre
        """,
    )


def stock_bajo(ruta: Path) -> list[dict]:
    return _consultar(
        ruta,
        """
        SELECT p.id_producto,
               p.nombre,
               c.nombre AS categoria,
               pr.nombre AS proveedor,
               pr.telefono AS proveedor_telefono,
               p.unidad,
               p.stock_actual,
               p.stock_minimo,
               p.stock_minimo - p.stock_actual AS faltante
        FROM productos AS p
        JOIN categorias AS c ON c.id_categoria = p.id_categoria
        JOIN proveedores AS pr ON pr.id_proveedor = p.id_proveedor
        WHERE p.activo = 1 AND p.stock_actual <= p.stock_minimo
        ORDER BY faltante DESC, p.nombre
        """,
    )


def movimientos_por_proveedor(
    ruta: Path, desde: str | None, hasta: str | None
) -> list[dict]:
    return _consultar(
        ruta,
        """
        SELECT pr.nombre AS proveedor,
               p.unidad,
               COUNT(m.id_movimiento) AS movimientos,
               COALESCE(SUM(CASE WHEN m.tipo = 'ENTRADA' THEN m.cantidad END), 0)
                   AS entradas,
               COALESCE(SUM(CASE WHEN m.tipo = 'SALIDA' THEN m.cantidad END), 0)
                   AS salidas
        FROM movimientos AS m
        JOIN productos AS p ON p.id_producto = m.id_producto
        JOIN proveedores AS pr ON pr.id_proveedor = p.id_proveedor
        WHERE (:desde IS NULL OR date(m.fecha) >= :desde)
          AND (:hasta IS NULL OR date(m.fecha) <= :hasta)
        GROUP BY pr.id_proveedor, p.unidad
        ORDER BY pr.nombre, p.unidad
        """,
        {"desde": desde, "hasta": hasta},
    )


def movimientos_por_usuario(
    ruta: Path, desde: str | None, hasta: str | None
) -> list[dict]:
    return _consultar(
        ruta,
        """
        SELECT u.nombre AS usuario,
               r.nombre AS rol,
               p.unidad,
               COUNT(m.id_movimiento) AS movimientos,
               COALESCE(SUM(CASE WHEN m.tipo = 'ENTRADA' THEN m.cantidad END), 0)
                   AS entradas,
               COALESCE(SUM(CASE WHEN m.tipo = 'SALIDA' THEN m.cantidad END), 0)
                   AS salidas
        FROM movimientos AS m
        JOIN usuarios AS u ON u.id_usuario = m.id_usuario
        JOIN roles AS r ON r.id_rol = u.id_rol
        JOIN productos AS p ON p.id_producto = m.id_producto
        WHERE (:desde IS NULL OR date(m.fecha) >= :desde)
          AND (:hasta IS NULL OR date(m.fecha) <= :hasta)
        GROUP BY u.id_usuario, p.unidad
        ORDER BY u.nombre, p.unidad
        """,
        {"desde": desde, "hasta": hasta},
    )
