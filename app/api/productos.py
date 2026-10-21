import sqlite3

from fastapi import APIRouter, HTTPException, Request, Response, status

from app.servicios.productos import (
    UnidadProductoInmutable,
    actualizar_producto,
    crear_producto,
    eliminar_producto,
    listar_catalogos,
    listar_productos,
    obtener_producto,
)
from app.schemas import Producto, ProductoEntrada

router = APIRouter(tags=["Productos"])


@router.get("/productos", response_model=list[Producto])
def obtener_productos(request: Request) -> list[Producto]:
    return listar_productos(request.app.state.database_path)


@router.get("/productos/{id_producto}", response_model=Producto)
def obtener_detalle_producto(id_producto: int, request: Request) -> Producto:
    producto = obtener_producto(request.app.state.database_path, id_producto)
    if producto is None:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return producto


@router.get("/catalogos")
def obtener_catalogos(request: Request) -> dict[str, list[dict]]:
    return listar_catalogos(request.app.state.database_path)


@router.post(
    "/productos",
    response_model=Producto,
    status_code=status.HTTP_201_CREATED,
)
def agregar_producto(producto: ProductoEntrada, request: Request) -> Producto:
    try:
        return crear_producto(
            request.app.state.database_path,
            producto.model_dump(),
        )
    except sqlite3.IntegrityError as error:
        raise HTTPException(
            status_code=409,
            detail="Nombre de producto duplicado o categoría/proveedor inexistente",
        ) from error


@router.put("/productos/{id_producto}", response_model=Producto)
def editar_producto(
    id_producto: int,
    producto: ProductoEntrada,
    request: Request,
) -> Producto:
    try:
        actualizado = actualizar_producto(
            request.app.state.database_path,
            id_producto,
            producto.model_dump(),
        )
    except UnidadProductoInmutable as error:
        raise HTTPException(
            status_code=409,
            detail="No se puede cambiar la unidad de un producto con stock o movimientos",
        ) from error
    except sqlite3.IntegrityError as error:
        raise HTTPException(
            status_code=409,
            detail="Nombre de producto duplicado o categoría/proveedor inexistente",
        ) from error
    if actualizado is None:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return actualizado


@router.delete(
    "/productos/{id_producto}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def borrar_producto(id_producto: int, request: Request) -> Response:
    try:
        eliminado = eliminar_producto(request.app.state.database_path, id_producto)
    except sqlite3.IntegrityError as error:
        raise HTTPException(
            status_code=409,
            detail="No se puede eliminar: el producto tiene movimientos asociados",
        ) from error
    if not eliminado:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
