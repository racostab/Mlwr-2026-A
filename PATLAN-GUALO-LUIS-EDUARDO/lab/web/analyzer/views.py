from django.shortcuts import render


def spa(request):
    """Sirve el shell del SPA. Toda la lógica vive en el cliente (Vue),
    que consume directamente la API del engine."""
    return render(request, "analyzer/index.html")
