import sqlite3

from fastapi import APIRouter, HTTPException, Request, Response, status

from app.schemas import Rol, RolEntrada
from app.servicios.roles import (
    actualizar_rol,
    crear_rol,
    eliminar_rol,
    listar_roles,
    obtener_rol,
)

router = APIRouter()


@router.get("/roles", response_model=list[Rol])
def obtener_roles(request: Request) -> list[Rol]:
    return listar_roles(request.app.state.database_path)


@router.get("/roles/{id_rol}", response_model=Rol)
def obtener_detalle_rol(id_rol: int, request: Request) -> Rol:
    rol = obtener_rol(request.app.state.database_path, id_rol)
    if rol is None:
        raise HTTPException(status_code=404, detail="Rol no encontrado")
    return rol


@router.post("/roles", response_model=Rol, status_code=status.HTTP_201_CREATED)
def agregar_rol(rol: RolEntrada, request: Request) -> Rol:
    try:
        return crear_rol(request.app.state.database_path, rol.model_dump())
    except sqlite3.IntegrityError as error:
        raise HTTPException(
            status_code=409,
            detail="Ya existe un rol con ese nombre",
        ) from error


@router.put("/roles/{id_rol}", response_model=Rol)
def editar_rol(id_rol: int, rol: RolEntrada, request: Request) -> Rol:
    try:
        actualizado = actualizar_rol(
            request.app.state.database_path,
            id_rol,
            rol.model_dump(),
        )
    except sqlite3.IntegrityError as error:
        raise HTTPException(
            status_code=409,
            detail="Ya existe un rol con ese nombre",
        ) from error
    if actualizado is None:
        raise HTTPException(status_code=404, detail="Rol no encontrado")
    return actualizado


@router.delete("/roles/{id_rol}", status_code=status.HTTP_204_NO_CONTENT)
def borrar_rol(id_rol: int, request: Request) -> Response:
    try:
        eliminado = eliminar_rol(request.app.state.database_path, id_rol)
    except sqlite3.IntegrityError as error:
        raise HTTPException(
            status_code=409,
            detail="No se puede eliminar: hay usuarios asignados a este rol",
        ) from error
    if not eliminado:
        raise HTTPException(status_code=404, detail="Rol no encontrado")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
