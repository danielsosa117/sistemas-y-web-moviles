from contextlib import closing
import sqlite3

from fastapi.testclient import TestClient
import pytest

from app.database import inicializar_base_datos, obtener_ruta_esquema
from app.ejecutar_sql import ejecutar_script
from app.main import crear_app


def test_openapi_agrupa_endpoints_por_modulo(tmp_path):
    app = crear_app(tmp_path / "productos.db")
    esquema = app.openapi()
    nombres_etiquetas = [etiqueta["name"] for etiqueta in esquema["tags"]]

    assert nombres_etiquetas == [
        "Productos",
        "Movimientos",
        "Categorías",
        "Proveedores",
        "Usuarios",
        "Roles",
        "Autenticación",
        "Sistema",
    ]
    assert "/" not in esquema["paths"]
    assert all(not ruta.endswith("-ui") for ruta in esquema["paths"])
    assert esquema["paths"]["/productos"]["get"]["tags"] == ["Productos"]
    assert esquema["paths"]["/movimientos"]["get"]["tags"] == ["Movimientos"]
    assert esquema["paths"]["/categorias"]["get"]["tags"] == ["Categorías"]
    assert esquema["paths"]["/proveedores"]["get"]["tags"] == ["Proveedores"]
    assert esquema["paths"]["/usuarios"]["get"]["tags"] == ["Usuarios"]
    assert esquema["paths"]["/roles"]["get"]["tags"] == ["Roles"]
    assert esquema["paths"]["/auth/login"]["post"]["tags"] == ["Autenticación"]
    assert esquema["paths"]["/salud"]["get"]["tags"] == ["Sistema"]

    for ruta, operaciones in esquema["paths"].items():
        for operacion in operaciones.values():
            assert operacion["tags"]
            assert "default" not in operacion["tags"]


