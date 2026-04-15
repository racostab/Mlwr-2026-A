#!/usr/bin/env python3
# ============================================================
#  
#  Equivalente Python de docker_login.bat y docker_cmd.bat
#
# 
#    python programa_docker.py login
#    python programa_docker.py login [contenedor]
#    python programa_docker.py cmd whoami
#    python programa_docker.py cmd [contenedor] uname -a
#    python programa_docker.py list
#    python programa_docker.py create
#    python programa_docker.py start  [contenedor]
#    python programa_docker.py stop   [contenedor]
#    python programa_docker.py logs   [contenedor]
#    python programa_docker.py ejemplo
# ============================================================

import subprocess
import sys

# ── Configuración ────────────────────────────────────────────
DEFAULT_NAME  = "ciber-docker" 
DEFAULT_IMAGE = "debian:bookworm-slim"
# ─────────────────────────────────────────────────────────────


def verificar_docker():
    """Verifica que Docker esté instalado y corriendo."""
    resultado = subprocess.run(
        ["docker", "--version"],
        capture_output=True,
        text=True,
        check=False
    )
    if resultado.returncode != 0:
        print("[ERROR] Docker no esta instalado.")
        print()
        print("  Para instalarlo:")
        print("  1. Ve a: https://www.docker.com/products/docker-desktop")
        print("  2. Descarga Docker Desktop para Windows")
        print("  3. Ejecuta el instalador como Administrador")
        print("  4. Reinicia Windows cuando lo pida")
        print("  5. Abre Docker Desktop y espera que inicie")
        print("  6. Vuelve a ejecutar este programa")
        sys.exit(1)

    # Verificar si el daemon esta corriendo
    resultado = subprocess.run(
        ["docker", "info"],
        capture_output=True,
        text=True,
        check=False
    )
    if resultado.returncode != 0:
        print("[ERROR] Docker esta instalado pero no esta corriendo.")
        print()
        print("  Para iniciarlo:")
        print("  1. Busca 'Docker Desktop' en el menu de inicio")
        print("  2. Abrelo y espera a que el icono de la ballena aparezca en la barra de tareas")
        print("  3. Vuelve a ejecutar este programa")
        sys.exit(1)

    print("[OK] Docker disponible y corriendo.")


def contenedor_existe(nombre):
    """Verifica si un contenedor existe."""
    resultado = subprocess.run(
        ["docker", "inspect", nombre],
        capture_output=True,
        text=True,
        check=False
    )
    return resultado.returncode == 0


def contenedor_corriendo(nombre):
    """Verifica si un contenedor está corriendo."""
    resultado = subprocess.run(
        ["docker", "inspect", "--format={{.State.Running}}", nombre],
        capture_output=True,
        text=True,
        check=False
    )
    return resultado.stdout.strip() == "true"


def iniciar_si_detenido(nombre):
    """Inicia el contenedor si está detenido."""
    if not contenedor_corriendo(nombre):
        print(f"[DOCKER] Contenedor detenido. Iniciando {nombre}...")
        subprocess.run(["docker", "start", nombre],
                       capture_output=True, check=False)


def listar_contenedores():
    """Lista todos los contenedores (corriendo y detenidos)."""
    print("[DOCKER] Lista de contenedores:\n")
    subprocess.run(["docker", "ps", "-a"], check=False)


def crear_contenedor(nombre=DEFAULT_NAME, imagen=DEFAULT_IMAGE):
    """Crea un contenedor nuevo sin iniciarlo."""
    if contenedor_existe(nombre):
        print(f"[WARN] El contenedor '{nombre}' ya existe.")
        return
    print(f"[DOCKER] Creando contenedor '{nombre}' con imagen '{imagen}'...")
    resultado = subprocess.run(
        ["docker", "create", "-it", "--name", nombre, imagen, "/bin/bash"],
        capture_output=True,
        text=True,
        check=False
    )
    if resultado.returncode == 0:
        print(f"[OK] Contenedor '{nombre}' creado.")
    else:
        print(f"[ERROR] No se pudo crear el contenedor.")
        print(resultado.stderr)


def iniciar_contenedor(nombre=DEFAULT_NAME):
    """Inicia un contenedor detenido."""
    if not contenedor_existe(nombre):
        print(f"[ERROR] El contenedor '{nombre}' no existe.")
        print(f"[INFO]  Usa: python programa_docker.py create")
        return
    if contenedor_corriendo(nombre):
        print(f"[WARN] El contenedor '{nombre}' ya esta corriendo.")
        return
    resultado = subprocess.run(
        ["docker", "start", nombre],
        capture_output=True,
        text=True,
        check=False
    )
    if resultado.returncode == 0:
        print(f"[OK] Contenedor '{nombre}' iniciado.")
    else:
        print(f"[ERROR] No se pudo iniciar el contenedor.")


def detener_contenedor(nombre=DEFAULT_NAME):
    """Detiene un contenedor corriendo."""
    if not contenedor_existe(nombre):
        print(f"[ERROR] El contenedor '{nombre}' no existe.")
        return
    if not contenedor_corriendo(nombre):
        print(f"[WARN] El contenedor '{nombre}' ya esta detenido.")
        return
    resultado = subprocess.run(
        ["docker", "stop", nombre],
        capture_output=True,
        text=True,
        check=False
    )
    if resultado.returncode == 0:
        print(f"[OK] Contenedor '{nombre}' detenido.")
    else:
        print(f"[ERROR] No se pudo detener el contenedor.")


