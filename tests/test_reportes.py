from contextlib import closing
import sqlite3

import pytest
from fastapi.testclient import TestClient

from app.database import inicializar_base_datos
from app.main import crear_app

RUTAS_REPORTES = [
    "/reportes/inventario-por-categoria",
    "/reportes/stock-bajo",
    "/reportes/movimientos-por-proveedor",
    "/reportes/movimientos-por-usuario",
]


def preparar_base(ruta):
    """Datos pequeños con totales fáciles de comprobar a mano."""
    inicializar_base_datos(ruta)
    with closing(sqlite3.connect(ruta)) as conexion, conexion:
        conexion.execute("PRAGMA foreign_keys = ON")
        conexion.executemany(
            "INSERT INTO roles (id_rol, nombre) VALUES (?, ?)",
            [(1, "ADMINISTRADOR"), (2, "VENDEDOR")],
        )
        conexion.executemany(
            "INSERT INTO usuarios (id_usuario, nombre, email, password_hash, id_rol, activo)"
            " VALUES (?, ?, ?, ?, ?, ?)",
            [(1, "Ana", "ana@example.com", "x", 1, 1), (2, "Beto", "beto@example.com", "x", 2, 1)],
        )
        conexion.executemany(
            "INSERT INTO categorias (id_categoria, nombre) VALUES (?, ?)",
            [(1, "Lácteos"), (2, "Embutidos"), (3, "Vacía")],
        )
        conexion.executemany(
            "INSERT INTO proveedores (id_proveedor, nombre, telefono, email) VALUES (?, ?, ?, ?)",
            [(1, "Prov A", "300", "a@example.com"), (2, "Prov B", None, None)],
        )
        conexion.executemany(
            "INSERT INTO productos (id_producto, nombre, id_categoria, id_proveedor, unidad,"
            " precio_venta, stock_actual, stock_minimo, activo) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [
                (1, "Queso", 1, 1, "KG", 10000, 5, 2, 1),
                (2, "Leche", 1, 2, "UND", 3000, 1, 4, 1),
                (3, "Jamón", 2, 1, "KG", 20000, 2, 2, 1),
                (4, "Viejo", 2, 1, "KG", 5000, 0, 5, 0),
            ],
        )
        conexion.executemany(
            "INSERT INTO movimientos (id_movimiento, id_producto, id_usuario, tipo, cantidad, fecha)"
            " VALUES (?, ?, ?, ?, ?, ?)",
            [
                (1, 1, 1, "ENTRADA", 10, "2026-10-01 08:00:00"),
                (2, 1, 1, "SALIDA", 5, "2026-10-02 09:00:00"),
                (3, 2, 2, "ENTRADA", 12, "2026-10-02 10:00:00"),
                (4, 3, 2, "SALIDA", 3, "2026-11-01 11:00:00"),
            ],
        )


@pytest.fixture
def cliente(tmp_path, monkeypatch):
    monkeypatch.delenv("CARGAR_DATOS_EJEMPLO", raising=False)
    monkeypatch.delenv("ADMIN_PASSWORD", raising=False)
    monkeypatch.delenv("VENDEDOR_PASSWORD", raising=False)
    ruta = tmp_path / "reportes.db"
    preparar_base(ruta)
    with TestClient(crear_app(ruta)) as cliente:
        yield cliente


def por_proveedor_o_usuario(filas):
    return [
        (f.get("proveedor") or f.get("usuario"), f["unidad"], f["movimientos"], f["entradas"], f["salidas"])
        for f in filas
    ]


def test_inventario_por_categoria(cliente):
    respuesta = cliente.get("/reportes/inventario-por-categoria")

    assert respuesta.status_code == 200
    filas = [
        (f["categoria"], f["productos"], f["bajo_minimo"], f["valor_inventario"])
        for f in respuesta.json()
    ]
    # Cuenta solo productos activos; las categorías sin productos aparecen en cero.
    assert filas == [("Lácteos", 2, 1, 53000), ("Embutidos", 1, 1, 40000), ("Vacía", 0, 0, 0)]


