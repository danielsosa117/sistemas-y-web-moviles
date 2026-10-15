from contextlib import closing
import os
from pathlib import Path
import sqlite3


def obtener_ruta_base_datos() -> Path:
    return Path(os.getenv("DATABASE_PATH", "data/productos.db"))


def obtener_ruta_esquema() -> Path:
    return Path(__file__).parent.parent / "sql" / "esquema.sql"


def inicializar_base_datos(ruta: Path) -> None:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(ruta)) as conexion, conexion:
        conexion.execute("PRAGMA foreign_keys = ON")
        conexion.row_factory = sqlite3.Row
        columnas = {
            fila["name"]
            for fila in conexion.execute("PRAGMA table_info(productos)")
        }
        columnas_modelo = {"unidad", "stock_actual", "activo"}
        if columnas and not columnas_modelo.issubset(columnas):
            cantidad = conexion.execute("SELECT COUNT(*) FROM productos").fetchone()[0]
            if cantidad:
                raise RuntimeError(
                    "La base de datos contiene productos del esquema anterior. "
                    "Haz una copia de data/productos.db y migra esos registros "
                    "antes de iniciar la aplicación."
                )
            conexion.execute("DROP TABLE productos")

        script_esquema = obtener_ruta_esquema().read_text(encoding="utf-8")
        conexion.executescript(script_esquema)


def obtener_ruta_datos_ejemplo() -> Path:
    return Path(__file__).parent.parent / "sql" / "productos.sql"


def cargar_datos_iniciales(ruta: Path, script: Path | None = None) -> bool:
    """Carga los datos de ejemplo solo si la base está vacía (tabla roles sin filas).

    Devuelve True si cargó los datos y False si ya había información.
    """
    script = script or obtener_ruta_datos_ejemplo()
    with closing(sqlite3.connect(ruta)) as conexion, conexion:
        conexion.execute("PRAGMA foreign_keys = ON")
        if conexion.execute("SELECT COUNT(*) FROM roles").fetchone()[0] > 0:
            return False
        conexion.executescript(script.read_text(encoding="utf-8"))
    return True
