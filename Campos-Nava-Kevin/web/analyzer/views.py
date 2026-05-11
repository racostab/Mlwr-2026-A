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
        min_len = request.POST.get("min_len", "4")
        try:
            up = requests.post(
                f"{ENGINE_URL}/samples",
                files={"file": (f.name, f.read(), f.content_type)},
                timeout=60,
            )
            up.raise_for_status()
            meta = up.json()
            sha  = meta["sha256"]
            data = {
                "sha256":   sha,
                "filename": meta["filename"],
                "size":     meta["size"],
                "hash":     _get(f"/samples/{sha}/hash"),
                "file":     _get(f"/samples/{sha}/file")["file"],
                "strings":  _get(f"/samples/{sha}/strings", min_len=min_len)["strings"],
                "entropy":  _get(f"/samples/{sha}/entropy")["entropy"],
                "ssdeep":   _get(f"/samples/{sha}/ssdeep")["ssdeep"],
                "exiftool": _get(f"/samples/{sha}/exiftool"),
                "readelf":  _get(f"/samples/{sha}/readelf")["readelf"],
            }
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
