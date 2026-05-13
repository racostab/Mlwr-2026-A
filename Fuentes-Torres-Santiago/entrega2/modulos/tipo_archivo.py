#!/usr/bin/env python3
# ============================================================
#  modulos/tipo_archivo.py  —  Módulo de Tipo de Archivo
#  Detecta el tipo real de un archivo por sus magic bytes
#  Sin dependencias externas — solo Python base
#
#  Uso standalone:
#    python tipo_archivo.py archivo.exe
#    python tipo_archivo.py imagen.jpg
#
#  Uso como módulo:
#    from modulos.tipo_archivo import detectar_tipo
# ============================================================

import sys
import os

# ── Tabla de Magic Bytes ─────────────────────────────────────
# (offset, bytes, tipo, descripcion)
MAGIC_BYTES = [
    # Ejecutables
    (0, b"\x4D\x5A",                     "EXE/DLL",  "Ejecutable Windows (PE)"),
    (0, b"\x7FELF",                       "ELF",      "Ejecutable Linux/Unix"),
    # Archivos comprimidos
    (0, b"\x50\x4B\x03\x04",             "ZIP",      "Archivo ZIP"),
    (0, b"\x52\x61\x72\x21\x1A\x07",     "RAR",      "Archivo RAR"),
    (0, b"\x1F\x8B",                      "GZIP",     "Archivo GZIP"),
    (0, b"\x42\x5A\x68",                  "BZIP2",    "Archivo BZIP2"),
    (0, b"\xFD\x37\x7A\x58\x5A\x00",     "XZ",       "Archivo XZ"),
    (0, b"\x37\x7A\xBC\xAF\x27\x1C",     "7ZIP",     "Archivo 7-Zip"),
    # Documentos
    (0, b"\x25\x50\x44\x46",             "PDF",      "Documento PDF"),
    (0, b"\xD0\xCF\x11\xE0",             "DOC/XLS",  "Documento Office antiguo"),
    (0, b"\x50\x4B\x03\x04",             "DOCX/XLSX","Documento Office moderno"),
    # Imagenes
    (0, b"\xFF\xD8\xFF",                  "JPEG",     "Imagen JPEG"),
    (0, b"\x89\x50\x4E\x47\x0D\x0A",     "PNG",      "Imagen PNG"),
    (0, b"\x47\x49\x46\x38",             "GIF",      "Imagen GIF"),
    (0, b"\x42\x4D",                      "BMP",      "Imagen BMP"),
    (0, b"\x49\x49\x2A\x00",             "TIFF",     "Imagen TIFF (little-endian)"),
    (0, b"\x4D\x4D\x00\x2A",             "TIFF",     "Imagen TIFF (big-endian)"),
    # Audio/Video
    (0, b"\x49\x44\x33",                  "MP3",      "Audio MP3"),
    (0, b"\x52\x49\x46\x46",             "WAV/AVI",  "Audio WAV o Video AVI"),
    (4, b"\x66\x74\x79\x70",             "MP4",      "Video MP4"),
    # Scripts y texto
    (0, b"\x23\x21",                      "SCRIPT",   "Script (shebang #!)"),
    (0, b"\xEF\xBB\xBF",                  "UTF-8",    "Texto UTF-8 con BOM"),
    (0, b"\xFF\xFE",                      "UTF-16LE", "Texto UTF-16 Little Endian"),
    (0, b"\xFE\xFF",                      "UTF-16BE", "Texto UTF-16 Big Endian"),
    # Otros
    (0, b"\x4D\x5A\x90\x00",             "EXE",      "Ejecutable Windows moderno"),
    (0, b"\xCA\xFE\xBA\xBE",             "CLASS",    "Bytecode Java"),
    (0, b"\x75\x73\x74\x61\x72",         "TAR",      "Archivo TAR"),
]
# ─────────────────────────────────────────────────────────────


def detectar_tipo(ruta_archivo):
    """
    Detecta el tipo de archivo por magic bytes.
    Retorna un diccionario con el resultado o None si hay error.
    """
    if not os.path.isfile(ruta_archivo):
        print(f"[ERROR] Archivo no encontrado: {ruta_archivo}", file=sys.stderr)
        return None

    try:
        with open(ruta_archivo, "rb") as f:
            cabecera = f.read(32)
    except PermissionError:
        print(f"[ERROR] Sin permisos para leer: {ruta_archivo}", file=sys.stderr)
        return None
    except OSError as e:
        print(f"[ERROR] No se pudo leer el archivo: {e}", file=sys.stderr)
        return None

    # Buscar coincidencia en tabla de magic bytes
    tipo      = "DESCONOCIDO"
    descripcion = "Tipo no identificado"

    for offset, magic, t, desc in MAGIC_BYTES:
        segmento = cabecera[offset:offset + len(magic)]
        if segmento == magic:
            tipo      = t
            descripcion = desc
            break

    # Si no hay magic bytes conocidos, intentar detectar texto plano
    if tipo == "DESCONOCIDO":
        try:
            with open(ruta_archivo, "r", encoding="utf-8") as f:
                f.read(512)
            tipo        = "TEXT"
            descripcion = "Archivo de texto plano (UTF-8)"
        except UnicodeDecodeError:
            tipo        = "BINARIO"
            descripcion = "Archivo binario desconocido"

    extension = os.path.splitext(ruta_archivo)[1].lower() or "(sin extension)"

    return {
        "archivo":    ruta_archivo,
        "extension":  extension,
        "tipo":       tipo,
        "descripcion": descripcion,
    }


def mostrar_tipo(resultado):
    """Muestra el tipo de archivo en formato legible."""
    if not resultado:
        return
    print(f"\n  Archivo    : {resultado['archivo']}")
    print(f"  Extension  : {resultado['extension']}")
    print(f"  Tipo       : {resultado['tipo']}")
    print(f"  Descripcion: {resultado['descripcion']}")
    print()


def mostrar_uso():
    print("""
 Uso: python tipo_archivo.py [archivo]

 Ejemplos:
   python tipo_archivo.py archivo.txt
   python tipo_archivo.py malware.exe
   python tipo_archivo.py imagen.jpg
""")


# ── Main (uso standalone) ─────────────────────────────────────
if __name__ == "__main__":
    if len(sys.argv) < 2:
        mostrar_uso()
        sys.exit(1)

    ruta = sys.argv[1]
    print(f"[TIPO] Detectando tipo de: {ruta}")

    resultado = detectar_tipo(ruta)

    if resultado:
        mostrar_tipo(resultado)
        print("[OK] Tipo detectado correctamente.")
        sys.exit(0)
    else:
        print("[ERROR] No se pudo detectar el tipo.")
        sys.exit(1)