import pytest


@pytest.fixture(autouse=True)
def autenticacion_desactivada_por_defecto(monkeypatch):
    """Las pruebas de CRUD existentes llaman a la API sin iniciar sesión.

    Las pruebas de autenticación (test_auth.py) activan la autenticación
    explícitamente con AUTH_ACTIVADA=1.
    """
    monkeypatch.setenv("AUTH_ACTIVADA", "0")
