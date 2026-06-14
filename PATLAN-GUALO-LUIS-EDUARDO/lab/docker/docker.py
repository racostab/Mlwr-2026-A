import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from core.config import docker as cfg


def _container() -> str:
    return cfg()["container"]


def run(cmd: list) -> str:
    result = subprocess.run(cmd, capture_output=True, text=True)
    salida = result.stdout.strip()
    error  = result.stderr.strip()
    if salida:
        print(f"[OUT] {salida}")
    if error:
        print(f"[ERR] {error}")
    return salida


def estado():
    c = _container()
    salida = run(["docker", "inspect", "-f", "{{.State.Status}}", c])
    print(f"[*] Estado: {salida}")
    return salidadef hash_archivo(client, ruta: str) -> dict:
    comandos = {
        "MD5":    f"md5sum {ruta}    | cut -d' ' -f1",
        "SHA1":   f"sha1sum {ruta}   | cut -d' ' -f1",
        "SHA256": f"sha256sum {ruta} | cut -d' ' -f1",
    }
    resultados = {}
    for nombre, cmd in comandos.items():
        _, stdout, stderr = client.exec_command(cmd)
        stdout.channel.recv_exit_status()
        valor = stdout.read().decode().strip()
        error = stderr.read().decode().strip()
        resultados[nombre] = f"ERROR: {error}" if error else valor
    return resultados


def iniciar():
    c = _container()
    print(f"[*] Iniciando {c}...")
    run(["docker", "start", c])


def detener():
    c = _container()
    print(f"[*] Deteniendo {c}...")
    run(["docker", "stop", c])


def reiniciar():
    c = _container()
    print(f"[*] Reiniciando {c}...")
    run(["docker", "restart", c])


def pausar():
    c = _container()
    print(f"[*] Pausando {c}...")
    run(["docker", "pause", c])


def reanudar():
    c = _container()
    print(f"[*] Reanudando {c}...")
    run(["docker", "unpause", c])


def logs():
    c = _container()
    print(f"[*] Logs de {c}:")
    run(["docker", "logs", "--tail", "20", c])


def ayuda():
    print("""
Uso: python3 docker.py <comando>

Comandos:
  start    Inicia el contenedor
  stop     Detiene el contenedor
  restart  Reinicia el contenedor
  pause    Pausa el contenedor
  resume   Reanuda el contenedor
  status   Muestra el estado actual
  logs     Muestra los últimos 20 logs
""")


if __name__ == "__main__":
    comandos = {
        "start":   iniciar,
        "stop":    detener,
        "restart": reiniciar,
        "pause":   pausar,
        "resume":  reanudar,
        "status":  estado,
        "logs":    logs,
    }
    if len(sys.argv) != 2 or sys.argv[1] not in comandos:
        ayuda()
    else:
        comandos[sys.argv[1]]()
