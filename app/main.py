from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Response
from fastapi.staticfiles import StaticFiles

from app.database import inicializar_base_datos, obtener_ruta_base_datos
from app.rutas.movimientos import router as movimientos_router
from app.rutas.productos import router as productos_router

RUTA_ESTATICOS = Path(__file__).parent / "static"


def crear_app(database_path: str | Path | None = None) -> FastAPI:
    ruta_base_datos = (
        Path(database_path) if database_path is not None else obtener_ruta_base_datos()
    )

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        inicializar_base_datos(ruta_base_datos)
        app.state.database_path = ruta_base_datos
        yield

    app = FastAPI(title="Catálogo de productos", version="1.0.0", lifespan=lifespan)
    app.mount(
        "/static",
        StaticFiles(directory=RUTA_ESTATICOS),
        name="static",
    )
    app.add_api_route("/", inicio, methods=["GET"], response_class=Response)
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
    app.include_router(productos_router)
    app.include_router(movimientos_router)
    return app


def inicio():
    return Response(
        content=(RUTA_ESTATICOS / "productos" / "index.html").read_text(encoding="utf-8"),
        media_type="text/html",
        headers={"Cache-Control": "no-cache, must-revalidate"},
    )


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


app = crear_app()
