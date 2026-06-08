#!/usr/bin/env python3
"""
Flujo:
    1. Aísla la red de la VM (host-only, sin NAT) y la arranca headless.
    2. Espera a que responda el SSH.
    3. Aplica el firewall del host (firewall local).
    4. VERIFICA(gate duro): si no está demostrablemente aislada, ABORTA sin detonar.
    5. Sube la muestra por SFTP, la ejecuta acotada por tiempo bajo strace
       (syscalls) y vuelca su memoria.
    6. Trae el volcado, el strace.log y los logs al host (./dynamic_output/<timestamp>/).
"""
import os
import sys

import aislamiento
import ejecucion
from compartido.configuracion import kali as cfg


def analizar(local_path: str, segundos: int = 20) -> None:
    if not os.path.isfile(local_path):
        raise FileNotFoundError(f"Muestra no encontrada: {local_path}")

    c = cfg()
    name = c["vm_name"]
    user = c["user"]

    ip = aislamiento.preparar_aislada(name)
    client = ejecucion.esperar_ssh(ip, 22, user, c["key_path"])
    try:
        # 3. Firewall del host ANTES de ejecutar nada (cinturón y tirantes).
        aislamiento.aplicar_firewall()

        # 4. Gate de seguridad: PROBAR que el nat esta cerrado
        aislamiento.verificar(name, client=client)

        # 5-6. Ejecutar la muestra, volcar memoria y traer resultados.
        destino = ejecucion.correr_y_volcar(client, local_path, user, segundos)

        print(f"\n Análisis dinámico completo. Resultados en: {destino}/")
        print("    (la VM sigue encendida; apágala con "
              "'bash dinamico/scripts/control_maquina_virtual.sh stop kali' si quieres)")
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