def test_stock_bajo_ordena_por_faltante_y_omite_inactivos(cliente):
    filas = cliente.get("/reportes/stock-bajo").json()

    assert [f["nombre"] for f in filas] == ["Leche", "Jamón"]
    assert filas[0]["faltante"] == 3
    assert filas[0]["proveedor"] == "Prov B"
    assert filas[0]["proveedor_telefono"] is None
    assert filas[1]["faltante"] == 0
    assert filas[1]["proveedor_telefono"] == "300"


def test_movimientos_por_proveedor_con_y_sin_fechas(cliente):
    todos = cliente.get("/reportes/movimientos-por-proveedor").json()
    octubre = cliente.get(
        "/reportes/movimientos-por-proveedor",
        params={"desde": "2026-10-01", "hasta": "2026-10-31"},
    ).json()
    hasta_primero = cliente.get(
        "/reportes/movimientos-por-proveedor", params={"hasta": "2026-10-01"}
    ).json()
    futuro = cliente.get(
        "/reportes/movimientos-por-proveedor", params={"desde": "2027-01-01"}
    ).json()

    assert por_proveedor_o_usuario(todos) == [("Prov A", "KG", 3, 10, 8), ("Prov B", "UND", 1, 12, 0)]
    assert por_proveedor_o_usuario(octubre) == [("Prov A", "KG", 2, 10, 5), ("Prov B", "UND", 1, 12, 0)]
    assert por_proveedor_o_usuario(hasta_primero) == [("Prov A", "KG", 1, 10, 0)]
    assert futuro == []


def test_movimientos_por_usuario_separa_por_unidad(cliente):
    filas = cliente.get("/reportes/movimientos-por-usuario").json()

    assert [(f["usuario"], f["rol"]) for f in filas] == [
        ("Ana", "ADMINISTRADOR"),
        ("Beto", "VENDEDOR"),
        ("Beto", "VENDEDOR"),
    ]
    assert por_proveedor_o_usuario(filas) == [
        ("Ana", "KG", 2, 10, 5),
        ("Beto", "KG", 1, 0, 3),
        ("Beto", "UND", 1, 12, 0),
    ]


@pytest.mark.parametrize(
    "parametros",
    [
        {"desde": "2026-12-01", "hasta": "2026-10-01"},
        {"desde": "hoy"},
        {"hasta": "2026-13-45"},
    ],
)
def test_fechas_invalidas_devuelven_422(cliente, parametros):
    for ruta in ("/reportes/movimientos-por-proveedor", "/reportes/movimientos-por-usuario"):
        assert cliente.get(ruta, params=parametros).status_code == 422


def test_pagina_de_reportes_esta_disponible(cliente):
    respuesta = cliente.get("/reportes-ui")

    assert respuesta.status_code == 200
    assert 'id="reporte"' in respuesta.text
    assert "/static/reportes/reportes.js?v=1" in respuesta.text


# --- Con autenticación activa ---------------------------------------------------


@pytest.fixture
def cliente_con_login(tmp_path, monkeypatch):
    monkeypatch.setenv("AUTH_ACTIVADA", "1")
    monkeypatch.setenv("SECRET_KEY", "clave-de-prueba")
    monkeypatch.setenv("CARGAR_DATOS_EJEMPLO", "1")
    monkeypatch.delenv("ADMIN_PASSWORD", raising=False)
    monkeypatch.delenv("VENDEDOR_PASSWORD", raising=False)
    with TestClient(crear_app(tmp_path / "productos.db")) as cliente:
        yield cliente


@pytest.mark.parametrize("ruta", RUTAS_REPORTES)
def test_reportes_exigen_sesion(cliente_con_login, ruta):
    assert cliente_con_login.get(ruta).status_code == 401


@pytest.mark.parametrize("ruta", RUTAS_REPORTES)
def test_el_vendedor_puede_consultar_reportes(cliente_con_login, ruta):
    login = cliente_con_login.post(
        "/auth/login",
        json={"email": "ventas@salsamentaria.com", "password": "ventas123"},
    )
    cabeceras = {"Authorization": f"Bearer {login.json()['access_token']}"}

    respuesta = cliente_con_login.get(ruta, headers=cabeceras)

    assert respuesta.status_code == 200
    assert isinstance(respuesta.json(), list)
