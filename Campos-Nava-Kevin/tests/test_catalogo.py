"""Catálogo estático: integridad del registro y del comando guiado."""
from catalogo.analizador_estatico import (
    CATALOGO,
    POR_DEFECTO,
    binarios_permitidos,
    catalogo_publico,
    comando_personalizado,
    comandos_extra,
)


class _FakeStd:
    """Imita stdout/stderr de paramiko para probar la ejecución sin SSH real."""
    def __init__(self, data: bytes = b""):
        self._data = data
        self.channel = self

    def recv_exit_status(self) -> int:
        return 0

    def read(self) -> bytes:
        return self._data


class _FakeClient:
    def __init__(self):
        self.ultimo = None

    def exec_command(self, full):
        self.ultimo = full
        return None, _FakeStd(b"salida de prueba"), _FakeStd(b"")


def test_catalogo_no_vacio():
    assert len(CATALOGO) >= 10


def test_la_clave_coincide_con_el_id():
    for clave, analizador in CATALOGO.items():
        assert clave == analizador.id


def test_por_defecto_es_subconjunto_del_catalogo():
    assert set(POR_DEFECTO).issubset(CATALOGO)


def test_publico_oculta_el_comando_guiado():
    ids = [t["id"] for t in catalogo_publico()]
    assert "hash" in ids
    assert "custom" not in ids  # oculto=True


def test_publico_marca_por_defecto():
    pub = {t["id"]: t for t in catalogo_publico()}
    for tid in POR_DEFECTO:
        assert pub[tid]["por_defecto"] is True
    assert pub["strings"]["por_defecto"] is False


def test_parametricos_no_se_cachean():
    assert CATALOGO["strings"].cacheable is False
    assert CATALOGO["xxd"].cacheable is False
    assert CATALOGO["hash"].cacheable is True


def test_comandos_json_carga_bien():
    cmds = comandos_extra()
    assert isinstance(cmds, list) and cmds
    assert {"id", "etiqueta", "cmd"} <= set(cmds[0])


def test_comando_guiado_rechaza_lo_peligroso():
    # No llega a usar el cliente SSH: valida y corta antes (client=None es seguro).
    assert comando_personalizado(None, "/x", cmd="ls; rm -rf /").startswith("[!]")
    assert comando_personalizado(None, "/x", cmd="cat > /etc/passwd").startswith("[!]")
    assert comando_personalizado(None, "/x", cmd="a | b").startswith("[!]")
    assert comando_personalizado(None, "/x", cmd="").startswith("[!]")


def test_whitelist_sale_de_comandos_json():
    permitidos = binarios_permitidos()
    for binario in ("objdump", "readelf", "nm", "strings", "xxd", "r2", "size", "ldd"):
        assert binario in permitidos
    assert "rm" not in permitidos
    assert "bash" not in permitidos


def test_comando_guiado_rechaza_binario_fuera_de_la_whitelist():
    # Sin metacaracteres, pero 'rm' no está en la whitelist → NO se ejecuta.
    # (client=None es seguro: se rechaza antes de tocarlo.)
    out = comando_personalizado(None, "/muestra", cmd="rm -rf /tmp")
    assert out.startswith("[!]")
    assert "no permitido" in out.lower()


def test_comando_guiado_ejecuta_binario_de_la_whitelist():
    # 'objdump' sí está → se ejecuta y se anexa la ruta de la muestra al final.
    fake = _FakeClient()
    out = comando_personalizado(fake, "/muestra", cmd="objdump -d")
    assert fake.ultimo == "objdump -d /muestra"
    assert "salida de prueba" in out
