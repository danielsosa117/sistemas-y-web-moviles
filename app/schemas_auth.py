from pydantic import BaseModel, Field

from app.schemas import CorreoUsuario, NombreCatalogo


class LoginEntrada(BaseModel):
    email: str = Field(min_length=1, max_length=254)
    password: str = Field(min_length=1, max_length=128)


class UsuarioSesion(BaseModel):
    id_usuario: int
    nombre: str
    email: str
    rol: str


class RespuestaLogin(BaseModel):
    access_token: str
    token_type: str = "bearer"
    usuario: UsuarioSesion


class CambioPassword(BaseModel):
    password_actual: str = Field(min_length=1, max_length=128)
    password_nueva: str = Field(min_length=8, max_length=128)


class UsuarioCreacion(BaseModel):
    nombre: NombreCatalogo
    email: CorreoUsuario
    password: str = Field(min_length=8, max_length=128)
    id_rol: int = Field(gt=0)