def test_inicio_y_archivos_estaticos(tmp_path):
    with TestClient(crear_app(tmp_path / "productos.db")) as cliente:
        respuesta = cliente.get("/")
        pagina_productos = cliente.get("/productos-ui")
        pagina_movimientos = cliente.get("/movimientos-ui")
        pagina_categorias = cliente.get("/categorias-ui")
        pagina_proveedores = cliente.get("/proveedores-ui")
        pagina_usuarios = cliente.get("/usuarios-ui")
        pagina_roles = cliente.get("/roles-ui")
        pagina_password = cliente.get("/cambiar-password-ui")
        pagina_recuperacion = cliente.get("/recuperar-password-ui")
        javascript_layout = cliente.get("/static/layout.js")
        javascript_productos = cliente.get("/static/productos/productos.js")
        javascript_movimientos = cliente.get("/static/movimientos/movimientos.js")
        javascript_categorias = cliente.get("/static/categorias/categorias.js")
        javascript_proveedores = cliente.get("/static/proveedores/proveedores.js")
        javascript_usuarios = cliente.get("/static/usuarios/usuarios.js")
        javascript_roles = cliente.get("/static/roles/roles.js")
        javascript_password = cliente.get("/static/password/password.js")
        javascript_recuperacion = cliente.get(
            "/static/recuperar-password/recuperar-password.js"
        )

    assert respuesta.status_code == 200
    assert "Productos" in respuesta.text
    assert "lista-productos" in respuesta.text
    assert respuesta.headers["content-type"].startswith("text/html")
    assert respuesta.headers["cache-control"] == "no-cache, must-revalidate"
    assert "/static/productos/productos.js?v=1" in respuesta.text
    assert 'id="dialogo-producto"' in respuesta.text
    assert 'id="abrir-formulario"' in respuesta.text
    assert pagina_productos.status_code == 200
    assert "/static/layout.js?v=1" in pagina_productos.text
    assert "<nav" not in pagina_productos.text
    for pagina_modulo in (
        pagina_productos,
        pagina_movimientos,
        pagina_categorias,
        pagina_proveedores,
        pagina_usuarios,
        pagina_roles,
    ):
        assert "/static/layout.js?v=1" in pagina_modulo.text
        assert "<nav" not in pagina_modulo.text
    assert javascript_layout.status_code == 200
    assert "Gestión de inventario" in javascript_layout.text
    assert 'ruta: "/movimientos-ui"' in javascript_layout.text
    assert pagina_movimientos.status_code == 200
    assert "lista-movimientos" in pagina_movimientos.text
    assert "/static/movimientos/movimientos.js?v=1" in pagina_movimientos.text
    assert pagina_categorias.status_code == 200
    assert "lista-categorias" in pagina_categorias.text
    assert "/static/categorias/categorias.js?v=1" in pagina_categorias.text
    assert pagina_proveedores.status_code == 200
    assert "lista-proveedores" in pagina_proveedores.text
    assert "/static/proveedores/proveedores.js?v=1" in pagina_proveedores.text
    assert pagina_usuarios.status_code == 200
    assert "Crear usuario" in pagina_usuarios.text
    assert "contraseña temporal aleatoria" in pagina_usuarios.text
    assert "lista-usuarios" in pagina_usuarios.text
    assert "/static/usuarios/usuarios.js?v=2" in pagina_usuarios.text
    assert javascript_usuarios.status_code == 200
    assert 'solicitar("/usuarios")' in javascript_usuarios.text
    assert 'solicitar("/auth/usuarios"' in javascript_usuarios.text
    assert 'method: "PUT"' in javascript_usuarios.text
    assert pagina_password.status_code == 200
    assert "Confirma la nueva contraseña" in pagina_password.text
    assert javascript_password.status_code == 200
    assert 'fetch("/auth/password"' in javascript_password.text
    assert pagina_recuperacion.status_code == 200
    assert "sin verificación por correo o SMS" in pagina_recuperacion.text
    assert javascript_recuperacion.status_code == 200
    assert 'fetch("/auth/recuperar-password"' in javascript_recuperacion.text
    assert pagina_roles.status_code == 200
    assert "lista-roles" in pagina_roles.text
    assert "/static/roles/roles.js?v=1" in pagina_roles.text
    assert javascript_roles.status_code == 200
    assert 'solicitar("/roles")' in javascript_roles.text
    assert 'method: editando ? "PUT" : "POST"' in javascript_roles.text
    assert javascript_productos.status_code == 200
    assert 'solicitar("/productos")' in javascript_productos.text
    assert "producto.categoria" in javascript_productos.text
    assert "producto.stock_actual" in javascript_productos.text
    assert 'method: esEdicion ? "PUT" : "POST"' in javascript_productos.text
    assert "dialogoProducto.showModal()" in javascript_productos.text
    assert javascript_movimientos.status_code == 200
    assert 'solicitar("/movimientos")' in javascript_movimientos.text
    assert "stock insuficiente" in javascript_movimientos.text.lower()
    assert "Editar movimiento" in javascript_movimientos.text
    assert 'method: esEdicion ? "PUT" : "POST"' in javascript_movimientos.text
    assert javascript_categorias.status_code == 200
    assert 'solicitar("/categorias")' in javascript_categorias.text
    assert javascript_proveedores.status_code == 200
    assert 'solicitar("/proveedores")' in javascript_proveedores.text


def test_base_nueva_crea_seis_tablas_y_catalogos_vacios(tmp_path):
    ruta_base_datos = tmp_path / "productos.db"

    with TestClient(crear_app(ruta_base_datos)) as cliente:
        respuesta = cliente.get("/productos")
        catalogos = cliente.get("/catalogos")

    assert respuesta.status_code == 200
    assert respuesta.json() == []
    assert catalogos.json() == {"categorias": [], "proveedores": [], "usuarios": []}
    with closing(sqlite3.connect(ruta_base_datos)) as conexion:
        tablas = {
            fila[0]
            for fila in conexion.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            )
        }
    assert {"roles", "usuarios", "categorias", "proveedores", "productos", "movimientos"} <= tablas


def test_script_de_datos_sql_alimenta_catalogo_y_catalogos(tmp_path):
    ruta_base_datos = tmp_path / "productos.db"
    ruta_datos = obtener_ruta_esquema().parent / "productos.sql"
    ejecutar_script(ruta_datos, ruta_base_datos)

    with TestClient(crear_app(ruta_base_datos)) as cliente:
        respuesta = cliente.get("/productos")
        catalogos = cliente.get("/catalogos")

    assert respuesta.status_code == 200
    productos = respuesta.json()
    assert len(productos) == 8
    assert len(catalogos.json()["categorias"]) == 4
    assert len(catalogos.json()["proveedores"]) == 3
    assert len(catalogos.json()["usuarios"]) == 2
    queso = next(producto for producto in productos if producto["nombre"] == "Queso campesino")
    assert queso == {
        "id_producto": 4,
        "nombre": "Queso campesino",
        "id_categoria": 2,
        "categoria": "Quesos",
        "id_proveedor": 2,
        "proveedor": "Lácteos La Pradera",
        "unidad": "KG",
        "precio_venta": 24000,
        "stock_actual": 15.75,
        "stock_minimo": 6,
        "activo": True,
    }


