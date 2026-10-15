from fastapi import APIRouter, HTTPException, Request, status

from app.movimientos import (
    AjusteStockInvalido,
    CantidadIncompatibleConUnidad,
    MovimientoNoEncontrado,
    ProductoNoEncontrado,
    StockInsuficiente,
    UsuarioNoEncontrado,
    actualizar_movimiento,
    listar_movimientos,
    registrar_movimiento,
)
from app.schemas import Movimiento, MovimientoActualizacion, MovimientoCreacion

router = APIRouter()


@router.get("/movimientos", response_model=list[Movimiento])
def obtener_movimientos(request: Request) -> list[Movimiento]:
    return listar_movimientos(request.app.state.database_path)


@router.post(
    "/movimientos",
    response_model=Movimiento,
    status_code=status.HTTP_201_CREATED,
)
def agregar_movimiento(
    movimiento: MovimientoCreacion,
    request: Request,
) -> Movimiento:
    try:
        return registrar_movimiento(
            request.app.state.database_path,
            movimiento.model_dump(),
        )
    except ProductoNoEncontrado as error:
        raise HTTPException(status_code=404, detail="Producto no encontrado") from error
    except UsuarioNoEncontrado as error:
        raise HTTPException(
            status_code=404,
            detail="Usuario no encontrado o inactivo",
        ) from error
    except StockInsuficiente as error:
        raise HTTPException(
            status_code=409,
            detail=f"Stock insuficiente. Disponible: {error.disponible}",
        ) from error
    except CantidadIncompatibleConUnidad as error:
        raise HTTPException(
            status_code=422,
            detail="La cantidad de un producto por unidades debe ser entera",
        ) from error
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error


@router.put("/movimientos/{id_movimiento}", response_model=Movimiento)
def editar_movimiento(
    id_movimiento: int,
    cambios: MovimientoActualizacion,
    request: Request,
) -> Movimiento:
    try:
        return actualizar_movimiento(
            request.app.state.database_path,
            id_movimiento,
            cambios.model_dump(),
        )
    except MovimientoNoEncontrado as error:
        raise HTTPException(status_code=404, detail="Movimiento no encontrado") from error
    except UsuarioNoEncontrado as error:
        raise HTTPException(
            status_code=404,
            detail="Usuario no encontrado o inactivo",
        ) from error
    except CantidadIncompatibleConUnidad as error:
        raise HTTPException(
            status_code=422,
            detail="La cantidad de un producto por unidades debe ser entera",
        ) from error
    except AjusteStockInvalido as error:
        raise HTTPException(
            status_code=409,
            detail="No se puede aplicar el cambio: dejaría el stock negativo",
        ) from error
