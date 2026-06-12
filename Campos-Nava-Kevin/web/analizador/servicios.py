import os

import requests
from django.shortcuts import render

ENGINE_URL = os.environ.get("ENGINE_URL", "http://localhost:8001")
# El análisis dinámico vive en el HOST (VBoxManage + iptables), fuera de Docker.
# La web lo alcanza por el gateway del host (ver docker-compose: extra_hosts).
DYNAMIC_URL = os.environ.get("DYNAMIC_URL", "http://localhost:8002")


def _tools_por_defecto(catalogo: list[dict]) -> list[str]:
    """Comandos del modo "por defecto", tomados del catálogo del engine.

    El engine es la única fuente de verdad: marca cada comando con `por_defecto`
    en `/tools`. Así no duplicamos aquí la lista (antes era una constante a mano).
    """
    return [t["id"] for t in catalogo if t.get("por_defecto")]


def _get(path: str, **params):
    r = requests.get(f"{ENGINE_URL}{path}", params=params, timeout=120)
    r.raise_for_status()
    return r.json()


def _catalogo() -> list[dict]:
    """Catálogo de comandos del engine; lista vacía si no responde."""
    try:
        return _get("/tools")
    except Exception:
        return []


def _tipo(result) -> str:
    """Clasifica el resultado para que la plantilla lo renderice genéricamente."""
    if isinstance(result, dict):
        return "matches" if "matches" in result else "kv"
    if isinstance(result, list):
        return "lines"
    return "text"


def _analizar(f, tools, etiquetas, min_len, cmds=None) -> dict:
    """Sube una muestra y corre sobre ella el conjunto de comandos elegido."""
    cmds = cmds or []
    up = requests.post(
        f"{ENGINE_URL}/samples",
        files={"file": (f.name, f.read(), f.content_type)},
        timeout=60,
    )
    up.raise_for_status()
    meta = up.json()
    sha  = meta["sha256"]

    resultados = []  # orden de ejecución, un tab por comando
    mapa       = {}  # id → resultado, para el resumen
    for tool in tools:
        res = _get(f"/samples/{sha}/run/{tool}", min_len=min_len)["result"]
        resultados.append({
            "id": tool,
            "etiqueta": etiquetas.get(tool, tool),
            "result": res,
            "kind": _tipo(res),
        })
        mapa[tool] = res

    # Comandos elegidos de la lista y/o escritos por el usuario: cada uno se
    # ejecuta en el sandbox y se añade como una pestaña más del reporte.
    for c in cmds:
        c = c.strip()
        if not c:
            continue
        res = _get(f"/samples/{sha}/run/custom", cmd=c)["result"]
        resultados.append({
            "id": "custom",
            "etiqueta": f"$ {c}",
            "result": res,
            "kind": _tipo(res),
        })

    return {
        "sha256":     sha,
        "filename":   meta["filename"],
        "size":       meta["size"],
        "resultados": resultados,
        "mapa":       mapa,
    }


def _indices_experimentos(request) -> list[int]:
    """Índices de los experimentos presentes en el envío (campos `file_<n>`).

    La web manda cada experimento con sus campos sufijados por un índice
    (`file_0`, `mode_0`, `tools_0`…). Aquí se descubren esos índices a partir de
    los grupos de archivos subidos, en orden.
    """
    return sorted(
        int(k[5:]) for k in request.FILES
        if k.startswith("file_") and k[5:].isdigit()
    )


def _experimento(request, i: int, catalogo: list[dict], etiquetas: dict) -> dict | None:
    """Procesa un experimento (grupo de N muestras + su selección de comandos).

    Devuelve `{"reports": [...], "errors": [...]}` o `None` si el grupo no trae
    archivos. Replica el comportamiento de un análisis, pero acotado a los campos
    sufijados con el índice `i` (cada experimento elige sus propios comandos).
    """
    files = request.FILES.getlist(f"file_{i}")
    if not files:
        return None

    mode    = request.POST.get(f"mode_{i}", "default")
    min_len = request.POST.get(f"min_len_{i}", "4")

    # En modo personalizado corre lo que el usuario marque; si no marca nada
    # (o en modo por defecto) corre el conjunto por defecto.
    custom    = mode == "custom"
    seleccion = request.POST.getlist(f"tools_{i}") if custom else []
    # Comandos personalizados: los que el usuario escriba en la barra (uno por
    # línea en `cmd_libre_<i>`; con JS son los chips añadidos). Se ejecutan por el
    # comando guiado, que los valida contra la whitelist del backend.
    cmds = []
    if custom:
        cmds += request.POST.get(f"cmd_libre_{i}", "").splitlines()
    cmds = [c.strip() for c in cmds if c.strip()]
    # Si solo eligió/escribió comandos, no forzamos el set por defecto.
    tools = seleccion or ([] if cmds else _tools_por_defecto(catalogo))

    reports, errors = [], []
    for f in files:
        try:
            reports.append(_analizar(f, tools, etiquetas, min_len, cmds))
        except Exception as e:
            errors.append({"filename": f.name, "error": str(e)})
    return {"reports": reports, "errors": errors}


