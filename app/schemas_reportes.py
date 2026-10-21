from pydantic import BaseModel


class InventarioCategoria(BaseModel):
    categoria: str
    productos: int
    bajo_minimo: int
    valor_inventario: float


class StockBajo(BaseModel):
    id_producto: int
    nombre: str
    categoria: str
    proveedor: str
    proveedor_telefono: str | None
    unidad: str
    stock_actual: float
    stock_minimo: float
    faltante: float


class MovimientosProveedor(BaseModel):
    proveedor: str
    unidad: str
    movimientos: int
    entradas: float
    salidas: float


class MovimientosUsuario(BaseModel):
    usuario: str
    rol: str
    unidad: str
    movimientos: int
    entradas: float
    salidas: float
