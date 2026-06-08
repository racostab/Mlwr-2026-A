"""Verificación de aislamiento (pre-vuelo) ANTES de detonar una muestra.

Confirma —con pruebas, no de palabra— que la VM está realmente enjaulada antes
de ejecutar nada dentro de ella. Es el "cinturón de seguridad" que corre el
runner (`analizador_dinamico.py`) justo antes de subir/ejecutar el malware; si
cualquier comprobación falla, lanza `NoAislada` y el análisis se ABORTA: mejor no
detonar que hacerlo con una fuga abierta.

Comprobaciones (TODAS son críticas: si una falla, se aborta sin detonar):
  1. NAT desconectado   — el adaptador 1 está en `null`/`none`: la VM no tiene
     tarjeta con salida a internet. Es la "regla DOWN" que aplica `red.aislar()`.
  2. Red host-only      — existe `vboxnet0` (el único canal host↔VM).
  3. Firewall del host  — iptables descarta lo que la VM INICIE hacia el host.
     Se lee con `sudo -n` (vía `firewall.esta_aplicado`); si no se puede CONFIRMAR
     el DROP (firewall ausente o sudo no disponible), se aborta.
  4. Internet INALCANZABLE — LA PRUEBA DE FUEGO: desde dentro de la VM se intenta
     abrir TCP a IPs públicas y resolver DNS; TODO debe fallar.

Uso directo (diagnóstico, enciende la VM aislada si hace falta):
    python3 dinamico/analizador/verificacion.py [nombre_vm]
"""
import sys

import red
import firewall
from compartido.configuracion import kali as cfg
from compartido.sftp.conexion import conectar_con_reintentos

# IPs públicas para la prueba de fuga (puerto 53: casi siempre alcanzable si hay
# salida). Se prueban por TCP con el builtin /dev/tcp de bash: no depende de que
# `ping` o `curl` estén instalados en la VM.
IPS_PUBLICAS = ("1.1.1.1", "8.8.8.8")


class NoAislada(RuntimeError):
    """La VM no quedó demostrablemente aislada: NO se debe detonar la muestra."""


def _run(client, cmd: str) -> str:
    """Ejecuta `cmd` por SSH en la VM y devuelve stdout (sin saltos sobrantes)."""
    _, stdout, _ = client.exec_command(cmd)
    stdout.channel.recv_exit_status()
    return stdout.read().decode(errors="replace").strip()


def nat_desconectado(nombre: str) -> tuple[bool, str]:
    """True si el adaptador 1 NO está en modo `nat` (es `null`/`none` ⇒ sin internet)."""
    info = red.vboxmanage("showvminfo", nombre, "--machinereadable")
    for linea in info.splitlines():
        if linea.startswith("nic1="):
            modo = linea.split("=", 1)[1].strip().strip('"')
            return modo in ("null", "none"), modo
    return False, "?"


def hostonly_presente() -> bool:
    """True si existe la interfaz host-only `vboxnet0` (el único canal host↔VM)."""
    return red.IFACE_HOSTONLY in red.vboxmanage("list", "hostonlyifs")


def internet_alcanzable(client) -> tuple[bool, str]:
    """Prueba REAL desde dentro de la VM si hay salida a internet.

    Devuelve (alcanzable, detalle). Usa TCP a IPs públicas (no depende de DNS ni
    de binarios) y, como señal extra, una resolución DNS.
    """
    for ip in IPS_PUBLICAS:
        cmd = (
            f"timeout 3 bash -c 'echo > /dev/tcp/{ip}/53' 2>/dev/null "
            f"&& echo SALE || echo NO"
        )
        if _run(client, cmd) == "SALE":
            return True, f"la VM ALCANZÓ {ip}:53 — hay salida a internet"
    dns = _run(
        client,
        "timeout 3 getent hosts google.com >/dev/null 2>&1 && echo SALE || echo NO",
    )
    if dns == "SALE":
        return True, "la VM resolvió DNS público — hay salida a internet"
    return False, "TCP a 1.1.1.1/8.8.8.8:53 y DNS bloqueados (sin salida)"


def _icono(estado) -> str:
    return {True: "✓", False: "✗", None: "?"}[estado]


def verificar(nombre: str, client=None, ip: str | None = None) -> bool:
    """Verifica el aislamiento de `nombre`. Lanza `NoAislada` si hay fallo crítico.

    Si no se pasa `client`, abre su propia conexión SSH a la VM (usando `config`)
    para la prueba de internet y la cierra al terminar. En el flujo del análisis
    se reutiliza el `client` ya abierto.
    """
    chequeos: list[tuple[str, object, str]] = []
    criticos: list[str] = []

    ok_nat, modo = nat_desconectado(nombre)
    chequeos.append(("NAT desconectado (sin tarjeta a internet)", ok_nat, f'nic1="{modo}"'))
    if not ok_nat:
        criticos.append(f'el adaptador NAT sigue ACTIVO (nic1="{modo}"): la VM tendría internet')

    ok_ho = hostonly_presente()
    chequeos.append(("Red host-only vboxnet0 presente", ok_ho, red.IFACE_HOSTONLY))
    if not ok_ho:
        criticos.append("no existe la interfaz host-only 'vboxnet0' (canal host↔VM)")

    fw = firewall.esta_aplicado()
    detalle_fw = {
        True: "iptables descarta lo que la VM inicie hacia el host",
        False: "NO hay DROP: el host queda EXPUESTO a la VM",
        None: "no se pudo CONFIRMAR sin 'sudo -n' (aplica el firewall / corre con sudo)",
    }[fw]
    chequeos.append(("Firewall del host (VM→host)", fw, detalle_fw))
    if fw is not True:  # gate CRÍTICO: sin firewall confirmado, no se detona
        criticos.append(
            "firewall del host no confirmado: "
            + ("NO hay DROP, el host queda EXPUESTO" if fw is False
               else "no verificable sin 'sudo -n'; aplica 'aislar_host.sh' y reintenta")
        )

    propio = False
    if client is None:
        c = cfg()
        ip = ip or red.GUEST_IP
        client = conectar_con_reintentos(ip, 22, c["user"], c["key_path"], label="Kali")
        propio = True
    try:
        alcanza, detalle = internet_alcanzable(client)
        chequeos.append(("Internet INALCANZABLE desde la VM", not alcanza, detalle))
        if alcanza:
            criticos.append(detalle)
    finally:
        if propio:
            client.close()

    print("[*] Verificación de aislamiento:")
    for etiqueta, estado, detalle in chequeos:
        print(f"    [{_icono(estado)}] {etiqueta} — {detalle}")

    if criticos:
        raise NoAislada(
            "Aislamiento NO confirmado; se aborta para no detonar con fuga:\n  - "
            + "\n  - ".join(criticos)
        )
    print("[✓] Jaula cerrada: es seguro detonar la muestra.")
    return True


if __name__ == "__main__":
    vm = sys.argv[1] if len(sys.argv) > 1 else "kali-malware-lab"
    # Asegura que la VM esté corriendo y aislada antes de verificar.
    direccion = red.preparar_aislada(vm)
    try:
        verificar(vm, ip=direccion)
    except NoAislada as e:
        print(f"[!] {e}")
        sys.exit(1)
    except Exception as e:  # noqa: BLE001
        print(f"[!] {e}")
        sys.exit(1)
