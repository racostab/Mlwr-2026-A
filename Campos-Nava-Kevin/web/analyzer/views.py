import os
import requests
from django.shortcuts import render

ENGINE_URL = os.environ.get("ENGINE_URL", "http://localhost:8001")


def index(request):
    if request.method == "POST" and request.FILES.get("file"):
        f = request.FILES["file"]
        min_len = request.POST.get("min_len", "4")
        try:
            resp = requests.post(
                f"{ENGINE_URL}/static/analyze",
                files={"file": (f.name, f.read(), f.content_type)},
                params={"min_len": min_len},
                timeout=30,
            )
            resp.raise_for_status()
            return render(request, "analyzer/results.html", {"data": resp.json()})
        except Exception as e:
            return render(request, "analyzer/index.html", {"error": str(e)})
    return render(request, "analyzer/index.html")