def test_usuarios_solo_se_consultan_y_actualizan_sin_exponer_contrasenas(tmp_path):
    ruta_base_datos = tmp_path / "productos.db"
    ejecutar_script(obtener_ruta_esquema().parent / "productos.sql", ruta_base_datos)

    with TestClient(crear_app(ruta_base_datos)) as cliente:
        listado = cliente.get("/usuarios")
        roles = cliente.get("/roles")
        id_usuario = listado.json()[0]["id_usuario"]
        detalle = cliente.get(f"/usuarios/{id_usuario}")
        actualizado = cliente.put(
            f"/usuarios/{id_usuario}",
            json={
                "nombre": "Nombre actualizado",
                "email": "actualizado@example.com",
                "id_rol": listado.json()[0]["id_rol"],
                "activo": False,
            },
        )
        no_encontrado = cliente.get("/usuarios/999")
        creacion_no_disponible = cliente.post(
            "/usuarios",
            json={
                "nombre": "Usuario nuevo",
                "email": "nuevo@example.com",
                "id_rol": 1,
                "activo": True,
            },
        )

    assert listado.status_code == 200
    assert len(listado.json()) == 2
    assert all("password_hash" not in usuario for usuario in listado.json())
    assert all(usuario["requiere_cambio_password"] is False for usuario in listado.json())
    assert detalle.status_code == 200
    assert "password_hash" not in detalle.json()
    assert roles.status_code == 200
    assert {rol["nombre"] for rol in roles.json()} == {"ADMINISTRADOR", "VENDEDOR"}
    assert actualizado.status_code == 200
    assert actualizado.json()["nombre"] == "Nombre actualizado"
    assert actualizado.json()["activo"] is False
    assert "password_hash" not in actualizado.json()
    assert no_encontrado.status_code == 404
    assert creacion_no_disponible.status_code == 405

    with closing(sqlite3.connect(ruta_base_datos)) as conexion:
        hash_guardado = conexion.execute(
            "SELECT password_hash FROM usuarios WHERE id_usuario = ?",
            (id_usuario,),
        ).fetchone()[0]
    assert hash_guardado.startswith("pbkdf2_sha256$")


def test_actualizacion_de_usuario_valida_correo_rol_y_campos_permitidos(tmp_path):
    ruta_base_datos = tmp_path / "productos.db"
    ejecutar_script(obtener_ruta_esquema().parent / "productos.sql", ruta_base_datos)

    with TestClient(crear_app(ruta_base_datos)) as cliente:
        usuarios = cliente.get("/usuarios").json()
        id_usuario = usuarios[0]["id_usuario"]
        correo_duplicado = cliente.put(
            f"/usuarios/{id_usuario}",
            json={
                "nombre": usuarios[0]["nombre"],
                "email": usuarios[1]["email"],
                "id_rol": usuarios[0]["id_rol"],
                "activo": True,
            },
        )
        rol_inexistente = cliente.put(
            f"/usuarios/{id_usuario}",
            json={
                "nombre": usuarios[0]["nombre"],
                "email": "valido@example.com",
                "id_rol": 999,
                "activo": True,
            },
        )
        hash_no_permitido = cliente.put(
            f"/usuarios/{id_usuario}",
            json={
                "nombre": usuarios[0]["nombre"],
                "email": usuarios[0]["email"],
                "id_rol": usuarios[0]["id_rol"],
                "activo": True,
                "password_hash": "nuevo-hash",
            },
        )
        correo_invalido = cliente.put(
            f"/usuarios/{id_usuario}",
            json={
                "nombre": usuarios[0]["nombre"],
                "email": "no-es-correo",
                "id_rol": usuarios[0]["id_rol"],
                "activo": True,
            },
        )

    assert correo_duplicado.status_code == 409
    assert rol_inexistente.status_code == 409
    assert hash_no_permitido.status_code == 422
    assert correo_invalido.status_code == 422


