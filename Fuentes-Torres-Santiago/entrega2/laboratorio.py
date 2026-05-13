#!/usr/bin/env python3
# ============================================================
#  laboratorio.py  —  Laboratorio de Análisis Estático
#  Integra todos los módulos de análisis en un solo programa
#
#  Uso:
#    python laboratorio.py analizar [archivo]
#    python laboratorio.py comparar [archivo1] [archivo2]
#    python laboratorio.py dir      [carpeta]
#    python laboratorio.py ejemplo
#
#  Módulos integrados:
#    hashes.py       — MD5, SHA1, SHA256
#    entropia.py     — Entropía de Shannon
#    tipo_archivo.py — Tipo por magic bytes
#    cadenas.py      — Strings del archivo
#    ssdeep.py       — Similitud entre archivos
# ============================================================

import sys
import os

# Agregar carpeta padre al path para importar módulos
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modulos.hashes       import calcular_hashes,   mostrar_hashes
from modulos.entropia     import calcular_entropia,  mostrar_entropia
from modulos.tipo_archivo import detectar_tipo,      mostrar_tipo
from modulos.cadenas      import extraer_cadenas,    mostrar_cadenas
from modulos.ssdeep       import calcular_ssdeep,    mostrar_ssdeep, comparar

# ── Separador visual ─────────────────────────────────────────
SEP = "=" * 60


def analizar_archivo(ruta, mostrar_cadenas_flag=True, max_cadenas=20):
    """
    Ejecuta análisis completo de un archivo.
    Llama a todos los módulos en orden.
    """
    if not os.path.isfile(ruta):
        print(f"[ERROR] Archivo no encontrado: {ruta}")
        sys.exit(1)

    print(SEP)
    print(f"  LABORATORIO DE ANÁLISIS ESTÁTICO")
    print(f"  Archivo: {ruta}")
    print(SEP)

    # ── 1. Tipo de archivo ───────────────────────────────────
    print("\n[1/5] TIPO DE ARCHIVO")
    print("-" * 40)
    tipo = detectar_tipo(ruta)
    mostrar_tipo(tipo)

    # ── 2. Hashes ────────────────────────────────────────────
    print("[2/5] FIRMAS (HASHES)")
    print("-" * 40)
    hashes = calcular_hashes(ruta)
    mostrar_hashes(hashes)

    # ── 3. Entropía ──────────────────────────────────────────
    print("[3/5] ENTROPÍA DE SHANNON")
    print("-" * 40)
    entropia = calcular_entropia(ruta)
    mostrar_entropia(entropia)

    # Advertencia: si entropía alta, cadenas no son útiles
    if entropia and entropia["sospechoso"]:
        print("  ⚠ Entropia alta detectada.")
        if entropia["entropia"] >= 7.0:
            print("  ⚠ Archivo posiblemente cifrado — cadenas no seran utiles.\n")
            mostrar_cadenas_flag = False

    # ── 4. Cadenas ───────────────────────────────────────────
    print("[4/5] CADENAS (STRINGS)")
    print("-" * 40)
    if mostrar_cadenas_flag:
        cadenas = extraer_cadenas(ruta)
        mostrar_cadenas(cadenas, max_mostrar=max_cadenas)
    else:
        print("  Omitido por entropia alta.\n")

    # ── 5. Fuzzy Hash ────────────────────────────────────────
    print("[5/5] FUZZY HASH (SSDEEP)")
    print("-" * 40)
    ssdeep = calcular_ssdeep(ruta)
    mostrar_ssdeep(ssdeep)

    # ── Resumen final ────────────────────────────────────────
    print(SEP)
    print("  RESUMEN")
    print(SEP)
    if tipo:
        print(f"  Tipo       : {tipo['tipo']} — {tipo['descripcion']}")
    if hashes:
        print(f"  MD5        : {hashes['md5']}")
        print(f"  SHA1       : {hashes['sha1']}")
        print(f"  SHA256     : {hashes['sha256']}")
    if entropia:
        estado = "⚠ SOSPECHOSO" if entropia["sospechoso"] else "OK"
        print(f"  Entropia   : {entropia['entropia']} / 8.0 — {estado}")
    if cadenas and mostrar_cadenas_flag:
        print(f"  Cadenas    : {cadenas['total']} encontradas")
    if ssdeep:
        print(f"  Fuzzy hash : {ssdeep['hash']}")
    print(SEP)
    print()


def comparar_archivos(ruta1, ruta2):
    """Compara dos archivos con fuzzy hashing."""
    print(SEP)
    print("  COMPARACIÓN DE ARCHIVOS")
    print(SEP)

    for ruta in [ruta1, ruta2]:
        if not os.path.isfile(ruta):
            print(f"[ERROR] Archivo no encontrado: {ruta}")
            sys.exit(1)

    r1 = calcular_ssdeep(ruta1)
    r2 = calcular_ssdeep(ruta2)

    mostrar_ssdeep(r1)
    mostrar_ssdeep(r2)

    similitud = comparar(r1, r2)
    print(f"  Similitud  : {similitud}%")

    if similitud >= 80:
        print("  ⚠ ALERTA: Archivos muy similares — posible variante de malware.")
    elif similitud >= 50:
        print("  ~ Archivos parcialmente similares.")
    else:
        print("  OK Archivos diferentes.")
    print(SEP)
    print()


