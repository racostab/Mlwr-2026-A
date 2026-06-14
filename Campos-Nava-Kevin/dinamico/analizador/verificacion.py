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
  4. Internet INALCANZABLE — LA PRUEBA DE FUEGO: desde dentro de la VM se tantea
     salida por TCP (/dev/tcp), UDP (/dev/udp), ICMP (ping) y DNS a varias IPs y
     puertos; TODO debe fallar. Como señal estructural extra, se revisa que NO
     haya ruta por defecto (sin gateway ⇒ nada enruta afuera por ningún protocolo).
  5. Sin carpetas compartidas — la VM no tiene ningún mapeo de carpeta (máquina ni
     global): no hay puente de disco guest→host por el que el malware escriba en el
     host sin tocar la red.

Uso directo (diagnóstico, enciende la VM aislada si hace falta):
    python3 dinamico/analizador/verificacion.py [nombre_vm]
"""
import sys

import red
import firewall
from compartido.configuracion import kali as cfg
from compartido.sftp.conexion import conectar_con_reintentos

# IPs públicas para la prueba de fuga. Se prueban con los builtins /dev/tcp y
# /dev/udp de bash (no dependen de que `curl`/`nc` estén en la VM), más ICMP y DNS.
IPS_PUBLICAS = ("1.1.1.1", "8.8.8.8")
# Puertos representativos a tantear por cada protocolo (servicios comunes de C2).
PUERTOS_TCP = (53, 80, 443)        # DNS, HTTP, HTTPS
PUERTOS_UDP = (53, 123, 1194)      # DNS, NTP, OpenVPN (UDP también se usa para C2)


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


def _sale(client, cmd: str) -> bool:
    """True si `cmd` tuvo éxito en la VM (salió un paquete / hubo respuesta)."""
    return _run(client, f"{cmd} && echo SALE || echo NO").endswith("SALE")


def internet_alcanzable(client) -> tuple[bool, str]:
    """Prueba REAL y EXTENSA desde la VM si hay salida (TCP+UDP+ICMP+DNS).

    Devuelve (alcanzable, detalle). CUALQUIER éxito por cualquier protocolo cuenta
    como fuga y corta al primer indicio. En la jaula (sin ruta por defecto) todo
    falla al instante con ENETUNREACH, así que el barrido es barato pese a probar
    varios puertos/protocolos.

    Notas por protocolo:
      - TCP (`/dev/tcp`): el connect() falla si no hay ruta → no salió nada.
      - UDP (`/dev/udp`): el sendto() también falla con ENETUNREACH sin ruta; con
        ruta tiene éxito aunque no haya respuesta (el datagrama YA salió = fuga).
      - ICMP (`ping`): best-effort; sólo cuenta si LLEGA respuesta.
      - DNS (`getent`): resolución contra el resolutor configurado.
    """
    # 1. TCP a varios puertos comunes.
    for ip in IPS_PUBLICAS:
        for puerto in PUERTOS_TCP:
            if _sale(client, f"timeout 3 bash -c 'echo > /dev/tcp/{ip}/{puerto}' 2>/dev/null"):
                return True, f"TCP salió a {ip}:{puerto} — hay salida a internet"
    # 2. UDP: enviar un datagrama; si la pila lo acepta es que hay ruta de salida.
    for ip in IPS_PUBLICAS:
        for puerto in PUERTOS_UDP:
            if _sale(client, f"timeout 3 bash -c 'echo x > /dev/udp/{ip}/{puerto}' 2>/dev/null"):
                return True, f"UDP salió a {ip}:{puerto} — hay salida a internet (datagrama enviado)"
    # 3. ICMP: sólo cuenta si hay RESPUESTA (ping puede faltar o requerir privilegios).
    for ip in IPS_PUBLICAS:
        if _sale(client, f"timeout 3 ping -c1 -W2 {ip} >/dev/null 2>&1"):
            return True, f"ICMP: {ip} respondió al ping — hay salida a internet"
    # 4. DNS: resolución contra el resolutor de la VM.
    if _sale(client, "timeout 3 getent hosts google.com >/dev/null 2>&1"):
        return True, "la VM resolvió DNS público — hay salida a internet"
    return False, ("sin salida por NINGÚN protocolo: TCP(53/80/443) + UDP(53/123/1194) "
                   "+ ICMP + DNS a 1.1.1.1/8.8.8.8 todos bloqueados")


def ruta_por_defecto(client) -> str:
    """Ruta(s) por defecto en la VM. Vacío = no hay gateway de salida (no puede
    enrutar a redes externas por ningún protocolo). Señal estructural extra."""
    return _run(client, "ip route show default 2>/dev/null")


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

    # Una carpeta compartida es un puente de disco guest→host que el malware puede
    # usar para escribir en el host SIN red, saltándose todo el aislamiento de red.
    # Debe haber CERO (red.preparar_aislada ya las quita; aquí se re-confirma).
    compartidas = red.carpetas_compartidas(nombre)
    ok_sf = not compartidas
    chequeos.append(("Sin carpetas compartidas (puente de disco al host)", ok_sf,
                     "ninguna" if ok_sf else "EXPUESTAS: " + ", ".join(compartidas)))
    if not ok_sf:
        criticos.append(
            "hay carpeta(s) compartida(s) montables en la VM (" + ", ".join(compartidas)
            + "): el malware podría escribir en el disco del host sin red. Quítalas "
            "('VBoxManage sharedfolder remove " + nombre + " --name <n> [--global]') "
            "y re-toma el snapshot limpio")

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
        chequeos.append(("Internet INALCANZABLE (TCP+UDP+ICMP+DNS)", not alcanza, detalle))
        if alcanza:
            criticos.append(detalle)
        # Señal estructural extra (informativa): sin gateway de salida, nada puede
        # enrutar afuera por ningún protocolo. No es crítica por sí sola (la prueba
        # de fuego de arriba ya es la que decide), pero documenta el porqué.
        ruta = ruta_por_defecto(client)
        chequeos.append(("Sin ruta por defecto (gateway de salida)", not ruta,
                         "ninguna" if not ruta else f"EXISTE: {ruta}"))
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