def test_crud_de_roles_y_proteccion_de_roles_asignados(tmp_path):
    ruta_base_datos = tmp_path / "productos.db"
    ejecutar_script(obtener_ruta_esquema().parent / "productos.sql", ruta_base_datos)

    with TestClient(crear_app(ruta_base_datos)) as cliente:
        roles_iniciales = cliente.get("/roles").json()
        rol_creado = cliente.post("/roles", json={"nombre": "  INVENTARIO  "})
        id_rol = rol_creado.json()["id_rol"]
        detalle = cliente.get(f"/roles/{id_rol}")
        actualizado = cliente.put(
            f"/roles/{id_rol}",
            json={"nombre": "SUPERVISOR DE INVENTARIO"},
        )
        listado = cliente.get("/roles")
        eliminado = cliente.delete(f"/roles/{id_rol}")
        inexistente = cliente.get(f"/roles/{id_rol}")
        nombre_duplicado = cliente.post(
            "/roles",
            json={"nombre": roles_iniciales[0]["nombre"]},
        )
        rol_asignado = cliente.delete(f"/roles/{roles_iniciales[0]['id_rol']}")
        invalidos = cliente.post("/roles", json={"nombre": "   "})

    assert rol_creado.status_code == 201
    assert rol_creado.json() == {"id_rol": id_rol, "nombre": "INVENTARIO"}
    assert detalle.status_code == 200
    assert actualizado.status_code == 200
    assert actualizado.json()["nombre"] == "SUPERVISOR DE INVENTARIO"
    assert any(rol["id_rol"] == id_rol for rol in listado.json())
    assert eliminado.status_code == 204
    assert inexistente.status_code == 404
    assert nombre_duplicado.status_code == 409
    assert rol_asignado.status_code == 409
    assert invalidos.status_code == 422


def test_crud_de_categorias(tmp_path):
    ruta_base_datos = tmp_path / "productos.db"

    with TestClient(crear_app(ruta_base_datos)) as cliente:
        creada = cliente.post("/categorias", json={"nombre": "  Congelados  "})
        id_categoria = creada.json()["id_categoria"]
        detalle = cliente.get(f"/categorias/{id_categoria}")
        actualizada = cliente.put(
            f"/categorias/{id_categoria}",
            json={"nombre": "Congelados y fríos"},
        )
        listado = cliente.get("/categorias")
        eliminada = cliente.delete(f"/categorias/{id_categoria}")
        inexistente = cliente.get(f"/categorias/{id_categoria}")

    assert creada.status_code == 201
    assert creada.json()["nombre"] == "Congelados"
    assert detalle.status_code == 200
    assert actualizada.status_code == 200
    assert actualizada.json()["nombre"] == "Congelados y fríos"
    assert any(item["id_categoria"] == id_categoria for item in listado.json())
    assert eliminada.status_code == 204
    assert inexistente.status_code == 404


def test_crud_de_proveedores(tmp_path):
    ruta_base_datos = tmp_path / "productos.db"

    with TestClient(crear_app(ruta_base_datos)) as cliente:
        creado = cliente.post(
            "/proveedores",
            json={
                "nombre": "  Proveedor nuevo  ",
                "telefono": "3001234567",
                "email": "contacto@example.com",
            },
        )
        id_proveedor = creado.json()["id_proveedor"]
        detalle = cliente.get(f"/proveedores/{id_proveedor}")
        actualizado = cliente.put(
            f"/proveedores/{id_proveedor}",
            json={"nombre": "Proveedor editado", "telefono": None, "email": None},
        )
        listado = cliente.get("/proveedores")
        eliminado = cliente.delete(f"/proveedores/{id_proveedor}")
        inexistente = cliente.get(f"/proveedores/{id_proveedor}")

    assert creado.status_code == 201
    assert creado.json() == {
        "id_proveedor": id_proveedor,
        "nombre": "Proveedor nuevo",
        "telefono": "3001234567",
        "email": "contacto@example.com",
    }
    assert detalle.status_code == 200
    assert actualizado.status_code == 200
    assert actualizado.json()["nombre"] == "Proveedor editado"
    assert actualizado.json()["telefono"] is None
    assert any(item["id_proveedor"] == id_proveedor for item in listado.json())
    assert eliminado.status_code == 204
    assert inexistente.status_code == 404


