import os

import requests
from django.shortcuts import render

ENGINE_URL = os.environ.get("ENGINE_URL", "http://localhost:8001")


def _get(path: str, **params):
    r = requests.get(f"{ENGINE_URL}{path}", params=params, timeout=120)
    r.raise_for_status()
    return r.json()


def index(request):
    if request.method == "POST" and request.FILES.get("file"):
        f = request.FILES["file"]
        mode    = request.POST.get("mode", "default")
        extras  = request.POST.getlist("extras")
        min_len = request.POST.get("min_len", "4")

        # strings y ssdeep son opcionales: solo en modo personalizado y si se marcan.
        # El resto (hash, file, entropy, exiftool, readelf) son obligatorios.
        run_strings = mode == "custom" and "strings" in extras
        run_ssdeep  = mode == "custom" and "ssdeep" in extras

        try:
            up = requests.post(
                f"{ENGINE_URL}/samples",
                files={"file": (f.name, f.read(), f.content_type)},
                timeout=60,
            )
            up.raise_for_status()
            meta = up.json()
            sha  = meta["sha256"]

            # análisis obligatorios
            data = {
                "sha256":      sha,
                "filename":    meta["filename"],
                "size":        meta["size"],
                "hash":        _get(f"/samples/{sha}/hash"),
                # 'file' devuelve "ruta: descripción" — nos quedamos solo con la descripción
                "file":        _get(f"/samples/{sha}/file")["file"].split(": ", 1)[-1],
                "entropy":     _get(f"/samples/{sha}/entropy")["entropy"],
                "exiftool":    _get(f"/samples/{sha}/exiftool"),
                "readelf":     _get(f"/samples/{sha}/readelf")["readelf"],
                "ran_strings": run_strings,
                "ran_ssdeep":  run_ssdeep,
            }

            # análisis opcionales
            if run_strings:
                data["strings"] = _get(f"/samples/{sha}/strings", min_len=min_len)["strings"]
            if run_ssdeep:
                data["ssdeep"] = _get(f"/samples/{sha}/ssdeep")["ssdeep"]

            return render(request, "analyzer/results.html", {"data": data})
        except Exception as e:
            return render(request, "analyzer/index.html", {"error": str(e)})
    return render(request, "analyzer/index.html")


def history(request):
    try:
        samples = _get("/samples")
    except Exception as e:
        return render(request, "analyzer/history.html", {"error": str(e), "samples": []})
    return render(request, "analyzer/history.html", {"samples": samples})
