"""Motor (FastAPI): que la app monte y que los endpoints sin BD respondan.

No tocan `db` ni `sandbox`: probamos las rutas que solo leen el catálogo. El flujo
real contra el sandbox se prueba en `test_integracion.py` (con el lab levantado).
"""


def test_la_app_monta_sus_rutas():
    import principal
    paths = {r.path for r in principal.app.routes if hasattr(r, "path")}
    for esperado in ("/health", "/tools", "/commands", "/samples", "/status"):
        assert esperado in paths


def test_health():
    import rutas
    assert rutas.health() == {"status": "ok"}


def test_tools_sale_del_catalogo():
    import rutas
    tools = rutas.tools()
    ids = [t["id"] for t in tools]
    assert "hash" in ids
    assert "custom" not in ids
    assert all("por_defecto" in t for t in tools)


def test_commands_devuelve_lista():
    import rutas
    salida = rutas.commands()
    assert "comandos" in salida
    assert isinstance(salida["comandos"], list)
