from datetime import date

from fastapi import APIRouter, HTTPException, Request

from app.schemas_reportes import (
    InventarioCategoria,
    MovimientosProveedor,
    MovimientosUsuario,
    StockBajo,
)
from app.servicios.reportes import (
    inventario_por_categoria,
    movimientos_por_proveedor,
    movimientos_por_usuario,
    stock_bajo,
)

router = APIRouter(prefix="/reportes", tags=["Reportes"])


def _periodo(desde: date | None, hasta: date | None) -> tuple[str | None, str | None]:
    if desde and hasta and desde > hasta:
        raise HTTPException(
            status_code=422,
            detail="La fecha inicial no puede ser posterior a la final",
        )
    return (
        desde.isoformat() if desde else None,
        hasta.isoformat() if hasta else None,
    )


@router.get("/inventario-por-categoria", response_model=list[InventarioCategoria])
def reporte_inventario_por_categoria(request: Request) -> list[dict]:
    return inventario_por_categoria(request.app.state.database_path)


@router.get("/stock-bajo", response_model=list[StockBajo])
def reporte_stock_bajo(request: Request) -> list[dict]:
    return stock_bajo(request.app.state.database_path)


@router.get("/movimientos-por-proveedor", response_model=list[MovimientosProveedor])
def reporte_movimientos_por_proveedor(
    request: Request,
    desde: date | None = None,
    hasta: date | None = None,
) -> list[dict]:
    inicio, fin = _periodo(desde, hasta)
    return movimientos_por_proveedor(request.app.state.database_path, inicio, fin)


@router.get("/movimientos-por-usuario", response_model=list[MovimientosUsuario])
def reporte_movimientos_por_usuario(
    request: Request,
    desde: date | None = None,
    hasta: date | None = None,
) -> list[dict]:
    inicio, fin = _periodo(desde, hasta)
    return movimientos_por_usuario(request.app.state.database_path, inicio, fin)
