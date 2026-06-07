import os
from pathlib import Path

from fastapi import HTTPException

from compartido.sftp.conexion import asegurar_remoto, conectar as ssh_conectar
from catalogo.analizador_estatico import CATALOGO

from repositorio import get_report, save_report, stats as db_stats

SAMPLES_DIR  = Path(os.environ.get("SAMPLES_DIR", "/samples"))
SANDBOX_HOST = os.environ.get("SANDBOX_HOST", "sandbox")
SANDBOX_PORT = int(os.environ.get("SANDBOX_PORT", "22"))
SANDBOX_USER = os.environ.get("SANDBOX_USER", "root")
KEY_PATH     = os.environ.get("KEY_PATH", "/keys/id_rsa")


def ssh():
    """Abre una conexión SSH al sandbox."""
    return ssh_conectar(SANDBOX_HOST, SANDBOX_PORT, SANDBOX_USER, KEY_PATH, label="sandbox")


def ejecutar(sha256: str, analizador, **opts):
    """Conecta al sandbox, asegura la muestra por SFTP y corre el analizador."""
    local = SAMPLES_DIR / sha256
    if not local.exists():
        raise HTTPException(404, f"Sample {sha256} not found")
    remoto = f"/samples/{sha256}"
    client = ssh()
    try:
        asegurar_remoto(client, str(local), remoto)
        return analizador.fn(client, remoto, **opts)
    finally:
        client.close()


def run_tool(sha256: str, tool: str, **opts):
    """Ejecuta un comando del catálogo, usando la caché si procede."""
    analizador = CATALOGO.get(tool)
    if analizador is None:
        raise HTTPException(404, f"Herramienta desconocida: {tool}")
    # Solo cacheamos los análisis deterministas (no los paramétricos/guiados).
    if analizador.cacheable:
        cached = get_report(sha256, tool)
        if cached is not None:
            return cached
    result = ejecutar(sha256, analizador, **opts)
    if analizador.cacheable:
        save_report(sha256, tool, result)
    return result


def estado_componentes() -> dict:
    """Comprueba engine, base de datos y sandbox para la página de estado."""
    estado = {"engine": "ok", "db": "ok", "sandbox": "ok"}
    try:
        db_stats()
    except Exception as e:  # noqa: BLE001
        estado["db"] = f"error: {e}"
    try:
        ssh().close()
    except Exception as e:  # noqa: BLE001
        estado["sandbox"] = f"error: {e}"
    estado["ok"] = all(estado[k] == "ok" for k in ("engine", "db", "sandbox"))
    return estado
