"""Integración end-to-end contra el lab levantado.

Ejercita la cadena real web→engine→(SFTP)→sandbox: sube una muestra y corre un
análisis. Se SALTA automáticamente si el engine no está disponible, así que la
suite también pasa sin Docker (los demás tests son unitarios).

Para correrlo de verdad:  docker compose up -d  &&  pytest tests/test_integracion.py
"""
import hashlib
import os

import pytest
import requests

ENGINE = os.environ.get("ENGINE_URL", "http://localhost:8001")


def _engine_disponible() -> bool:
    try:
        return requests.get(f"{ENGINE}/health", timeout=2).status_code == 200
    except Exception:
        return False


pytestmark = pytest.mark.skipif(
    not _engine_disponible(), reason=f"engine no disponible en {ENGINE} (lab apagado)"
)


def test_tools_no_vacio():
    r = requests.get(f"{ENGINE}/tools", timeout=10)
    r.raise_for_status()
    assert any(t["id"] == "hash" for t in r.json())


def test_subir_y_analizar_por_sftp():
    # Subir la muestra al engine...
    contenido = b"\x7fELF muestra de prueba del laboratorio"
    up = requests.post(
        f"{ENGINE}/samples",
        files={"file": ("muestra.bin", contenido)},
        timeout=30,
    )
    up.raise_for_status()
    sha = up.json()["sha256"]

    # ...y correr `hash` en el sandbox (esto envía la muestra por SFTP).
    r = requests.get(f"{ENGINE}/samples/{sha}/run/hash", timeout=60)
    r.raise_for_status()
    resultado = r.json()["result"]
    assert resultado["SHA256"] == hashlib.sha256(contenido).hexdigest()