def index(request):
    catalogo = _catalogo()

    if request.method == "POST":
        etiquetas = {t["id"]: t["etiqueta"] for t in catalogo}

        # Cada experimento es un grupo independiente de muestras + sus comandos.
        experimentos = []
        for numero, i in enumerate(_indices_experimentos(request), start=1):
            exp = _experimento(request, i, catalogo, etiquetas)
            if exp is None:
                continue
            exp["numero"]     = numero
            exp["n_muestras"] = len(exp["reports"])
            experimentos.append(exp)

        if experimentos:
            return render(request, "analizador/results.html",
                          {"experimentos": experimentos})

        return render(request, "analizador/index.html",
                      {"error": "Sube al menos una muestra para analizar.",
                       "tools": catalogo})

    return render(request, "analizador/index.html", {"tools": catalogo})


def dynamic(request):
    """Análisis dinámico: detona una muestra en la VM Kali aislada (lado host).

    La web no toca VirtualBox ni el firewall; solo habla por HTTP con el servicio
    del host (`DYNAMIC_URL`). En POST sube la muestra y la encola; en GET muestra
    el estado del lab dinámico y los jobs recientes.
    """
    error = None

    if request.method == "POST" and request.FILES.get("file"):
        f = request.FILES["file"]
        segundos = request.POST.get("segundos", "20")
        try:
            requests.post(
                f"{DYNAMIC_URL}/analisis",
                files={"file": (f.name, f.read(), f.content_type)},
                data={"segundos": segundos},
                timeout=30,
            ).raise_for_status()
        except Exception as e:  # noqa: BLE001
            error = (f"No se pudo encolar la detonación: {e}. "
                     "¿Está corriendo el servicio dinámico en el host "
                     "(bash dinamico/scripts/servicio_dinamico.sh)?")

    estado, jobs = None, []
    try:
        estado = requests.get(f"{DYNAMIC_URL}/estado", timeout=5).json()
        jobs = requests.get(f"{DYNAMIC_URL}/analisis", timeout=5).json()
    except Exception as e:  # noqa: BLE001
        if error is None:
            error = (f"Servicio dinámico no disponible: {e}. "
                     "Arráncalo en el host con "
                     "bash dinamico/scripts/servicio_dinamico.sh")

    activos = any(j.get("estado") in ("en_cola", "ejecutando", "analizando_volcado")
                  for j in jobs)
    return render(request, "analizador/dynamic.html",
                  {"estado": estado, "jobs": jobs, "error": error,
                   "hay_activos": activos})


def history(request):
    try:
        samples = _get("/samples")
    except Exception as e:
        return render(request, "analizador/history.html", {"error": str(e), "samples": []})
    return render(request, "analizador/history.html", {"samples": samples})


def rules(request):
    """Reglas YARA cargadas en el sandbox."""
    try:
        archivos = _get("/yara/rules")["archivos"]
        return render(request, "analizador/rules.html", {"archivos": archivos})
    except Exception as e:
        return render(request, "analizador/rules.html", {"error": str(e), "archivos": []})


def stats(request):
    """Métricas del lab."""
    try:
        data = _get("/stats")
        return render(request, "analizador/stats.html", {"stats": data})
    except Exception as e:
        return render(request, "analizador/stats.html", {"error": str(e)})


def status(request):
    """Estado de los componentes del lab."""
    try:
        data = _get("/status")
        return render(request, "analizador/status.html", {"estado": data})
    except Exception as e:
        return render(request, "analizador/status.html", {"error": str(e)})


def docs(request):
    """Página de documentación / ayuda."""
    return render(request, "analizador/docs.html", {"tools": _catalogo()})
