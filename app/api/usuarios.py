import sqlite3

from fastapi import APIRouter, HTTPException, Request

from app.schemas import Rol, Usuario, UsuarioActualizacion
from app.servicios.usuarios import (
    actualizar_usuario,
    listar_roles,
    listar_usuarios,
    obtener_usuario,
)

router = APIRouter()


@router.get("/roles", response_model=list[Rol])
def obtener_roles(request: Request) -> list[Rol]:
    return listar_roles(request.app.state.database_path)


@router.get("/usuarios", response_model=list[Usuario])
def obtener_usuarios(request: Request) -> list[Usuario]:
    return listar_usuarios(request.app.state.database_path)


@router.get("/usuarios/{id_usuario}", response_model=Usuario)
def obtener_detalle_usuario(id_usuario: int, request: Request) -> Usuario:
    usuario = obtener_usuario(request.app.state.database_path, id_usuario)
    if usuario is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return usuario


@router.put("/usuarios/{id_usuario}", response_model=Usuario)
def editar_usuario(
    id_usuario: int,
    usuario: UsuarioActualizacion,
    request: Request,
) -> Usuario:
    try:
        actualizado = actualizar_usuario(
            request.app.state.database_path,
            id_usuario,
            usuario.model_dump(),
        )
    except sqlite3.IntegrityError as error:
        raise HTTPException(
            status_code=409,
            detail="El correo ya está registrado o el rol no existe",
        ) from error
    if actualizado is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return actualizado
