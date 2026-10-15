import pytest
from fastapi.testclient import TestClient

from app.main import crear_app
from app.seguridad import (
    _codificar,
    crear_token,
    hashear_password,
    leer_token,
    tiene_permiso,
    verificar_password,
)

ADMIN = {"email": "admin@salsamentaria.com", "password": "admin123"}
VENDEDOR = {"email": "ventas@salsamentaria.com", "password": "ventas123"}


def preparar_entorno(monkeypatch):
    monkeypatch.setenv("AUTH_ACTIVADA", "1")
    monkeypatch.setenv("SECRET_KEY", "clave-de-prueba")
    monkeypatch.setenv("CARGAR_DATOS_EJEMPLO", "1")
    monkeypatch.delenv("ADMIN_PASSWORD", raising=False)
    monkeypatch.delenv("VENDEDOR_PASSWORD", raising=False)


@pytest.fixture
def cliente(tmp_path, monkeypatch):
    preparar_entorno(monkeypatch)
    with TestClient(crear_app(tmp_path / "productos.db")) as cliente:
        yield cliente


def entrar(cliente, credenciales):
    respuesta = cliente.post("/auth/login", json=credenciales)
    assert respuesta.status_code == 200
    return {"Authorization": f"Bearer {respuesta.json()['access_token']}"}


# --- Seguridad (sin servidor) -------------------------------------------------


def test_password_se_guarda_con_hash_y_se_verifica():
    hash_guardado = hashear_password("clave-segura-1", iteraciones=1000)

    assert "clave-segura-1" not in hash_guardado
    assert verificar_password("clave-segura-1", hash_guardado)
    assert not verificar_password("otra-clave", hash_guardado)
    assert not verificar_password("x", "HASH_ADMIN")
    assert not verificar_password("x", "")


def test_token_valido_y_manipulado(monkeypatch):
    monkeypatch.setenv("SECRET_KEY", "clave-de-prueba")
    token = crear_token(7)
    cabecera, carga, firma = token.split(".")
    carga_falsa = _codificar(b'{"sub":"1","exp":9999999999}')

    assert leer_token(token)["sub"] == "7"
    assert leer_token(f"{cabecera}.{carga_falsa}.{firma}") is None
    assert leer_token(token + "a") is None
    assert leer_token("no-es-un-token") is None
    assert leer_token(crear_token(7, vigencia_segundos=-5)) is None


def test_token_firmado_con_otra_clave_se_rechaza(monkeypatch):
    monkeypatch.setenv("SECRET_KEY", "clave-uno")
    token = crear_token(1)
    monkeypatch.setenv("SECRET_KEY", "clave-dos")

    assert leer_token(token) is None


@pytest.mark.parametrize(
    ("rol", "metodo", "ruta", "esperado"),
    [
        ("ADMINISTRADOR", "DELETE", "/productos/1", True),
        ("ADMINISTRADOR", "GET", "/usuarios", True),
        ("VENDEDOR", "GET", "/productos", True),
        ("VENDEDOR", "GET", "/movimientos", True),
        ("VENDEDOR", "POST", "/movimientos", True),
        ("VENDEDOR", "PUT", "/movimientos/1", False),
        ("VENDEDOR", "POST", "/productos", False),
        ("VENDEDOR", "DELETE", "/categorias/1", False),
        ("VENDEDOR", "GET", "/usuarios", False),
        ("VENDEDOR", "GET", "/usuarios/2", False),
        ("VENDEDOR", "GET", "/roles", False),
    ],
)
def test_reglas_de_permisos_por_rol(rol, metodo, ruta, esperado):
    assert tiene_permiso(rol, metodo, ruta) is esperado


# --- API ----------------------------------------------------------------------


def test_paginas_y_salud_son_publicas(cliente):
    assert cliente.get("/salud").status_code == 200
    assert cliente.get("/").status_code == 200
    assert cliente.get("/productos-ui").status_code == 200
    login = cliente.get("/login-ui")
    assert login.status_code == 200
    assert 'id="formulario-login"' in login.text