def docker_login(nombre=DEFAULT_NAME):
    """Abre sesión interactiva dentro del contenedor."""
    print(f"[DOCKER] Abriendo sesion en {nombre}...")
    print("[DOCKER] Escribe 'exit' para cerrar la sesion.\n")

    if contenedor_existe(nombre):
        iniciar_si_detenido(nombre)
        subprocess.run(["docker", "exec", "-it", nombre, "/bin/bash"], check=False)
    else:
        print(f"[DOCKER] Contenedor no encontrado. Creando uno nuevo...")
        subprocess.run(
            ["docker", "run", "-it", "--name", nombre, DEFAULT_IMAGE, "/bin/bash"],
            check=False
        )
    print("\n[OK] Sesion cerrada.")


def docker_cmd(comando, nombre=DEFAULT_NAME):
    """Ejecuta un comando dentro del contenedor y captura la salida."""
    if not comando:
        print("[ERROR] Debes especificar un comando.")
        return

    print(f"[DOCKER] Ejecutando en {nombre}: {comando}\n")

    if contenedor_existe(nombre):
        iniciar_si_detenido(nombre)
        resultado = subprocess.run(
            ["docker", "exec", nombre, "/bin/bash", "-c", comando],
            capture_output=True,
            text=True,
            check=False
        )
    else:
        resultado = subprocess.run(
            ["docker", "run", "--rm", DEFAULT_IMAGE, "/bin/bash", "-c", comando],
            capture_output=True,
            text=True,
            check=False
        )

    if resultado.stdout:
        print(resultado.stdout)
    if resultado.stderr:
        print(f"[STDERR] {resultado.stderr}")

    if resultado.returncode == 0:
        print("[OK] Comando ejecutado correctamente.")
    else:
        print(f"[ERROR] El comando termino con codigo {resultado.returncode}.")


def logs_contenedor(nombre=DEFAULT_NAME):
    """Muestra los logs del contenedor."""
    if not contenedor_existe(nombre):
        print(f"[ERROR] El contenedor '{nombre}' no existe.")
        return
    print(f"[DOCKER] Logs de {nombre}:\n")
    subprocess.run(["docker", "logs", nombre], check=False)


def mostrar_ejemplos():
    """Ejecuta ejemplos de demostración."""
    print("[INFO] Ejecutando ejemplos de demostracion...\n")

    print("── Ejemplo 1: listar contenedores ─────────────")
    listar_contenedores()

    print("\n── Ejemplo 2: whoami ──────────────────────────")
    docker_cmd("whoami")

    print("\n── Ejemplo 3: uname -a ────────────────────────")
    docker_cmd("uname -a")

    print("\n── Ejemplo 4: df -h ───────────────────────────")
    docker_cmd("df -h")


def mostrar_uso():
    print("""
 Uso: python programa_docker.py [accion] [argumentos]

 Acciones:
   list                          Lista todos los contenedores
   create                        Crea el contenedor ciber-docker
   create [nombre]               Crea contenedor con nombre especifico
   start                         Inicia ciber-docker
   start  [nombre]               Inicia contenedor especifico
   stop                          Detiene ciber-docker
   stop   [nombre]               Detiene contenedor especifico
   login                         Sesion interactiva en ciber-docker
   login  [nombre]               Sesion en contenedor especifico
   cmd    [comando]              Ejecuta comando en ciber-docker
   cmd    [nombre] [comando]     Ejecuta comando en contenedor especifico
   logs                          Muestra logs de ciber-docker
   logs   [nombre]               Muestra logs de contenedor especifico
   ejemplo                       Ejecuta demos automaticas

 Ejemplos:
   python programa_docker.py list
   python programa_docker.py create
   python programa_docker.py login
   python programa_docker.py cmd whoami
   python programa_docker.py cmd ciber-docker uname -a
   python programa_docker.py logs
""")


# ── Main ─────────────────────────────────────────────────────
if __name__ == "__main__":
    args = sys.argv[1:]

    if not args:
        mostrar_uso()
        sys.exit(0)

    verificar_docker()

    accion = args[0].lower()

    if accion == "list":
        listar_contenedores()

    elif accion == "create":
        nombre = args[1] if len(args) > 1 else DEFAULT_NAME
        crear_contenedor(nombre)

    elif accion == "start":
        nombre = args[1] if len(args) > 1 else DEFAULT_NAME
        iniciar_contenedor(nombre)

    elif accion == "stop":
        nombre = args[1] if len(args) > 1 else DEFAULT_NAME
        detener_contenedor(nombre)

    elif accion == "login":
        nombre = args[1] if len(args) > 1 else DEFAULT_NAME
        docker_login(nombre)

    elif accion == "cmd":
        if len(args) < 2:
            print("[ERROR] Especifica un comando.")
            mostrar_uso()
            sys.exit(1)
        if len(args) > 2 and not args[1].startswith("-"):
            nombre = args[1]
            comando = " ".join(args[2:])
        else:
            nombre = DEFAULT_NAME
            comando = " ".join(args[1:])
        docker_cmd(comando, nombre)

    elif accion == "logs":
        nombre = args[1] if len(args) > 1 else DEFAULT_NAME
        logs_contenedor(nombre)

    elif accion == "ejemplo":
        mostrar_ejemplos()

    else:
        print(f"[ERROR] Accion desconocida: {accion}")
        mostrar_uso()
        sys.exit(1)