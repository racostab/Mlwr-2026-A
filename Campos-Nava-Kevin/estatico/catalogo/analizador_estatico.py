"""
El motor importa SIEMPRE desde aquí:
    from catalogo.analizador_estatico import CATALOGO, catalogo_publico, comandos_extra, yara_reglas
"""
from catalogo.analizadores import yara_reglas
from catalogo.comando_guiado import binarios_permitidos, comando_personalizado, comandos_extra
from catalogo.registro import CATALOGO, POR_DEFECTO, Analizador, catalogo_publico

__all__ = [
    "CATALOGO",
    "POR_DEFECTO",
    "Analizador",
    "catalogo_publico",
    "comandos_extra",
    "comando_personalizado",
    "binarios_permitidos",
    "yara_reglas",
]