@pytest.mark.parametrize(
    "ruta",
    ["/productos", "/movimientos", "/categorias", "/proveedores", "/usuarios", "/roles", "/catalogos"],
)
def test_api_sin_token_devuelve_401(cliente, ruta):
    respuesta = cliente.get(ruta)

    assert respuesta.status_code == 401
    assert respuesta.headers["www-authenticate"] == "Bearer"


def test_token_invalido_o_vencido_devuelve_401(cliente):
    invalido = cliente.get("/productos", headers={"Authorization": "Bearer abc"})
    vencido = cliente.get(
        "/productos",
        headers={"Authorization": f"Bearer {crear_token(1, vigencia_segundos=-10)}"},
    )

    assert invalido.status_code == 401
    assert vencido.status_code == 401


def test_login_correcto_devuelve_token_y_datos_del_usuario(cliente):
    respuesta = cliente.post("/auth/login", json=ADMIN)

    assert respuesta.status_code == 200
    datos = respuesta.json()
    assert datos["token_type"] == "bearer"
    assert datos["usuario"]["rol"] == "ADMINISTRADOR"
    assert "password_hash" not in respuesta.text


def test_login_incorrecto_devuelve_401(cliente):
    password_mala = cliente.post(
        "/auth/login", json={**ADMIN, "password": "incorrecta"}
    )
    correo_inexistente = cliente.post(
        "/auth/login", json={"email": "nadie@example.com", "password": "admin123"}
    )
    sin_password = cliente.post("/auth/login", json={"email": ADMIN["email"]})

    assert password_mala.status_code == 401
    assert correo_inexistente.status_code == 401
    assert password_mala.json()["detail"] == correo_inexistente.json()["detail"]
    assert sin_password.status_code == 422


def test_auth_yo_devuelve_el_usuario_de_la_sesion(cliente):
    admin = cliente.get("/auth/yo", headers=entrar(cliente, ADMIN))
    vendedor = cliente.get("/auth/yo", headers=entrar(cliente, VENDEDOR))
    sin_token = cliente.get("/auth/yo")

    assert admin.json()["rol"] == "ADMINISTRADOR"
    assert vendedor.json()["email"] == VENDEDOR["email"]
    assert vendedor.json()["rol"] == "VENDEDOR"
    assert sin_token.status_code == 401


def test_administrador_puede_consultar_y_modificar(cliente):
    cabeceras = entrar(cliente, ADMIN)

    assert cliente.get("/productos", headers=cabeceras).status_code == 200
    assert cliente.get("/usuarios", headers=cabeceras).status_code == 200
    assert cliente.get("/roles", headers=cabeceras).status_code == 200
    creada = cliente.post("/categorias", json={"nombre": "Bebidas"}, headers=cabeceras)
    assert creada.status_code == 201


def test_vendedor_consulta_y_registra_movimientos_pero_no_modifica(cliente):
    cabeceras = entrar(cliente, VENDEDOR)

    assert cliente.get("/productos", headers=cabeceras).status_code == 200
    assert cliente.get("/movimientos", headers=cabeceras).status_code == 200
    movimiento = cliente.post(
        "/movimientos",
        json={"id_producto": 1, "id_usuario": 2, "tipo": "ENTRADA", "cantidad": 2},
        headers=cabeceras,
    )
    assert movimiento.status_code == 201

    crear = cliente.post("/categorias", json={"nombre": "Bebidas"}, headers=cabeceras)
    borrar = cliente.delete("/productos/1", headers=cabeceras)
    usuarios = cliente.get("/usuarios", headers=cabeceras)
    roles = cliente.get("/roles", headers=cabeceras)
    assert crear.status_code == 403
    assert borrar.status_code == 403
    assert usuarios.status_code == 403
    assert roles.status_code == 403
    assert "permiso" in crear.json()["detail"]


