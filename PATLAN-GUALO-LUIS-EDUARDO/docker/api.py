import docker
import sys


if len(sys.argv) < 3:
    print("Uso: python api.py <start|stop|pause|unpause> <CONTAINER_NAME>")
    sys.exit(1)

client = docker.from_env()

action = sys.argv[1]
container_name = sys.argv[2]

# Buscar el contenedor por nombre
try:
    container = client.containers.get(container_name)
except docker.errors.NotFound:
    print(f"[ERROR] Contenedor '{container_name}' no encontrado")
    sys.exit(1)

if action == "start":
    # Inicia el contenedor
    if container.status == "running":
        print(f"[OK] Contenedor '{container_name}' ya está corriendo")
    else:
        container.start()
        print(f"[OK] Contenedor '{container_name}' iniciado")

elif action == "stop":
    # Detiene el contenedor
    if container.status == "exited":
        print(f"[OK] Contenedor '{container_name}' ya está detenido")
    else:
        container.stop()
        print(f"[OK] Contenedor '{container_name}' detenido")

elif action == "pause":
    # Pausa el contenedor
    if container.status == "paused":
        print(f"[OK] Contenedor '{container_name}' ya está pausado")
    else:
        container.pause()
        print(f"[OK] Contenedor '{container_name}' pausado")

elif action == "unpause":
    # Reanuda el contenedor
    if container.status == "running":
        print(f"[OK] Contenedor '{container_name}' ya está corriendo")
    else:
        container.unpause()
        print(f"[OK] Contenedor '{container_name}' reanudado")

else:
    print("Uso: python api.py <start|stop|pause|unpause> <CONTAINER_NAME>")
