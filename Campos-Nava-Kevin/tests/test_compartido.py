"""Paquete compartido: la conexión SSH/SFTP y la config."""
import pytest

from compartido import configuracion
from compartido.sftp import conexion


def test_funciones_de_transmision_existen():
    for fn in ("conectar", "subir", "asegurar_remoto"):
        assert callable(getattr(conexion, fn))


def test_ejecutar_fue_eliminado():
    # Era código muerto (nadie lo llamaba); se quitó en la depuración.
    assert not hasattr(conexion, "ejecutar")


def test_conectar_falla_si_no_hay_llave():
    with pytest.raises(FileNotFoundError):
        conexion.conectar("host", 22, "user", "/ruta/que/no/existe/id_rsa")


def test_config_expone_kali():
    assert callable(configuracion.kali)
