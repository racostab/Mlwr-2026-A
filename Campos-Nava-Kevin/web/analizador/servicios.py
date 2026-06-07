import os

import requests
from django.shortcuts import render

ENGINE_URL = os.environ.get("ENGINE_URL", "http://localhost:8001")


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


def index(request):
    catalogo = _catalogo()
    files    = request.FILES.getlist("file")

    if request.method == "POST" and files:
        mode      = request.POST.get("mode", "default")
        min_len   = request.POST.get("min_len", "4")
        etiquetas = {t["id"]: t["etiqueta"] for t in catalogo}

        # En modo personalizado corre lo que el usuario marque; si no marca nada
        # (o en modo por defecto) corre el conjunto por defecto.
        custom = mode == "custom"
        seleccion = request.POST.getlist("tools") if custom else []
        # Comandos personalizados: los que el usuario escriba en la barra
        # (uno por línea en `cmd_libre`; con JS son los chips añadidos).
        cmds = []
        if custom:
            cmds += request.POST.get("cmd_libre", "").splitlines()
        cmds = [c.strip() for c in cmds if c.strip()]
        # Si solo eligió/escribió comandos, no forzamos el set por defecto.
        tools = seleccion or ([] if cmds else _tools_por_defecto(catalogo))

        reports, errors = [], []
        for f in files:
            try:
                reports.append(_analizar(f, tools, etiquetas, min_len, cmds))
            except Exception as e:
                errors.append({"filename": f.name, "error": str(e)})

        if not reports:
            msg = "; ".join(f"{e['filename']}: {e['error']}" for e in errors)
            return render(request, "analizador/index.html", {"error": msg, "tools": catalogo})

        return render(
            request,
            "analizador/results.html",
            {"reports": reports, "errors": errors},
        )

    return render(request, "analizador/index.html", {"tools": catalogo})


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