@pytest.mark.parametrize(
    ("endpoint", "payload", "expected_status", "crear_existente"),
    [
        ("/categorias", {"nombre": "   "}, 422, False),
        ("/categorias", {"nombre": "Embutidos"}, 409, True),
        ("/proveedores", {"nombre": "   "}, 422, False),
    ],
)
def test_validacion_creacion_de_catalogos(
    tmp_path,
    endpoint,
    payload,
    expected_status,
    crear_existente,
):
    ruta_base_datos = tmp_path / "productos.db"

    with TestClient(crear_app(ruta_base_datos)) as cliente:
        if crear_existente:
            cliente.post(endpoint, json=payload)
        respuesta = cliente.post(endpoint, json=payload)

    assert respuesta.status_code == expected_status
    if expected_status == 409:
        assert respuesta.json()["detail"] == "Ya existe una categoría con ese nombre"


@pytest.mark.parametrize(
    ("endpoint", "mensaje"),
    [
        ("/categorias/1", "hay productos asociados a esta categoría"),
        ("/proveedores/1", "hay productos asociados a este proveedor"),
    ],
)
def test_no_se_eliminan_catalogos_referenciados(endpoint, mensaje, tmp_path):
    ruta_base_datos = tmp_path / "productos.db"
    ejecutar_script(obtener_ruta_esquema().parent / "productos.sql", ruta_base_datos)

    with TestClient(crear_app(ruta_base_datos)) as cliente:
        respuesta = cliente.delete(endpoint)

    assert respuesta.status_code == 409
    assert mensaje in respuesta.json()["detail"]


def test_claves_foraneas_rechazan_categoria_inexistente(tmp_path):
    ruta_base_datos = tmp_path / "productos.db"
    ruta_script = tmp_path / "producto_invalido.sql"
    ruta_script.write_text(
        """
        INSERT INTO productos (
            nombre, id_categoria, id_proveedor, unidad, precio_venta
        ) VALUES ('Producto inválido', 99, 99, 'UND', 1000);
        """,
        encoding="utf-8",
    )

    with pytest.raises(sqlite3.IntegrityError, match="FOREIGN KEY"):
        ejecutar_script(ruta_script, ruta_base_datos)


def test_migra_tabla_antigua_vacia(tmp_path):
    ruta_base_datos = tmp_path / "productos.db"
    with sqlite3.connect(ruta_base_datos) as conexion:
        conexion.execute(
            """
            CREATE TABLE productos (
                id_producto INTEGER PRIMARY KEY,
                codigo TEXT NOT NULL,
                nombre TEXT NOT NULL,
                descripcion TEXT NOT NULL,
                id_categoria INTEGER NOT NULL,
                id_proveedor INTEGER NOT NULL,
                precio_compra REAL NOT NULL,
                precio_venta REAL NOT NULL,
                stock INTEGER NOT NULL,
                stock_minimo INTEGER NOT NULL,
                estado TEXT NOT NULL
            )
            """
        )

    inicializar_base_datos(ruta_base_datos)
    with closing(sqlite3.connect(ruta_base_datos)) as conexion:
        columnas = {
            fila[1] for fila in conexion.execute("PRAGMA table_info(productos)")
        }

    assert {"unidad", "stock_actual", "activo"} <= columnas


def test_migracion_no_descarta_productos_de_la_tabla_antigua(tmp_path):
    ruta_base_datos = tmp_path / "productos.db"
    with sqlite3.connect(ruta_base_datos) as conexion:
        conexion.execute(
            "CREATE TABLE productos (id_producto INTEGER PRIMARY KEY, unidad TEXT)"
        )
        conexion.execute("INSERT INTO productos (id_producto, unidad) VALUES (1, 'KG')")

    with pytest.raises(RuntimeError, match="contiene productos del esquema anterior"):
        inicializar_base_datos(ruta_base_datos)


