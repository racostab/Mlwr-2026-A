import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from core.config import vbox as cfg

try:
    from vboxapi import VirtualBoxManager
except ImportError:
    VirtualBoxManager = None


def run(action: str, vm_name: str = None):
    if VirtualBoxManager is None:
        print("[!] vboxapi no disponible. Usa cli.sh para controlar la VM con VBoxManage.")
        return

    if vm_name is None:
        vm_name = cfg()["vm_name"]

    mgr     = VirtualBoxManager(None, None)
    vbox    = mgr.getVirtualBox()
    machine = vbox.findMachine(vm_name)
    session = mgr.getSessionObject(vbox)

    if action == "start":
        progress = machine.launchVMProcess(session, "headless", "")
        progress.waitForCompletion(-1)
        print(f"[+] VM '{vm_name}' iniciada")

    elif action == "stop":
        machine.lockMachine(session, 1)
        session.console.powerDown()
        print(f"[+] VM '{vm_name}' apagada")

    elif action == "pause":
        machine.lockMachine(session, 1)
        session.console.pause()
        print(f"[+] VM '{vm_name}' pausada")

    elif action == "resume":
        machine.lockMachine(session, 1)
        session.console.resume()
        print(f"[+] VM '{vm_name}' reanudada")

    else:
        print(f"[!] Acción desconocida: {action}")
        print("    Acciones válidas: start | stop | pause | resume")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python3 api.py <start|stop|pause|resume> [vm_name]")
        sys.exit(1)
    run(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
