"""Firewall del HOST (firewall local): la capa que protege TU máquina de la VM.

Responsabilidad única: aplicar y comprobar el firewall **del host** que descarta
lo que la VM/malware intente INICIAR hacia el host (escaneo, brute-force SSH),
dejando pasar solo las RESPUESTAS a las sesiones que abre el host (SSH/SFTP del
análisis siguen funcionando).

Las reglas viven en `dinamico/reglas_firewall/aislar_host.sh`; este módulo solo
las invoca con sudo y comprueba que quedaron puestas. Las reglas de iptables NO
persisten al reiniciar el host, por eso se reaplican en cada análisis/setup.
"""
import subprocess
import sys
from pathlib import Path

import red

# reglas_firewall/aislar_host.sh está dos niveles arriba (en dinamico/).
_SCRIPT = Path(__file__).resolve().parent.parent / "reglas_firewall" / "aislar_host.sh"


def _log(*args) -> None:
    """Log a stderr: así quien captura el stdout (la fachada) solo ve la IP."""
    print(*args, file=sys.stderr)


def aplicar() -> None:
    """Aplica el firewall del host (pide sudo). Lanza si no se pudo asegurar.

    - Si existe `vboxnet0` pero el script falla → `RuntimeError` (mejor no
      ejecutar la muestra que hacerlo con el host expuesto).
    - Si NO existe `vboxnet0` → solo advierte (la VM podría no estar en host-only).
    """
    hostonly = subprocess.run(
        ["VBoxManage", "list", "hostonlyifs"], capture_output=True, text=True
    ).stdout
    if red.IFACE_HOSTONLY not in hostonly:
        _log(f"[!] ADVERTENCIA: no detecto la interfaz host-only '{red.IFACE_HOSTONLY}'.")
        _log("    La VM podría NO estar aislada (¿NAT con internet?). Revisa la red.")
        return
    if not _SCRIPT.exists():
        raise RuntimeError(f"No encuentro el script del firewall: {_SCRIPT}")
    _log("[*] Aplicando firewall del host (pedirá sudo)...")
    # El stdout del script va a stderr para no contaminar la IP que imprime la fachada.
    if subprocess.run(["bash", str(_SCRIPT)], stdout=sys.stderr).returncode != 0:
        raise RuntimeError(
            "No se pudo aplicar el firewall del host; abortando por seguridad. "
            f"Corre 'bash {_SCRIPT}' a mano y reintenta."
        )


def esta_aplicado(iface: str | None = None):
    """¿Hay un DROP en iptables para lo que la VM INICIE hacia el host?

    Devuelve True/False, o None si no se pudo leer sin contraseña (`sudo -n`):
    en ese caso no se puede afirmar nada (el verificador lo trata como crítico).
    """
    iface = iface or red.IFACE_HOSTONLY
    r = subprocess.run(
        ["sudo", "-n", "iptables", "-S", "INPUT"], capture_output=True, text=True
    )
    if r.returncode != 0:
        return None  # sin sudo no-interactivo: no verificable aquí
    return any(f"-i {iface}" in l and "-j DROP" in l for l in r.stdout.splitlines())


if __name__ == "__main__":
    aplicar()
