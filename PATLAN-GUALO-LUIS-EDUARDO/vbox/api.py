from vboxapi import VirtualBoxManager
import sys


if len(sys.argv) < 3:
    print("Uso: python api.py <start|stop|suspend|resume> <VM_NAME>")
    sys.exit(1)

mgr = VirtualBoxManager(None, None)
vbox = mgr.getVirtualBox()

action = sys.argv[1]
vm_name = sys.argv[2]

# Buscar la máquina virtual por nombre
machine = vbox.findMachine(vm_name)

# Crear un objeto de sesión
session = mgr.getSessionObject(vbox)

if action == "start":
    # Arranca la VM en modo headless
    progress = machine.launchVMProcess(session, "headless", "")
    progress.waitForCompletion(-1)
    print(f"[OK] VM '{vm_name}' iniciada")

elif action == "stop":
    # Bloquea y apaga la VM
    machine.lockMachine(session, 1)
    console = session.console
    console.powerDown()
    print(f"[OK] VM '{vm_name}' apagada")

elif action == "suspend":
    # Bloquea y pausa la VM
    machine.lockMachine(session, 1)
    console = session.console
    console.pause()
    print(f"[OK] VM '{vm_name}' suspendida")

elif action == "resume":
    # Bloquea y reanuda la VM
    machine.lockMachine(session, 1)
    console = session.console
    console.resume()
    print(f"[OK] VM '{vm_name}' reanudada")

else:
    print("Uso: python api.py <start|stop|suspend|resume> <VM_NAME>")