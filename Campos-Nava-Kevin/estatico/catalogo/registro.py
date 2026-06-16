"""Registro de comandos: la ÚNICA fuente de verdad del análisis estático.

`CATALOGO` une cada analizador con su id estable, su etiqueta legible y sus flags.
La API (`/tools`, `/samples/{sha}/run/{tool}`) y la web leen de aquí, así que
**añadir un análisis nuevo es una sola línea** en `CATALOGO` (más su función en
`analizadores.py`).
"""
from dataclasses import dataclass
from typing import Callable

from catalogo.analizadores import (
    entropia_archivo,
    exiftool_archivo,
    file_archivo,
    hash_archivo,
    radare_archivo,
    radare_volcado,
    readelf_archivo,
    ssdeep_archivo,
    strings_archivo,
    xxd_archivo,
    yara_archivo,
)
from catalogo.comando_guiado import comando_personalizado


@dataclass(frozen=True)
class Analizador:
    id: str                   # identificador estable usado en API/CLI/web
    etiqueta: str             # texto legible para la interfaz
    fn: Callable[..., object]
    cacheable: bool = True    # los paramétricos (strings, xxd) no se cachean
    oculto: bool = False      # no aparece en /tools (p. ej. el comando guiado)


CATALOGO: dict[str, Analizador] = {
    a.id: a for a in [
        Analizador("hash",     "Hashes (MD5/SHA1/SHA256)",        hash_archivo),
        Analizador("file",     "Tipo de archivo (file)",          file_archivo),
        Analizador("entropy",  "Entropía (bits/byte)",            entropia_archivo),
        Analizador("ssdeep",   "Fuzzy hash (ssdeep)",             ssdeep_archivo),
        Analizador("exiftool", "Metadatos (ExifTool)",            exiftool_archivo),
        Analizador("readelf",  "Cabeceras ELF (readelf)",         readelf_archivo),
        Analizador("yara",     "Reglas YARA",                     yara_archivo),
        Analizador("radare",   "Desensamblado (radare2)",         radare_archivo),
        # Variante para VOLCADOS de memoria (core ELF): la usa el post-análisis
        # dinámico. Oculta en /tools (no aplica a un binario en disco normal).
        Analizador("radare_dump", "Volcado: radare2 (disasm @ PC)", radare_volcado,
                   oculto=True),
        Analizador("strings",  "Cadenas legibles (strings)",      strings_archivo, cacheable=False),
        Analizador("xxd",      "Volcado hexadecimal (xxd)",       xxd_archivo,     cacheable=False),
        # Comando guiado: no se cachea (depende del cmd) ni se lista en /tools.
        Analizador("custom",   "Comando guiado",                  comando_personalizado,
                   cacheable=False, oculto=True),
    ]
}

# Conjunto que corre la web/CLI cuando el usuario elige el modo "por defecto".
# Es la fuente de verdad: la web ya no lo duplica, lo lee de /tools (por_defecto).
POR_DEFECTO = ["hash", "file", "entropy", "exiftool", "readelf", "yara"]


def catalogo_publico() -> list[dict]:
    """Lista [{id, etiqueta, cacheable, por_defecto}] de los comandos visibles."""
    return [
        {
            "id":         a.id,
            "etiqueta":   a.etiqueta,
            "cacheable":  a.cacheable,
            "por_defecto": a.id in POR_DEFECTO,
        }
        for a in CATALOGO.values() if not a.oculto
    ]
