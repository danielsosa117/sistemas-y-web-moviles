"""Cambia la contraseña de un usuario desde la terminal.

Uso:
    python -m app.establecer_password admin@salsamentaria.com
    docker compose exec api python -m app.establecer_password admin@salsamentaria.com
"""

import argparse
from getpass import getpass

from app.database import inicializar_base_datos, obtener_ruta_base_datos
from app.seguridad import hashear_password
from app.servicios.autenticacion import actualizar_password_por_email


def main() -> None:
    parser = argparse.ArgumentParser(description="Establece la contraseña de un usuario.")
    parser.add_argument("email", help="Correo del usuario")
    parser.add_argument(
        "--password",
        help="Contraseña nueva (si se omite, se pide por teclado sin mostrarla)",
    )
    argumentos = parser.parse_args()

    password = argumentos.password or getpass("Contraseña nueva: ")
    if len(password) < 8:
        parser.error("La contraseña debe tener al menos 8 caracteres.")

    ruta = obtener_ruta_base_datos()
    inicializar_base_datos(ruta)
    if not actualizar_password_por_email(ruta, argumentos.email, hashear_password(password)):
        parser.error(f"No existe un usuario con el correo {argumentos.email}.")
    print(f"Contraseña actualizada para {argumentos.email}.")


if __name__ == "__main__":
    main()
