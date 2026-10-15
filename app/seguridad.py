"""Contraseñas, tokens de sesión y reglas de permisos.

Solo usa la biblioteca estándar de Python, así que no agrega dependencias.
- Contraseñas: PBKDF2-HMAC-SHA256 con sal aleatoria.
- Tokens: JWT firmado con HS256 (cabecera.carga.firma).
"""

import base64
import hashlib
import hmac
import json
import os
import secrets
import time

ROL_ADMIN = "ADMINISTRADOR"
ITERACIONES = 600_000
VIGENCIA_TOKEN_SEGUNDOS = 8 * 60 * 60

# Si no se define SECRET_KEY, se usa una clave aleatoria por proceso:
# las sesiones se cierran cada vez que se reinicia la aplicación.
_CLAVE_ALEATORIA = secrets.token_hex(32)

# Hash de una contraseña inexistente; se usa para que el login tarde lo mismo
# cuando el correo no existe y no revelar qué correos están registrados.
HASH_FALSO = "pbkdf2_sha256$600000$00000000000000000000000000000000$" + "0" * 64

# Rutas que solo puede usar el administrador (con cualquier método).
RUTAS_SOLO_ADMIN = ("/usuarios", "/roles")


def hashear_password(password: str, iteraciones: int = ITERACIONES) -> str:
    sal = secrets.token_hex(16)
    derivado = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), sal.encode("ascii"), iteraciones
    ).hex()
    return f"pbkdf2_sha256${iteraciones}${sal}${derivado}"


def verificar_password(password: str, hash_guardado: str) -> bool:
    try:
        algoritmo, iteraciones, sal, esperado = hash_guardado.split("$")
        if algoritmo != "pbkdf2_sha256":
            return False
        iteraciones = int(iteraciones)
        if iteraciones < 1:
            return False
        derivado = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), sal.encode("ascii"), iteraciones
        ).hex()
    except (ValueError, AttributeError, UnicodeError):
        return False
    return hmac.compare_digest(derivado, esperado)


def obtener_clave_secreta() -> bytes:
    return (os.getenv("SECRET_KEY") or _CLAVE_ALEATORIA).encode("utf-8")


def _codificar(datos: bytes) -> str:
    return base64.urlsafe_b64encode(datos).rstrip(b"=").decode("ascii")


def _decodificar(texto: str) -> bytes:
    return base64.urlsafe_b64decode(texto + "=" * (-len(texto) % 4))


def _firmar(contenido: str) -> str:
    firma = hmac.new(
        obtener_clave_secreta(), contenido.encode("ascii"), hashlib.sha256
    ).digest()
    return _codificar(firma)


def crear_token(
    id_usuario: int,
    vigencia_segundos: int = VIGENCIA_TOKEN_SEGUNDOS,
    ahora: float | None = None,
) -> str:
    emitido = int(time.time() if ahora is None else ahora)
    cabecera = _codificar(
        json.dumps({"alg": "HS256", "typ": "JWT"}, separators=(",", ":")).encode()
    )
    carga = _codificar(
        json.dumps(
            {"sub": str(id_usuario), "iat": emitido, "exp": emitido + vigencia_segundos},
            separators=(",", ":"),
        ).encode()
    )
    contenido = f"{cabecera}.{carga}"
    return f"{contenido}.{_firmar(contenido)}"


def leer_token(token: str) -> dict | None:
    """Devuelve la carga del token si la firma y la vigencia son válidas."""
    try:
        cabecera_b64, carga_b64, firma = token.split(".")
        if not hmac.compare_digest(firma, _firmar(f"{cabecera_b64}.{carga_b64}")):
            return None
        if json.loads(_decodificar(cabecera_b64)).get("alg") != "HS256":
            return None
        carga = json.loads(_decodificar(carga_b64))
        if int(carga["exp"]) <= time.time():
            return None
    except (ValueError, KeyError, TypeError, AttributeError):
        return None
    return carga


def _bajo_ruta(ruta: str, prefijo: str) -> bool:
    return ruta == prefijo or ruta.startswith(prefijo + "/")


def tiene_permiso(rol: str, metodo: str, ruta: str) -> bool:
    """Reglas de acceso.

    - ADMINISTRADOR: todo.
    - Resto de roles (VENDEDOR): consultar todo salvo usuarios y roles, y
      registrar movimientos. No pueden crear, editar ni borrar nada más.
    """
    if rol == ROL_ADMIN:
        return True
    if any(_bajo_ruta(ruta, prefijo) for prefijo in RUTAS_SOLO_ADMIN):
        return False
    metodo = metodo.upper()
    if metodo in ("GET", "HEAD", "OPTIONS"):
        return True
    return metodo == "POST" and ruta == "/movimientos"
