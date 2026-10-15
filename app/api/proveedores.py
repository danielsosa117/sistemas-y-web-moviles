import sqlite3

from fastapi import APIRouter, HTTPException, Request, Response, status

from app.servicios.catalogos import (
    actualizar_proveedor,
    crear_proveedor,
    eliminar_proveedor,
    listar_proveedores,
    obtener_proveedor,
)
from app.schemas import Proveedor, ProveedorEntrada

router = APIRouter()


@router.get("/proveedores", response_model=list[Proveedor])
def obtener_proveedores(request: Request) -> list[Proveedor]:
    return listar_proveedores(request.app.state.database_path)


@router.get("/proveedores/{id_proveedor}", response_model=Proveedor)
def obtener_detalle_proveedor(id_proveedor: int, request: Request) -> Proveedor:
    proveedor = obtener_proveedor(request.app.state.database_path, id_proveedor)
    if proveedor is None:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")
    return proveedor


@router.post(
    "/proveedores",
    response_model=Proveedor,
    status_code=status.HTTP_201_CREATED,
)
def agregar_proveedor(proveedor: ProveedorEntrada, request: Request) -> Proveedor:
    return crear_proveedor(
        request.app.state.database_path,
        proveedor.model_dump(),
    )


@router.put("/proveedores/{id_proveedor}", response_model=Proveedor)
def editar_proveedor(
    id_proveedor: int,
    proveedor: ProveedorEntrada,
    request: Request,
) -> Proveedor:
    actualizado = actualizar_proveedor(
        request.app.state.database_path,
        id_proveedor,
        proveedor.model_dump(),
    )
    if actualizado is None:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")
    return actualizado


@router.delete(
    "/proveedores/{id_proveedor}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def borrar_proveedor(id_proveedor: int, request: Request) -> Response:
    try:
        eliminado = eliminar_proveedor(request.app.state.database_path, id_proveedor)
    except sqlite3.IntegrityError as error:
        raise HTTPException(
            status_code=409,
            detail="No se puede eliminar: hay productos asociados a este proveedor",
        ) from error
    if not eliminado:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
