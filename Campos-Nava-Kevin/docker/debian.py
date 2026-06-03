
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from core.ssh import conectar as _conectar, ejecutar


def conectar():
    from core.config import docker as cfg
    c = cfg()
    return _conectar(c["host"], c["port"], c["user"], c["key_path"], label="Debian")


def hash_archivo(client, ruta: str) -> dict:
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


def file_archivo(client, ruta: str) -> str:
    _, stdout, stderr = client.exec_command(f"file {ruta}")
    stdout.channel.recv_exit_status()
    return stdout.read().decode().strip() or stderr.read().decode().strip()


def strings_archivo(client, ruta: str, min_len: int = 4) -> str:
    _, stdout, _ = client.exec_command(f"strings -n {min_len} {ruta}")
    stdout.channel.recv_exit_status()
    return stdout.read().decode(errors="replace").strip()


def entropia_archivo(client, ruta: str) -> str:
    script = (
        "import math,collections;"
        f"d=open('{ruta}','rb').read();"
        "freq=collections.Counter(d);"
        "e=-sum((c/len(d))*math.log2(c/len(d)) for c in freq.values());"
        "print(f'{e:.4f}')"
    )
    _, stdout, stderr = client.exec_command(f"python3 -c \"{script}\"")
    stdout.channel.recv_exit_status()
    return stdout.read().decode().strip() or stderr.read().decode().strip()


def exiftool_archivo(client, ruta: str) -> dict:
    _, stdout, stderr = client.exec_command(f"exiftool {ruta}")
    stdout.channel.recv_exit_status()
    out = stdout.read().decode().strip()
    err = stderr.read().decode().strip()
    if err and not out:
        return {"ERROR": err}
    result = {}
    for line in out.splitlines():
        if ":" in line:
            key, _, val = line.partition(":")
            result[key.strip()] = val.strip()
    return result


def readelf_archivo(client, ruta: str) -> str:
    _, stdout, _ = client.exec_command(f"readelf -a {ruta} 2>&1")
    stdout.channel.recv_exit_status()
    return stdout.read().decode(errors="replace").strip()


def xxd_archivo(client, ruta: str, length: int = 4096) -> str:
    # Vista hex + caracteres. Acotamos los primeros `length` bytes para no
    # devolver megabytes de volcado en binarios grandes (0 = archivo completo).
    flag = f"-l {length} " if length and length > 0 else ""
    _, stdout, stderr = client.exec_command(f"xxd {flag}{ruta}")
    stdout.channel.recv_exit_status()
    out = stdout.read().decode(errors="replace").rstrip("\n")
    err = stderr.read().decode().strip()
    return out or (f"ERROR: {err}" if err else "")


def radare_archivo(client, ruta: str) -> str:
    # Desensamblado con radare2 en modo batch (-q) y sin color (scr.color=0).
    # -A ejecuta el análisis (aaa) al cargar; listamos funciones (afl) y
    # desensamblamos el punto de entrada y main si existe.
    cmd = (
        "r2 -A -q -e scr.color=0 "
        '-c "afl ; '
        'echo === entry0 === ; pdf @ entry0 ; '
        'echo === main === ; pdf @ main" '
        f"{ruta} 2>&1"
    )
    _, stdout, _ = client.exec_command(cmd)
    stdout.channel.recv_exit_status()
    return stdout.read().decode(errors="replace").strip()


def ssdeep_archivo(client, ruta: str) -> str:
    _, stdout, stderr = client.exec_command(f"ssdeep {ruta}")
    stdout.channel.recv_exit_status()
    out = stdout.read().decode().strip()
    err = stderr.read().decode().strip()
    if err:
        return f"ERROR: {err}"
    # ssdeep prints header + hash line; return just the hash line
    lines = [l for l in out.splitlines() if l and not l.startswith("ssdeep")]
    return lines[0] if lines else out


if __name__ == "__main__":
    client = conectar()
    if len(sys.argv) == 3 and sys.argv[1] == "hash":
        ruta   = sys.argv[2]
        hashes = hash_archivo(client, ruta)
        print(f"\nArchivo: {ruta}")
        for alg, val in hashes.items():
            print(f"  {alg:<8} {val}")
    else:
        ejecutar(client, "whoami")
        ejecutar(client, "uname -a")
        ejecutar(client, "cat /etc/os-release")
    client.close()
