
from vboxapi import VirtualBoxManager
import sys


mgr = VirtualBoxManager(None, None)
vbox = mgr.getVirtualBox()


action = sys.argv[1]
vm_name = sys.argv[2]

# Buscar la máquina virtual por nombre. Si no existe, `findMachine` lanzará
# una excepción (no capturada aquí, para mantener la lógica original).
machine = vbox.findMachine(vm_name)

# Crear un objeto de sesión. Este objeto se usa para bloquear la máquina y
# acceder a su consola cuando se requiera (stop/pause/resume).
session = mgr.getSessionObject(vbox)

if action == "start":
    # Arranca la VM en modo "headless" (sin GUI). Se obtiene un objeto de
    # progreso y se espera a que la operación termine.
    progress = machine.launchVMProcess(session, "headless", "")
    progress.waitForCompletion(-1)  # -1 = esperar indefinidamente

elif action == "stop":
    # Bloquea la máquina en modo compartido (tipo 1) para obtener la consola
    # y solicitar el apagado (powerDown).
    machine.lockMachine(session, 1)  # tipo de bloqueo: 1 = Shared, 2 = Write
    console = session.console
    console.powerDown()

elif action == "pause":
    # Bloqueo y pausa de la VM; útil para detener temporalmente su ejecución.
    machine.lockMachine(session, 1)
    console = session.console
    console.pause()

elif action == "resume":
    # Bloqueo y reanudación de la ejecución de la VM.
    machine.lockMachine(session, 1)
    console = session.console
    console.resume()