from contextlib import closing
import sqlite3

from fastapi.testclient import TestClient

from app.database import cargar_datos_iniciales, inicializar_base_datos
from app.main import crear_app


def contar(ruta, tabla):
    with closing(sqlite3.connect(ruta)) as conexion:
        return conexion.execute(f"SELECT COUNT(*) FROM {tabla}").fetchone()[0]


def test_salud_responde_ok(tmp_path):
    with TestClient(crear_app(tmp_path / "productos.db")) as cliente:
        respuesta = cliente.get("/salud")

    assert respuesta.status_code == 200
    assert respuesta.json() == {"estado": "ok"}


def test_datos_iniciales_se_cargan_una_sola_vez(tmp_path):
    ruta = tmp_path / "productos.db"
    inicializar_base_datos(ruta)

    assert cargar_datos_iniciales(ruta) is True
    productos = contar(ruta, "productos")
    assert productos > 0

    assert cargar_datos_iniciales(ruta) is False
    assert contar(ruta, "productos") == productos


def test_arranque_carga_datos_si_la_variable_esta_activa(tmp_path, monkeypatch):
    ruta = tmp_path / "productos.db"
    monkeypatch.setenv("CARGAR_DATOS_EJEMPLO", "1")

    with TestClient(crear_app(ruta)):
        pass

    assert contar(ruta, "roles") > 0
    assert contar(ruta, "productos") > 0


def test_arranque_sin_variable_deja_la_base_vacia(tmp_path, monkeypatch):
    ruta = tmp_path / "productos.db"
    monkeypatch.delenv("CARGAR_DATOS_EJEMPLO", raising=False)

    with TestClient(crear_app(ruta)):
        pass

    assert contar(ruta, "productos") == 0


def test_migracion_agrega_cambio_password_sin_marcar_usuarios_existentes(tmp_path):
    ruta = tmp_path / "productos.db"
    with closing(sqlite3.connect(ruta)) as conexion:
        conexion.executescript(
            """
            CREATE TABLE roles (
                id_rol INTEGER PRIMARY KEY,
                nombre TEXT NOT NULL UNIQUE
            );
            CREATE TABLE usuarios (
                id_usuario INTEGER PRIMARY KEY,
                nombre TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                id_rol INTEGER NOT NULL,
                activo INTEGER NOT NULL DEFAULT 1
            );
            INSERT INTO roles VALUES (1, 'ADMINISTRADOR');
            INSERT INTO usuarios VALUES
                (1, 'Admin', 'admin@example.com', 'hash', 1, 1);
            """
        )

    inicializar_base_datos(ruta)

    with closing(sqlite3.connect(ruta)) as conexion:
        columnas = {
            fila[1] for fila in conexion.execute("PRAGMA table_info(usuarios)")
        }
        requiere_cambio = conexion.execute(
            "SELECT requiere_cambio_password FROM usuarios WHERE id_usuario = 1"
        ).fetchone()[0]

    assert "requiere_cambio_password" in columnas
    assert requiere_cambio == 0
