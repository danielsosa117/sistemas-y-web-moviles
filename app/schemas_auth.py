from pydantic import BaseModel, ConfigDict, Field

from app.schemas import CorreoUsuario, NombreCatalogo


class LoginEntrada(BaseModel):
    email: str = Field(min_length=1, max_length=254)
    password: str = Field(min_length=1, max_length=128)


class UsuarioSesion(BaseModel):
    id_usuario: int
    nombre: str
    email: str
    rol: str
    requiere_cambio_password: bool


class RespuestaLogin(BaseModel):
    access_token: str
    token_type: str = "bearer"
    usuario: UsuarioSesion


class CambioPassword(BaseModel):
    password_actual: str = Field(min_length=1, max_length=128)
    password_nueva: str = Field(min_length=8, max_length=128)


class UsuarioCreacion(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nombre: NombreCatalogo
    email: CorreoUsuario
    id_rol: int = Field(gt=0)


class UsuarioCreacionRespuesta(BaseModel):
    usuario: UsuarioSesion
    contrasena_temporal: str


class RecuperacionPassword(BaseModel):
    email: CorreoUsuario
    password_nueva: str = Field(min_length=8, max_length=128)