def test_usuario_desactivado_pierde_el_acceso_de_inmediato(cliente):
    admin = entrar(cliente, ADMIN)
    vendedor = entrar(cliente, VENDEDOR)
    assert cliente.get("/productos", headers=vendedor).status_code == 200

    desactivar = cliente.put(
        "/usuarios/2",
        json={
            "nombre": "Laura Vendedora",
            "email": VENDEDOR["email"],
            "id_rol": 2,
            "activo": False,
        },
        headers=admin,
    )

    assert desactivar.status_code == 200
    assert cliente.get("/productos", headers=vendedor).status_code == 401
    assert cliente.post("/auth/login", json=VENDEDOR).status_code == 401


def test_cambiar_password_propia(cliente):
    cabeceras = entrar(cliente, VENDEDOR)

    incorrecta = cliente.put(
        "/auth/password",
        json={"password_actual": "mala", "password_nueva": "nueva-clave-123"},
        headers=cabeceras,
    )
    corta = cliente.put(
        "/auth/password",
        json={"password_actual": "ventas123", "password_nueva": "corta"},
        headers=cabeceras,
    )
    correcta = cliente.put(
        "/auth/password",
        json={"password_actual": "ventas123", "password_nueva": "nueva-clave-123"},
        headers=cabeceras,
    )

    assert incorrecta.status_code == 400
    assert corta.status_code == 422
    assert correcta.status_code == 204
    assert cliente.post("/auth/login", json=VENDEDOR).status_code == 401
    nuevo = {"email": VENDEDOR["email"], "password": "nueva-clave-123"}
    assert cliente.post("/auth/login", json=nuevo).status_code == 200


def test_administrador_crea_usuarios_con_contrasena(cliente):
    admin = entrar(cliente, ADMIN)
    vendedor = entrar(cliente, VENDEDOR)
    datos = {
        "nombre": "Pedro Pérez",
        "email": "pedro@example.com",
        "password": "clave-segura-1",
        "id_rol": 2,
    }

    creado = cliente.post("/auth/usuarios", json=datos, headers=admin)
    duplicado = cliente.post("/auth/usuarios", json=datos, headers=admin)
    rol_inexistente = cliente.post(
        "/auth/usuarios",
        json={**datos, "email": "otro@example.com", "id_rol": 99},
        headers=admin,
    )
    por_vendedor = cliente.post("/auth/usuarios", json=datos, headers=vendedor)
    sin_token = cliente.post("/auth/usuarios", json=datos)

    assert creado.status_code == 201
    assert creado.json()["rol"] == "VENDEDOR"
    assert "password" not in creado.text
    assert duplicado.status_code == 409
    assert rol_inexistente.status_code == 409
    assert por_vendedor.status_code == 403
    assert sin_token.status_code == 401
    login = cliente.post(
        "/auth/login", json={"email": "pedro@example.com", "password": "clave-segura-1"}
    )
    assert login.status_code == 200


def test_contrasenas_de_demostracion_se_reemplazan_desde_el_entorno(tmp_path, monkeypatch):
    preparar_entorno(monkeypatch)
    monkeypatch.setenv("ADMIN_PASSWORD", "otra-clave-123")

    with TestClient(crear_app(tmp_path / "productos.db")) as cliente:
        nueva = cliente.post(
            "/auth/login", json={"email": ADMIN["email"], "password": "otra-clave-123"}
        )
        demo = cliente.post("/auth/login", json=ADMIN)
        vendedor = cliente.post("/auth/login", json=VENDEDOR)

    assert nueva.status_code == 200
    assert demo.status_code == 401
    assert vendedor.status_code == 200


def test_con_autenticacion_desactivada_la_api_no_pide_token(tmp_path, monkeypatch):
    preparar_entorno(monkeypatch)
    monkeypatch.setenv("AUTH_ACTIVADA", "0")

    with TestClient(crear_app(tmp_path / "productos.db")) as cliente:
        respuesta = cliente.get("/productos")

    assert respuesta.status_code == 200
