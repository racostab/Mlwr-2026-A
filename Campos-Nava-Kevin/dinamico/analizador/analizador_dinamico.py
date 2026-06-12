#!/usr/bin/env python3
"""
Flujo:
    0. Restaura el snapshot LIMPIO de la VM (cada muestra arranca sin residuos de
       la anterior). La primera vez crea ese snapshot desde el estado actual.
    1. Aísla la red de la VM (host-only, sin NAT) y la arranca headless.
    2. Espera a que responda el SSH.
    3. Aplica el firewall del host (firewall local).
    4. VERIFICA(gate duro): si no está demostrablemente aislada, ABORTA sin detonar.
    5. Sube la muestra por SFTP, la ejecuta acotada por tiempo bajo strace
       (syscalls) y vuelca su memoria.
    6. Trae el volcado, el strace.log y los logs al host (./dynamic_output/<timestamp>/).
    7. Post-análisis ESTÁTICO del volcado con el motor (yara/strings); best-effort.
"""
import os
import sys
from pathlib import Path

import aislamiento
import ejecucion
import post_analisis
from compartido.configuracion import kali as cfg


def analizar(local_path: str, segundos: int = 20) -> Path:
    """Detona `local_path` en la VM aislada y devuelve la carpeta de resultados.

    El mismo flujo lo usan el CLI (`__main__`) y el servicio host
    (`servicio_dinamico.py`); por eso devuelve la ruta de `dynamic_output/<ts>/`
    en vez de solo imprimir.
    """
    if not os.path.isfile(local_path):
        raise FileNotFoundError(f"Muestra no encontrada: {local_path}")

    c = cfg()
    name = c["vm_name"]
    user = c["user"]

    # 0. Volver al estado base limpio: cada muestra se detona sobre una VM sin
    #    residuos de la anterior (persistencia, cron, procesos, archivos).
    aislamiento.restaurar_limpio(name)

    ip = aislamiento.preparar_aislada(name)
    client = ejecucion.esperar_ssh(ip, 22, user, c["key_path"])
    try:
        # 3. Firewall del host ANTES de ejecutar nada (cinturón y tirantes).
        aislamiento.aplicar_firewall()

        # 4. Gate de seguridad: PROBAR que el nat esta cerrado
        aislamiento.verificar(name, client=client)

        # 5-6. Ejecutar la muestra, volcar memoria y traer resultados.
        destino = ejecucion.correr_y_volcar(client, local_path, user, segundos)

        # 7. Post-análisis estático del volcado con el motor (yara/strings).
        #    Best-effort: si el motor no responde, deja la nota en post_analisis.json
        #    y NO rompe el análisis dinámico (el volcado ya está a salvo en disco).
        print("[*] Post-análisis del volcado con el motor (yara/strings)...")
        try:
            post_analisis.analizar_volcado(destino)
            print(f"[+] post_analisis.json escrito en {destino}/")
        except Exception as e:  # noqa: BLE001 — best-effort, nunca aborta por esto
            print(f"[!] Post-análisis omitido ({e}); el volcado sigue en {destino}/")

        print(f"\n Análisis dinámico completo. Resultados en: {destino}/")
        print("    (la VM sigue encendida; apágala con "
              "'bash dinamico/scripts/control_maquina_virtual.sh stop kali' si quieres)")
        return destino
    finally:
        client.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python3 dinamico/analizador/analizador_dinamico.py <ruta_local> [segundos]")
        sys.exit(1)
    ruta = sys.argv[1]
    secs = int(sys.argv[2]) if len(sys.argv) > 2 else 20
    try:
        analizar(ruta, secs)
    except Exception as e:  # noqa: BLE001
        print(f"[!] {e}")
        sys.exit(1)
