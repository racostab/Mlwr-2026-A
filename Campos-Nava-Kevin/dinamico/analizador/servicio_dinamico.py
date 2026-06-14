#!/usr/bin/env python3
"""Servicio HOST que dispara el análisis dinámico desde la web.

¿Por qué existe? El análisis dinámico NO puede vivir en Docker: necesita
`VBoxManage` (controlar la VM) y `sudo iptables` (firewall del host). La web y el
motor sí están contenedorizados. Este servicio es el **puente**: un FastAPI que
corre en el host (fuera de Docker) y expone por HTTP el flujo que ya orquesta
`analizador_dinamico.analizar()`. La web (Django, en Docker) lo llama vía
`host.docker.internal`. Así VBoxManage/iptables se quedan en el host y el
aislamiento del laboratorio no se toca.

La VM es un recurso ÚNICO: las detonaciones se ejecutan EN SERIE (una cola con un
worker). Cada job restaura el snapshot limpio, aísla, verifica y detona; si el
gate de aislamiento falla, el job queda en estado `error` y NADA se detona.

Arranque (en el host):
    pip install -e ".[dinamico]"          # fastapi + uvicorn + python-multipart
    bash dinamico/scripts/servicio_dinamico.sh        # escucha en :8002
"""
import os
import queue
import shutil
import tempfile
import threading
import uuid
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

import analizador_dinamico
import mitre
import post_analisis
import red
import snapshot
from compartido.configuracion import kali as cfg

app = FastAPI(title="Malware Lab — servicio dinámico (host)")
# La web corre en otro origen (otro contenedor/puerto); permitir su llamada.
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"],
)

# Límite de tiempo de detonación que aceptamos desde la web (segundos).
MAX_SEGUNDOS = 120
SUBIDAS = Path(tempfile.gettempdir()) / "mlwr_dinamico_subidas"
SUBIDAS.mkdir(parents=True, exist_ok=True)

_jobs: dict[str, dict] = {}          # id → estado del job
_cola: "queue.Queue[str]" = queue.Queue()
_lock = threading.Lock()


def _nuevo_job(filename: str, segundos: int, ruta: Path) -> dict:
    jid = uuid.uuid4().hex[:12]
    job = {
        "id": jid,
        "filename": filename,
        "segundos": segundos,
        "estado": "en_cola",          # en_cola → ejecutando → listo | error
        "mensaje": "En cola; la VM atiende una muestra a la vez.",
        "creado": datetime.now().isoformat(timespec="seconds"),
        "destino": None,
        "archivos": [],
        "error": None,
        "_ruta": str(ruta),           # interno: ruta local de la muestra subida
    }
    with _lock:
        _jobs[jid] = job
    return job


def _publico(job: dict) -> dict:
    """El job sin los campos internos (prefijados con _)."""
    return {k: v for k, v in job.items() if not k.startswith("_")}


def _worker() -> None:
    """Procesa la cola de detonaciones EN SERIE (la VM es recurso único)."""
    while True:
        jid = _cola.get()
        job = _jobs.get(jid)
        if job is None:
            _cola.task_done()
            continue
        ruta = job["_ruta"]
        try:
            job["estado"] = "ejecutando"
            job["mensaje"] = ("Restaurando estado limpio, aislando, verificando y "
                              "detonando bajo strace…")
            destino = analizador_dinamico.analizar(ruta, job["segundos"])
            job["destino"] = str(destino)
            job["archivos"] = sorted(p.name for p in Path(destino).glob("*"))
            # Post-análisis: el volcado de memoria pasa por el motor ESTÁTICO
            # (mismas reglas YARA que en disco; sin duplicarlas en dinamico/).
            job["estado"] = "analizando_volcado"
            job["mensaje"] = "Escaneando el volcado de memoria con YARA/strings…"
            job["post_analisis"] = post_analisis.analizar_volcado(destino)
            # Mapa MITRE ATT&CK (strace + YARA del volcado → técnicas/grafo).
            job["mitre"] = mitre.mapear(destino)
            job["estado"] = "listo"
            job["mensaje"] = f"Detonación completa. Resultados en {destino}/"
        except Exception as e:  # noqa: BLE001 — cualquier fallo deja el job en error
            job["estado"] = "error"
            job["error"] = str(e)
            job["mensaje"] = f"Abortado: {e}"
        finally:
            # La muestra subida ya no se necesita en el host.
            try:
                os.remove(ruta)
            except OSError:
                pass
            # Dejar la VM LIMPIA tras la detonación: restaurar el snapshot base
            # DESCARTA el estado contaminado (la muestra y cualquier residuo:
            # procesos, persistencia, archivos) y apaga la VM. Así no queda malware
            # "vivo" entre análisis lanzados desde el front; el siguiente job vuelve
            # a restaurar al arrancar (idempotente). Best-effort: si falla, no rompe
            # el job ya terminado.
            try:
                vm = cfg()["vm_name"]
                if snapshot.existe(vm):
                    snapshot.restaurar(vm)  # apaga la VM y revierte al estado limpio
                    job["mensaje"] += " · VM restaurada al estado limpio."
            except Exception as e:  # noqa: BLE001 — limpieza best-effort
                job["mensaje"] += f" · (no se pudo restaurar la VM: {e})"
            _cola.task_done()