def test_crud_crear_ver_editar_y_eliminar_producto(tmp_path):
    ruta_base_datos = tmp_path / "productos.db"
    ejecutar_script(obtener_ruta_esquema().parent / "productos.sql", ruta_base_datos)
    producto = {
        "nombre": "Producto CRUD",
        "id_categoria": 1,
        "id_proveedor": 1,
        "unidad": "UND",
        "precio_venta": 1000,
        "stock_minimo": 2,
        "activo": True,
    }

    with TestClient(crear_app(ruta_base_datos)) as cliente:
        creado = cliente.post("/productos", json=producto)
        id_producto = creado.json()["id_producto"]
        detalle = cliente.get(f"/productos/{id_producto}")
        actualizado = cliente.put(
            f"/productos/{id_producto}",
            json={**producto, "nombre": "Producto actualizado", "stock_actual": 5},
        )
        eliminacion = cliente.delete(f"/productos/{id_producto}")
        detalle_borrado = cliente.get(f"/productos/{id_producto}")

    assert creado.status_code == 201
    assert creado.json()["categoria"] == "Embutidos"
    assert creado.json()["proveedor"] == "Cárnicos del Valle"
    assert detalle.status_code == 200
    assert actualizado.status_code == 200
    assert actualizado.json()["nombre"] == "Producto actualizado"
    assert creado.json()["stock_actual"] == 0
    assert actualizado.json()["stock_actual"] == 0
    assert eliminacion.status_code == 204
    assert detalle_borrado.status_code == 404


def test_no_se_puede_eliminar_producto_con_movimientos(tmp_path):
    ruta_base_datos = tmp_path / "productos.db"
    ejecutar_script(obtener_ruta_esquema().parent / "productos.sql", ruta_base_datos)

    with TestClient(crear_app(ruta_base_datos)) as cliente:
        respuesta = cliente.delete("/productos/1")
        producto = cliente.get("/productos/1")

    assert respuesta.status_code == 409
    assert "movimientos asociados" in respuesta.json()["detail"]
    assert producto.status_code == 200


def test_validaciones_de_producto_y_referencias(tmp_path):
    ruta_base_datos = tmp_path / "productos.db"
    ejecutar_script(obtener_ruta_esquema().parent / "productos.sql", ruta_base_datos)
    producto = {
        "nombre": "Producto inválido",
        "id_categoria": 99,
        "id_proveedor": 99,
        "unidad": "UND",
        "precio_venta": 0,
        "stock_minimo": 0,
        "activo": True,
    }

    with TestClient(crear_app(ruta_base_datos)) as cliente:
        invalido = cliente.post("/productos", json=producto)
        referencia_invalida = cliente.post(
            "/productos",
            json={**producto, "nombre": "Producto sin referencia", "precio_venta": 1},
        )
        inexistente = cliente.put("/productos/9999", json={
            **producto,
            "id_categoria": 1,
            "id_proveedor": 1,
            "precio_venta": 1,
        })

    assert invalido.status_code == 422
    assert referencia_invalida.status_code == 409
    assert inexistente.status_code == 404


def test_movimientos_actualizan_stock_y_guardan_usuario(tmp_path):
    ruta_base_datos = tmp_path / "productos.db"
    ejecutar_script(obtener_ruta_esquema().parent / "productos.sql", ruta_base_datos)

    with TestClient(crear_app(ruta_base_datos)) as cliente:
        ingreso = cliente.post(
            "/movimientos",
            json={
                "id_producto": 1,
                "id_usuario": 1,
                "tipo": "ENTRADA",
                "cantidad": 2,
                "observacion": "Reposición",
            },
        )
        salida = cliente.post(
            "/movimientos",
            json={
                "id_producto": 1,
                "id_usuario": 2,
                "tipo": "SALIDA",
                "cantidad": 3.5,
                "observacion": "Venta mostrador",
            },
        )
        producto = cliente.get("/productos/1")
        movimientos = cliente.get("/movimientos")

    assert ingreso.status_code == 201
    assert ingreso.json()["tipo"] == "ENTRADA"
    assert ingreso.json()["usuario"] == "Administrador"
    assert salida.status_code == 201
    assert salida.json()["tipo"] == "SALIDA"
    assert salida.json()["usuario"] == "Laura Vendedora"
    assert producto.json()["stock_actual"] == 15
    assert len(movimientos.json()) == 18
    assert movimientos.json()[0]["id_movimiento"] == salida.json()["id_movimiento"]


