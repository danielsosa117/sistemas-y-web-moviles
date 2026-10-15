from contextlib import closing
from pathlib import Path
import sqlite3


class ProductoNoEncontrado(Exception):
    pass


class MovimientoNoEncontrado(Exception):
    pass


class UsuarioNoEncontrado(Exception):
    pass


class StockInsuficiente(Exception):
    def __init__(self, disponible: float):
        self.disponible = disponible


class CantidadIncompatibleConUnidad(Exception):
    pass


class AjusteStockInvalido(Exception):
    pass


def registrar_movimiento(ruta: Path, movimiento: dict) -> dict:
    conexion = sqlite3.connect(ruta, timeout=10)
    conexion.row_factory = sqlite3.Row
    try:
        conexion.execute("PRAGMA foreign_keys = ON")
        conexion.execute("BEGIN IMMEDIATE")

        producto = conexion.execute(
            """
            SELECT nombre, unidad, stock_actual, activo
            FROM productos
            WHERE id_producto = ?
            """,
            (movimiento["id_producto"],),
        ).fetchone()
        if producto is None:
            raise ProductoNoEncontrado
        if not producto["activo"]:
            raise ValueError("No se pueden registrar movimientos para un producto inactivo")

        usuario = conexion.execute(
            "SELECT nombre FROM usuarios WHERE id_usuario = ? AND activo = 1",
            (movimiento["id_usuario"],),
        ).fetchone()
        if usuario is None:
            raise UsuarioNoEncontrado

        cantidad = movimiento["cantidad"]
        if producto["unidad"] == "UND" and not cantidad.is_integer():
            raise CantidadIncompatibleConUnidad

        stock_actual = producto["stock_actual"]
        if movimiento["tipo"] == "SALIDA":
            if stock_actual < cantidad:
                raise StockInsuficiente(stock_actual)
            nuevo_stock = stock_actual - cantidad
        else:
            nuevo_stock = stock_actual + cantidad

        conexion.execute(
            "UPDATE productos SET stock_actual = ? WHERE id_producto = ?",
            (nuevo_stock, movimiento["id_producto"]),
        )
        cursor = conexion.execute(
            """
            INSERT INTO movimientos (
                id_producto, id_usuario, tipo, cantidad, observacion
            ) VALUES (
                :id_producto, :id_usuario, :tipo, :cantidad, :observacion
            )
            """,
            movimiento,
        )
        resultado = conexion.execute(
            """
            SELECT m.id_movimiento, m.id_producto, p.nombre AS producto,
                   p.unidad, m.id_usuario, u.nombre AS usuario, m.tipo,
                   m.cantidad, m.fecha, m.observacion
            FROM movimientos AS m
            JOIN productos AS p ON p.id_producto = m.id_producto
            JOIN usuarios AS u ON u.id_usuario = m.id_usuario
            WHERE m.id_movimiento = ?
            """,
            (cursor.lastrowid,),
        ).fetchone()
        conexion.commit()
        return dict(resultado)
    except Exception:
        conexion.rollback()
        raise
    finally:
        conexion.close()


def actualizar_movimiento(ruta: Path, id_movimiento: int, cambios: dict) -> dict:
    conexion = sqlite3.connect(ruta, timeout=10)
    conexion.row_factory = sqlite3.Row
    try:
        conexion.execute("PRAGMA foreign_keys = ON")
        conexion.execute("BEGIN IMMEDIATE")

        movimiento = conexion.execute(
            """
            SELECT m.id_producto, m.id_usuario, m.tipo, m.cantidad,
                   p.unidad, p.stock_actual
            FROM movimientos AS m
            JOIN productos AS p ON p.id_producto = m.id_producto
            WHERE m.id_movimiento = ?
            """,
            (id_movimiento,),
        ).fetchone()
        if movimiento is None:
            raise MovimientoNoEncontrado

        usuario = conexion.execute(
            "SELECT nombre FROM usuarios WHERE id_usuario = ? AND activo = 1",
            (cambios["id_usuario"],),
        ).fetchone()
        if usuario is None:
            raise UsuarioNoEncontrado

        cantidad = cambios["cantidad"]
        if movimiento["unidad"] == "UND" and not cantidad.is_integer():
            raise CantidadIncompatibleConUnidad

        diferencia = cantidad - movimiento["cantidad"]
        cambio_stock = diferencia if movimiento["tipo"] == "ENTRADA" else -diferencia
        nuevo_stock = movimiento["stock_actual"] + cambio_stock
        if nuevo_stock < -1e-9:
            raise AjusteStockInvalido

        conexion.execute(
            "UPDATE productos SET stock_actual = ? WHERE id_producto = ?",
            (max(nuevo_stock, 0), movimiento["id_producto"]),
        )
        conexion.execute(
            """
            UPDATE movimientos
            SET cantidad = :cantidad,
                id_usuario = :id_usuario,
                observacion = :observacion
            WHERE id_movimiento = :id_movimiento
            """,
            {**cambios, "id_movimiento": id_movimiento},
        )
        resultado = conexion.execute(
            """
            SELECT m.id_movimiento, m.id_producto, p.nombre AS producto,
                   p.unidad, m.id_usuario, u.nombre AS usuario, m.tipo,
                   m.cantidad, m.fecha, m.observacion
            FROM movimientos AS m
            JOIN productos AS p ON p.id_producto = m.id_producto
            JOIN usuarios AS u ON u.id_usuario = m.id_usuario
            WHERE m.id_movimiento = ?
            """,
            (id_movimiento,),
        ).fetchone()
        conexion.commit()
        return dict(resultado)
    except Exception:
        conexion.rollback()
        raise
    finally:
        conexion.close()


def listar_movimientos(ruta: Path) -> list[dict]:
    with closing(sqlite3.connect(ruta)) as conexion:
        conexion.row_factory = sqlite3.Row
        filas = conexion.execute(
            """
            SELECT m.id_movimiento, m.id_producto, p.nombre AS producto,
                   p.unidad, m.id_usuario, u.nombre AS usuario, m.tipo,
                   m.cantidad, m.fecha, m.observacion
            FROM movimientos AS m
            JOIN productos AS p ON p.id_producto = m.id_producto
            JOIN usuarios AS u ON u.id_usuario = m.id_usuario
            ORDER BY m.fecha DESC, m.id_movimiento DESC
            """
        ).fetchall()
    return [dict(fila) for fila in filas]
