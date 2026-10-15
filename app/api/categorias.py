import sqlite3

from fastapi import APIRouter, HTTPException, Request, Response, status

from app.servicios.catalogos import (
    actualizar_categoria,
    crear_categoria,
    eliminar_categoria,
    listar_categorias,
    obtener_categoria,
)
from app.schemas import Categoria, CategoriaEntrada

router = APIRouter()


@router.get("/categorias", response_model=list[Categoria])
def obtener_categorias(request: Request) -> list[Categoria]:
    return listar_categorias(request.app.state.database_path)


@router.get("/categorias/{id_categoria}", response_model=Categoria)
def obtener_detalle_categoria(id_categoria: int, request: Request) -> Categoria:
    categoria = obtener_categoria(request.app.state.database_path, id_categoria)
    if categoria is None:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    return categoria


@router.post(
    "/categorias",
    response_model=Categoria,
    status_code=status.HTTP_201_CREATED,
)
def agregar_categoria(categoria: CategoriaEntrada, request: Request) -> Categoria:
    try:
        return crear_categoria(
            request.app.state.database_path,
            categoria.model_dump(),
        )
    except sqlite3.IntegrityError as error:
        raise HTTPException(
            status_code=409,
            detail="Ya existe una categoría con ese nombre",
        ) from error


@router.put("/categorias/{id_categoria}", response_model=Categoria)
def editar_categoria(
    id_categoria: int,
    categoria: CategoriaEntrada,
    request: Request,
) -> Categoria:
    try:
        actualizada = actualizar_categoria(
            request.app.state.database_path,
            id_categoria,
            categoria.model_dump(),
        )
    except sqlite3.IntegrityError as error:
        raise HTTPException(
            status_code=409,
            detail="Ya existe una categoría con ese nombre",
        ) from error
    if actualizada is None:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    return actualizada


@router.delete("/categorias/{id_categoria}", status_code=status.HTTP_204_NO_CONTENT)
def borrar_categoria(id_categoria: int, request: Request) -> Response:
    try:
        eliminada = eliminar_categoria(request.app.state.database_path, id_categoria)
    except sqlite3.IntegrityError as error:
        raise HTTPException(
            status_code=409,
            detail="No se puede eliminar: hay productos asociados a esta categoría",
        ) from error
    if not eliminada:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