def test_salida_mayor_al_stock_es_rechazada_sin_cambiar_inventario(tmp_path):
    ruta_base_datos = tmp_path / "productos.db"
    ejecutar_script(obtener_ruta_esquema().parent / "productos.sql", ruta_base_datos)

    with TestClient(crear_app(ruta_base_datos)) as cliente:
        respuesta = cliente.post(
            "/movimientos",
            json={
                "id_producto": 3,
                "id_usuario": 2,
                "tipo": "SALIDA",
                "cantidad": 91,
            },
        )
        producto = cliente.get("/productos/3")
        movimientos = cliente.get("/movimientos")

    assert respuesta.status_code == 409
    assert respuesta.json()["detail"] == "Stock insuficiente. Disponible: 90.0"
    assert producto.json()["stock_actual"] == 90
    assert len(movimientos.json()) == 16


@pytest.mark.parametrize(
    ("payload", "status_code", "detail"),
    [
        (
            {"id_producto": 3, "id_usuario": 2, "tipo": "SALIDA", "cantidad": 0},
            422,
            None,
        ),
        (
            {"id_producto": 3, "id_usuario": 2, "tipo": "SALIDA", "cantidad": 1.5},
            422,
            "La cantidad de un producto por unidades debe ser entera",
        ),
        (
            {"id_producto": 3, "id_usuario": 99, "tipo": "ENTRADA", "cantidad": 1},
            404,
            "Usuario no encontrado o inactivo",
        ),
        (
            {"id_producto": 999, "id_usuario": 2, "tipo": "ENTRADA", "cantidad": 1},
            404,
            "Producto no encontrado",
        ),
    ],
)
def test_validaciones_de_movimientos(tmp_path, payload, status_code, detail):
    ruta_base_datos = tmp_path / "productos.db"
    ejecutar_script(obtener_ruta_esquema().parent / "productos.sql", ruta_base_datos)

    with TestClient(crear_app(ruta_base_datos)) as cliente:
        respuesta = cliente.post("/movimientos", json=payload)

    assert respuesta.status_code == status_code
    if detail is not None:
        assert respuesta.json()["detail"] == detail


def test_editar_movimiento_actualiza_solo_campos_permitidos_y_stock(tmp_path):
    ruta_base_datos = tmp_path / "productos.db"
    ejecutar_script(obtener_ruta_esquema().parent / "productos.sql", ruta_base_datos)

    with TestClient(crear_app(ruta_base_datos)) as cliente:
        respuesta = cliente.put(
            "/movimientos/9",
            json={
                "cantidad": 2.5,
                "id_usuario": 1,
                "observacion": "Venta corregida",
            },
        )
        producto = cliente.get("/productos/1")
        historial = cliente.get("/movimientos")

    assert respuesta.status_code == 200
    assert respuesta.json()["tipo"] == "SALIDA"
    assert respuesta.json()["id_producto"] == 1
    assert respuesta.json()["cantidad"] == 2.5
    assert respuesta.json()["usuario"] == "Administrador"
    assert respuesta.json()["observacion"] == "Venta corregida"
    original = next(item for item in historial.json() if item["id_movimiento"] == 9)
    assert respuesta.json()["fecha"] == original["fecha"]
    assert producto.json()["stock_actual"] == 17.5
    assert original["tipo"] == "SALIDA"
    assert original["id_producto"] == 1
    assert original["cantidad"] == 2.5


def test_editar_ingreso_ajusta_stock_por_diferencia(tmp_path):
    ruta_base_datos = tmp_path / "productos.db"
    ejecutar_script(obtener_ruta_esquema().parent / "productos.sql", ruta_base_datos)

    with TestClient(crear_app(ruta_base_datos)) as cliente:
        respuesta = cliente.put(
            "/movimientos/4",
            json={
                "cantidad": 17,
                "id_usuario": 2,
                "observacion": "Ingreso corregido",
            },
        )
        producto = cliente.get("/productos/4")

    assert respuesta.status_code == 200
    assert respuesta.json()["tipo"] == "ENTRADA"
    assert respuesta.json()["id_producto"] == 4
    assert respuesta.json()["cantidad"] == 17
    assert respuesta.json()["usuario"] == "Laura Vendedora"
    assert producto.json()["stock_actual"] == 14.75


