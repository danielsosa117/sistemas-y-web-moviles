from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints


class Producto(BaseModel):
    id_producto: int
    nombre: str
    id_categoria: int
    categoria: str
    id_proveedor: int
    proveedor: str
    unidad: Literal["KG", "UND"]
    precio_venta: float
    stock_actual: float
    stock_minimo: float
    activo: bool


class ProductoEntrada(BaseModel):
    nombre: str = Field(min_length=1, max_length=100)
    id_categoria: int = Field(gt=0)
    id_proveedor: int = Field(gt=0)
    unidad: Literal["KG", "UND"]
    precio_venta: float = Field(gt=0)
    stock_minimo: float = Field(ge=0)
    activo: bool = True


class MovimientoCreacion(BaseModel):
    id_producto: int = Field(gt=0)
    id_usuario: int = Field(gt=0)
    tipo: Literal["ENTRADA", "SALIDA"]
    cantidad: float = Field(gt=0, allow_inf_nan=False)
    observacion: str | None = Field(default=None, max_length=500)


class MovimientoActualizacion(BaseModel):
    model_config = ConfigDict(extra="forbid")
    cantidad: float = Field(gt=0, allow_inf_nan=False)
    id_usuario: int = Field(gt=0)
    observacion: str | None = Field(default=None, max_length=500)


class Movimiento(BaseModel):
    id_movimiento: int
    id_producto: int
    producto: str
    unidad: Literal["KG", "UND"]
    id_usuario: int
    usuario: str
    tipo: Literal["ENTRADA", "SALIDA"]
    cantidad: float
    fecha: str
    observacion: str | None


NombreCatalogo = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=100),
]

CorreoUsuario = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=3,
        max_length=254,
        pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$",
    ),
]


class CategoriaEntrada(BaseModel):
    nombre: NombreCatalogo


class Categoria(BaseModel):
    id_categoria: int
    nombre: str


class ProveedorEntrada(BaseModel):
    nombre: NombreCatalogo
    telefono: str | None = Field(default=None, max_length=30)
    email: str | None = Field(default=None, max_length=254)


class Proveedor(BaseModel):
    id_proveedor: int
    nombre: str
    telefono: str | None
    email: str | None


class Rol(BaseModel):
    id_rol: int
    nombre: str


class RolEntrada(BaseModel):
    nombre: NombreCatalogo


class UsuarioActualizacion(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nombre: NombreCatalogo
    email: CorreoUsuario
    id_rol: int = Field(gt=0)
    activo: bool


class Usuario(BaseModel):
    id_usuario: int
    nombre: str
    email: str
    id_rol: int
    rol: str
    activo: bool
