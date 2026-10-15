import sqlite3

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.schemas import Usuario
from app.schemas_auth import (
    CambioPassword,
    LoginEntrada,
    RespuestaLogin,
    UsuarioCreacion,
    UsuarioSesion,
)
from app.seguridad import (
    HASH_FALSO,
    ROL_ADMIN,
    crear_token,
    hashear_password,
    leer_token,
    tiene_permiso,
    verificar_password,
)
from app.servicios.autenticacion import (
    actualizar_password,
    buscar_cuenta_por_email,
    crear_usuario_con_password,
    obtener_usuario_activo,
)
from app.servicios.usuarios import obtener_usuario

router = APIRouter(tags=["Autenticación"])
esquema_bearer = HTTPBearer(auto_error=False)


def _no_autenticado(detalle: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detalle,
        headers={"WWW-Authenticate": "Bearer"},
    )


def _resolver_usuario(
    request: Request,
    credenciales: HTTPAuthorizationCredentials | None,
) -> dict:
    if credenciales is None:
        raise _no_autenticado("Inicia sesión para continuar")
    carga = leer_token(credenciales.credentials)
    if carga is None:
        raise _no_autenticado("La sesión no es válida o ya venció")
    try:
        id_usuario = int(carga["sub"])
    except (KeyError, TypeError, ValueError):
        raise _no_autenticado("La sesión no es válida o ya venció") from None
    usuario = obtener_usuario_activo(request.app.state.database_path, id_usuario)
    if usuario is None:
        raise _no_autenticado("La cuenta no existe o está inactiva")
    return usuario


def usuario_autenticado(
    request: Request,
    credenciales: HTTPAuthorizationCredentials | None = Depends(esquema_bearer),
) -> dict:
    return _resolver_usuario(request, credenciales)


def controlar_acceso(
    request: Request,
    credenciales: HTTPAuthorizationCredentials | None = Depends(esquema_bearer),
) -> dict | None:
    """Dependencia para proteger routers completos según el rol del usuario."""
    if not request.app.state.auth_activada:
        return None
    usuario = _resolver_usuario(request, credenciales)
    if not tiene_permiso(usuario["rol"], request.method, request.url.path):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para realizar esta acción",
        )
    return usuario


def requiere_admin(usuario: dict = Depends(usuario_autenticado)) -> dict:
    if usuario["rol"] != ROL_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo el administrador puede realizar esta acción",
        )
    return usuario


def _sesion(cuenta: dict) -> dict:
    return {
        "id_usuario": cuenta["id_usuario"],
        "nombre": cuenta["nombre"],
        "email": cuenta["email"],
        "rol": cuenta["rol"],
    }


@router.post("/auth/login", response_model=RespuestaLogin)
def iniciar_sesion(datos: LoginEntrada, request: Request) -> dict:
    ruta = request.app.state.database_path
    cuenta = buscar_cuenta_por_email(ruta, datos.email)
    # Se verifica siempre una contraseña, exista o no el correo, para que el
    # tiempo de respuesta no revele qué correos están registrados.
    valida = verificar_password(
        datos.password,
        cuenta["password_hash"] if cuenta else HASH_FALSO,
    )
    if cuenta is None or not cuenta["activo"] or not valida:
        raise _no_autenticado("Correo o contraseña incorrectos")
    return {
        "access_token": crear_token(cuenta["id_usuario"]),
        "token_type": "bearer",
        "usuario": _sesion(cuenta),
    }


@router.get("/auth/yo", response_model=UsuarioSesion)
def consultar_sesion(usuario: dict = Depends(usuario_autenticado)) -> dict:
    return _sesion(usuario)


@router.put("/auth/password", status_code=status.HTTP_204_NO_CONTENT)
def cambiar_password(
    datos: CambioPassword,
    request: Request,
    usuario: dict = Depends(usuario_autenticado),
) -> Response:
    if not verificar_password(datos.password_actual, usuario["password_hash"]):
        # 400 y no 401: un 401 haría que el frontend cierre la sesión.
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La contraseña actual no es correcta",
        )
    actualizar_password(
        request.app.state.database_path,
        usuario["id_usuario"],
        hashear_password(datos.password_nueva),
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/auth/usuarios",
    response_model=Usuario,
    status_code=status.HTTP_201_CREATED,
)
def registrar_usuario(
    datos: UsuarioCreacion,
    request: Request,
    _admin: dict = Depends(requiere_admin),
) -> dict:
    ruta = request.app.state.database_path
    try:
        id_usuario = crear_usuario_con_password(
            ruta,
            {"nombre": datos.nombre, "email": datos.email, "id_rol": datos.id_rol},
            hashear_password(datos.password),
        )
    except sqlite3.IntegrityError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El correo ya está registrado o el rol no existe",
        ) from error
    return obtener_usuario(ruta, id_usuario)