threading.Thread(target=_worker, name="detonador", daemon=True).start()


@app.get("/estado")
def estado() -> dict:
    """Readiness del lado dinámico para que la web sepa si puede ofrecerlo."""
    c = cfg()
    vm = c["vm_name"]
    vbox = red.disponible()
    existe = vbox and red.vm_existe(vm)
    return {
        "vbox_disponible": vbox,
        "vm": vm,
        "vm_existe": existe,
        "vm_corriendo": existe and red.vm_corriendo(vm),
        "snapshot_limpio": existe and snapshot.existe(vm),
        "en_cola": _cola.qsize(),
    }


@app.post("/analisis")
async def crear_analisis(file: UploadFile, segundos: int = Form(20)) -> dict:
    """Encola una muestra para detonarla en la VM aislada. Devuelve el id del job."""
    if not 1 <= segundos <= MAX_SEGUNDOS:
        raise HTTPException(400, f"segundos debe estar entre 1 y {MAX_SEGUNDOS}")
    nombre = os.path.basename(file.filename or "muestra")
    destino = SUBIDAS / f"{uuid.uuid4().hex[:8]}_{nombre}"
    with destino.open("wb") as out:
        shutil.copyfileobj(file.file, out)
    job = _nuevo_job(nombre, segundos, destino)
    _cola.put(job["id"])
    return _publico(job)


@app.get("/analisis")
def listar() -> list[dict]:
    """Jobs recientes (más nuevos primero)."""
    with _lock:
        jobs = sorted(_jobs.values(), key=lambda j: j["creado"], reverse=True)
    return [_publico(j) for j in jobs]


@app.get("/analisis/{jid}")
def ver(jid: str) -> dict:
    job = _jobs.get(jid)
    if job is None:
        raise HTTPException(404, "job no encontrado")
    return _publico(job)


@app.get("/analisis/{jid}/archivo/{nombre}")
def descargar(jid: str, nombre: str) -> FileResponse:
    """Descarga un archivo de resultados del job (strace.log, post_analisis.json,
    stdout/stderr.log, volcado…). Solo sirve archivos dentro de la carpeta del job."""
    job = _jobs.get(jid)
    if job is None:
        raise HTTPException(404, "job no encontrado")
    destino = job.get("destino")
    if not destino:
        raise HTTPException(409, "el job aún no tiene resultados")
    # `basename` evita path traversal (../): solo el nombre, sin rutas.
    ruta = (Path(destino) / os.path.basename(nombre)).resolve()
    if Path(destino).resolve() not in ruta.parents or not ruta.is_file():
        raise HTTPException(404, "archivo no encontrado")
    return FileResponse(ruta, filename=ruta.name, media_type="application/octet-stream")


if __name__ == "__main__":
    import uvicorn

    puerto = int(os.environ.get("DYNAMIC_PORT", "8002"))
    uvicorn.run(app, host="0.0.0.0", port=puerto)