def analizar_directorio(carpeta, umbral=50):
    """Analiza todos los archivos de una carpeta."""
    if not os.path.isdir(carpeta):
        print(f"[ERROR] No es una carpeta: {carpeta}")
        sys.exit(1)

    archivos = [
        os.path.join(carpeta, f)
        for f in os.listdir(carpeta)
        if os.path.isfile(os.path.join(carpeta, f))
    ]

    print(SEP)
    print(f"  ANÁLISIS DE DIRECTORIO: {carpeta}")
    print(f"  Archivos encontrados: {len(archivos)}")
    print(SEP)

    resultados = {}
    for archivo in archivos:
        print(f"\n>>> {os.path.basename(archivo)}")
        print("-" * 40)
        tipo     = detectar_tipo(archivo)
        hashes   = calcular_hashes(archivo)
        entropia = calcular_entropia(archivo)
        ssdeep   = calcular_ssdeep(archivo)

        if tipo:
            print(f"  Tipo     : {tipo['tipo']} — {tipo['descripcion']}")
        if hashes:
            print(f"  MD5      : {hashes['md5']}")
        if entropia:
            estado = "⚠ SOSPECHOSO" if entropia["sospechoso"] else "OK"
            print(f"  Entropia : {entropia['entropia']} / 8.0 — {estado}")
        if ssdeep:
            resultados[archivo] = ssdeep

    # Comparar similitudes
    print(f"\n{SEP}")
    print(f"  COMPARACIÓN DE SIMILITUD (umbral: {umbral}%)")
    print(SEP)

    archivos_lista = list(resultados.keys())
    encontrados    = False

    for i in range(len(archivos_lista)):
        for j in range(i + 1, len(archivos_lista)):
            a1  = archivos_lista[i]
            a2  = archivos_lista[j]
            sim = comparar(resultados[a1], resultados[a2])
            if sim >= umbral:
                encontrados = True
                n1 = os.path.basename(a1)
                n2 = os.path.basename(a2)
                alerta = "⚠ MUY SIMILARES" if sim >= 80 else "~ PARCIALMENTE SIMILARES"
                print(f"\n  {n1}  vs  {n2}")
                print(f"  Similitud: {sim}%  —  {alerta}")

    if not encontrados:
        print(f"\n  Sin archivos similares por encima del {umbral}%.")
    print(SEP)


def mostrar_ejemplos():
    """Ejecuta ejemplos de demostración."""
    print("[INFO] Ejecutando ejemplo de analisis...\n")
    # Analizar el propio laboratorio.py como demo
    analizar_archivo(os.path.abspath(__file__), max_cadenas=10)


def mostrar_uso():
    print(f"""
{SEP}
  LABORATORIO DE ANÁLISIS ESTÁTICO
{SEP}

 Uso: python laboratorio.py [accion] [argumentos]

 Acciones:
   analizar [archivo]              Análisis completo de un archivo
   comparar [archivo1] [archivo2]  Compara similitud entre 2 archivos
   dir      [carpeta]              Analiza todos los archivos de carpeta
   dir      [carpeta] [umbral]     Con umbral de similitud (0-100)
   ejemplo                         Ejecuta demo con laboratorio.py

 Ejemplos:
   python laboratorio.py analizar malware.exe
   python laboratorio.py comparar original.exe variante.exe
   python laboratorio.py dir C:\\muestras
   python laboratorio.py dir C:\\muestras 80
   python laboratorio.py ejemplo
{SEP}
""")


# ── Main ─────────────────────────────────────────────────────
if __name__ == "__main__":
    args = sys.argv[1:]

    if not args:
        mostrar_uso()
        sys.exit(0)

    accion = args[0].lower()

    if accion == "analizar":
        if len(args) < 2:
            print("[ERROR] Especifica un archivo.")
            mostrar_uso()
            sys.exit(1)
        analizar_archivo(args[1])

    elif accion == "comparar":
        if len(args) < 3:
            print("[ERROR] Especifica dos archivos.")
            mostrar_uso()
            sys.exit(1)
        comparar_archivos(args[1], args[2])

    elif accion == "dir":
        if len(args) < 2:
            print("[ERROR] Especifica una carpeta.")
            mostrar_uso()
            sys.exit(1)
        umbral = int(args[2]) if len(args) > 2 else 50
        analizar_directorio(args[1], umbral)

    elif accion == "ejemplo":
        mostrar_ejemplos()

    else:
        print(f"[ERROR] Accion desconocida: {accion}")
        mostrar_uso()
        sys.exit(1)