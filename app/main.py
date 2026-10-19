from contextlib import asynccontextmanager
import os
from pathlib import Path

from fastapi import Depends, FastAPI, Response
from fastapi.staticfiles import StaticFiles

from app.database import (
    cargar_datos_iniciales,
    inicializar_base_datos,
    obtener_ruta_base_datos,
)
from app.api.auth import controlar_acceso, router as auth_router
from app.api.categorias import router as categorias_router
from app.api.movimientos import router as movimientos_router
from app.api.proveedores import router as proveedores_router
from app.api.productos import router as productos_router
from app.api.roles import router as roles_router
from app.api.usuarios import router as usuarios_router
from app.servicios.autenticacion import aplicar_passwords_desde_entorno

RUTA_ESTATICOS = Path(__file__).parent / "static"


def crear_app(database_path: str | Path | None = None) -> FastAPI:
    ruta_base_datos = (
        Path(database_path) if database_path is not None else obtener_ruta_base_datos()
    )

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        inicializar_base_datos(ruta_base_datos)
        if os.getenv("CARGAR_DATOS_EJEMPLO") == "1":
            cargar_datos_iniciales(ruta_base_datos)
        aplicar_passwords_desde_entorno(ruta_base_datos)
        app.state.database_path = ruta_base_datos
        yield

    app = FastAPI(title="Catálogo de productos", version="1.0.0", lifespan=lifespan)
    app.state.auth_activada = os.getenv("AUTH_ACTIVADA", "1") != "0"
    app.mount(
        "/static",
        StaticFiles(directory=RUTA_ESTATICOS),
        name="static",
    )
    app.add_api_route("/", inicio, methods=["GET"], response_class=Response)
    app.add_api_route("/salud", salud, methods=["GET"])
    app.add_api_route(
        "/productos-ui",
        pagina_productos,
        methods=["GET"],
        response_class=Response,
    )
    app.add_api_route(
        "/movimientos-ui",
        pagina_movimientos,
        methods=["GET"],
        response_class=Response,
    )
    app.add_api_route(
        "/categorias-ui",
        pagina_categorias,
        methods=["GET"],
        response_class=Response,
    )
    app.add_api_route(
        "/proveedores-ui",
        pagina_proveedores,
        methods=["GET"],
        response_class=Response,
    )
    app.add_api_route(
        "/usuarios-ui",
        pagina_usuarios,
        methods=["GET"],
        response_class=Response,
    )
    app.add_api_route(
        "/roles-ui",
        pagina_roles,
        methods=["GET"],
        response_class=Response,
    )
    app.add_api_route(
        "/login-ui",
        pagina_login,
        methods=["GET"],
        response_class=Response,
    )
    app.add_api_route(
        "/cambiar-password-ui",
        pagina_cambiar_password,
        methods=["GET"],
        response_class=Response,
    )
    app.add_api_route(
        "/recuperar-password-ui",
        pagina_recuperar_password,
        methods=["GET"],
        response_class=Response,
    )
    app.include_router(auth_router)
    protegido = [Depends(controlar_acceso)]
    app.include_router(productos_router, dependencies=protegido)
    app.include_router(movimientos_router, dependencies=protegido)
    app.include_router(categorias_router, dependencies=protegido)
    app.include_router(proveedores_router, dependencies=protegido)
    app.include_router(roles_router, dependencies=protegido)
    app.include_router(usuarios_router, dependencies=protegido)
    return app


def inicio():
    return Response(
        content=(RUTA_ESTATICOS / "productos" / "index.html").read_text(encoding="utf-8"),
        media_type="text/html",
        headers={"Cache-Control": "no-cache, must-revalidate"},
    )


def salud() -> dict[str, str]:
    return {"estado": "ok"}


def pagina_productos():
    return inicio()


def pagina_movimientos():
    return Response(
        content=(RUTA_ESTATICOS / "movimientos" / "index.html").read_text(
            encoding="utf-8"
        ),
        media_type="text/html",
        headers={"Cache-Control": "no-cache, must-revalidate"},
    )


def pagina_categorias():
    return pagina_catalogo("categorias")


def pagina_proveedores():
    return pagina_catalogo("proveedores")


def pagina_usuarios():
    return pagina_catalogo("usuarios")


def pagina_roles():
    return pagina_catalogo("roles")


def pagina_login():
    return pagina_catalogo("login")


def pagina_cambiar_password():
    return pagina_catalogo("password")


def pagina_recuperar_password():
    return pagina_catalogo("recuperar-password")


def pagina_catalogo(modulo: str) -> Response:
    return Response(
        content=(RUTA_ESTATICOS / modulo / "index.html").read_text(encoding="utf-8"),
        media_type="text/html",
        headers={"Cache-Control": "no-cache, must-revalidate"},
    )


app = crear_app()