def test_editar_movimiento_rechaza_cambiar_producto_o_tipo(tmp_path):
    ruta_base_datos = tmp_path / "productos.db"
    ejecutar_script(obtener_ruta_esquema().parent / "productos.sql", ruta_base_datos)

    with TestClient(crear_app(ruta_base_datos)) as cliente:
        respuesta = cliente.put(
            "/movimientos/9",
            json={
                "cantidad": 2,
                "id_usuario": 1,
                "observacion": None,
                "id_producto": 2,
                "tipo": "ENTRADA",
            },
        )
        producto = cliente.get("/productos/1")
        historial = cliente.get("/movimientos")

    assert respuesta.status_code == 422
    assert producto.json()["stock_actual"] == 16.5
    original = next(item for item in historial.json() if item["id_movimiento"] == 9)
    assert original["tipo"] == "SALIDA"
    assert original["id_producto"] == 1
    assert original["cantidad"] == 3.5


@pytest.mark.parametrize(
    ("id_movimiento", "cantidad", "detail"),
    [
        (9, 21, "No se puede aplicar el cambio: dejaría el stock negativo"),
        (1, 1, "No se puede aplicar el cambio: dejaría el stock negativo"),
    ],
)
def test_editar_movimiento_rechaza_ajuste_que_deja_stock_negativo(
    tmp_path,
    id_movimiento,
    cantidad,
    detail,
):
    ruta_base_datos = tmp_path / "productos.db"
    ejecutar_script(obtener_ruta_esquema().parent / "productos.sql", ruta_base_datos)

    with TestClient(crear_app(ruta_base_datos)) as cliente:
        respuesta = cliente.put(
            f"/movimientos/{id_movimiento}",
            json={"cantidad": cantidad, "id_usuario": 1, "observacion": "Ajuste"},
        )
        producto = cliente.get("/productos/1")
        historial = cliente.get("/movimientos")

    assert respuesta.status_code == 409
    assert respuesta.json()["detail"] == detail
    assert producto.json()["stock_actual"] == 16.5
    original = next(
        item for item in historial.json() if item["id_movimiento"] == id_movimiento
    )
    assert original["cantidad"] == (3.5 if id_movimiento == 9 else 20)


def test_editar_movimiento_valida_usuario_unidad_y_existencia(tmp_path):
    ruta_base_datos = tmp_path / "productos.db"
    ejecutar_script(obtener_ruta_esquema().parent / "productos.sql", ruta_base_datos)

    with TestClient(crear_app(ruta_base_datos)) as cliente:
        unidad_invalida = cliente.put(
            "/movimientos/11",
            json={"cantidad": 1.5, "id_usuario": 1, "observacion": None},
        )
        usuario_invalido = cliente.put(
            "/movimientos/9",
            json={"cantidad": 3, "id_usuario": 999, "observacion": None},
        )
        inexistente = cliente.put(
            "/movimientos/9999",
            json={"cantidad": 1, "id_usuario": 1, "observacion": None},
        )
        cantidad_cero = cliente.put(
            "/movimientos/9",
            json={"cantidad": 0, "id_usuario": 1, "observacion": None},
        )

    assert unidad_invalida.status_code == 422
    assert usuario_invalido.status_code == 404
    assert usuario_invalido.json()["detail"] == "Usuario no encontrado o inactivo"
    assert inexistente.status_code == 404
    assert inexistente.json()["detail"] == "Movimiento no encontrado"
    assert cantidad_cero.status_code == 422


def test_unidad_no_se_cambia_si_el_producto_tiene_movimientos(tmp_path):
    ruta_base_datos = tmp_path / "productos.db"
    ejecutar_script(obtener_ruta_esquema().parent / "productos.sql", ruta_base_datos)
    producto = {
        "nombre": "Chorizo santarrosano",
        "id_categoria": 1,
        "id_proveedor": 1,
        "unidad": "KG",
        "precio_venta": 3800,
        "stock_minimo": 20,
        "activo": True,
    }

    with TestClient(crear_app(ruta_base_datos)) as cliente:
        respuesta = cliente.put("/productos/3", json=producto)
        detalle = cliente.get("/productos/3")

    assert respuesta.status_code == 409
    assert "no se puede cambiar la unidad" in respuesta.json()["detail"].lower()
    assert detalle.json()["unidad"] == "UND"
