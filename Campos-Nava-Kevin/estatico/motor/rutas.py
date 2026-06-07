import hashlib

from fastapi import APIRouter, HTTPException, Query, UploadFile

from catalogo.analizador_estatico import catalogo_publico, comandos_extra, yara_reglas

import servicios
from repositorio import get_sample, list_samples, save_sample, stats as db_stats

router = APIRouter()


@router.get("/health")
def health():
    return {"status": "ok"}


@router.get("/tools")
def tools():
    """Catálogo de analizadores disponibles (única fuente de verdad)."""
    return catalogo_publico()


@router.get("/commands")
def commands():
    """Comandos listos para usar en el análisis personalizado (desde JSON)."""
    return {"comandos": comandos_extra()}


@router.get("/yara/rules")
def yara_rules():
    """Reglas YARA cargadas en el sandbox."""
    client = servicios.ssh()
    try:
        return {"archivos": yara_reglas(client)}
    finally:
        client.close()


@router.get("/stats")
def stats():
    """Métricas del lab: muestras, reportes y desglose por comando."""
    return db_stats()


@router.get("/status")
def status():
    """Estado de los componentes: engine, base de datos y sandbox."""
    return servicios.estado_componentes()


@router.post("/samples")
async def upload(file: UploadFile):
    content = await file.read()
    sha256  = hashlib.sha256(content).hexdigest()
    dest    = servicios.SAMPLES_DIR / sha256
    if not dest.exists():
        dest.write_bytes(content)
    save_sample(sha256, file.filename, len(content))
    return {"sha256": sha256, "filename": file.filename, "size": len(content)}


@router.get("/samples")
def all_samples():
    return list_samples()


@router.get("/samples/{sha256}")
def one_sample(sha256: str):
    s = get_sample(sha256)
    if s is None:
        raise HTTPException(404, f"Sample {sha256} not found")
    return s


@router.get("/samples/{sha256}/run/{tool}")
def run(
    sha256: str,
    tool: str,
    min_len: int = Query(4, ge=1, le=512),
    length: int = Query(4096, ge=0, le=1_048_576),
    cmd: str = Query(""),
):
    """Ejecuta cualquier comando del catálogo sobre la muestra.

    `min_len` (strings), `length` (xxd) y `cmd` (comando guiado) se pasan a todos
    los analizadores; los que no los usan los ignoran (cada función acepta **opts).
    """
    result = servicios.run_tool(sha256, tool, min_len=min_len, length=length, cmd=cmd)
    return {"tool": tool, "result": result}
