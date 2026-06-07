"""Analizadores estáticos: una función por herramienta.

Cada analizador tiene la firma `fn(client, ruta, **opts)` y se ejecuta **por SSH
dentro del sandbox** (`client.exec_command`), nunca en el host. 
`ruta` es la ubicación de la muestra dentro del sandbox (la subió antes el motor por SFTP).
`**opts` recoge parámetros opcionales (p. ej. `min_len`, `length`) para que todas las funciones tengan la misma firma aunque no los usen.
"""


def hash_archivo(client, ruta: str, **_) -> dict:
    """MD5, SHA1 y SHA256 de la muestra."""
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


def file_archivo(client, ruta: str, **_) -> str:
    """Tipo de archivo según `file` (magia de cabeceras)."""
    _, stdout, stderr = client.exec_command(f"file {ruta}")
    stdout.channel.recv_exit_status()
    return stdout.read().decode().strip() or stderr.read().decode().strip()


def strings_archivo(client, ruta: str, *, min_len: int = 4, **_) -> str:
    """Cadenas legibles de longitud ≥ `min_len`."""
    _, stdout, _ = client.exec_command(f"strings -n {min_len} {ruta}")
    stdout.channel.recv_exit_status()
    return stdout.read().decode(errors="replace").strip()


def entropia_archivo(client, ruta: str, **_) -> str:
    """Entropía de Shannon en bits/byte (pista de empaquetado/cifrado)."""
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


def exiftool_archivo(client, ruta: str, **_) -> dict:
    """Metadatos del archivo (ExifTool), como pares clave/valor."""
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


def readelf_archivo(client, ruta: str, **_) -> str:
    """Cabeceras y secciones ELF (`readelf -a`)."""
    _, stdout, _ = client.exec_command(f"readelf -a {ruta} 2>&1")
    stdout.channel.recv_exit_status()
    return stdout.read().decode(errors="replace").strip()


def xxd_archivo(client, ruta: str, *, length: int = 4096, **_) -> str:
    """Volcado hexadecimal de los primeros `length` bytes (0 = archivo completo)."""
    # Acotamos para no devolver megabytes de volcado en binarios grandes.
    flag = f"-l {length} " if length and length > 0 else ""
    _, stdout, stderr = client.exec_command(f"xxd {flag}{ruta}")
    stdout.channel.recv_exit_status()
    out = stdout.read().decode(errors="replace").rstrip("\n")
    err = stderr.read().decode().strip()
    return out or (f"ERROR: {err}" if err else "")


def radare_archivo(client, ruta: str, **_) -> str:
    """Desensamblado con radare2: lista de funciones + entry0 y main."""
    # Modo batch (-q), sin color; -A ejecuta el análisis (aaa) al cargar.
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


def ssdeep_archivo(client, ruta: str, **_) -> str:
    """Fuzzy hash (ssdeep) para comparar similitud entre muestras."""
    _, stdout, stderr = client.exec_command(f"ssdeep {ruta}")
    stdout.channel.recv_exit_status()
    out = stdout.read().decode().strip()
    err = stderr.read().decode().strip()
    if err:
        return f"ERROR: {err}"
    # ssdeep imprime una cabecera + la línea del hash; devolvemos solo el hash.
    lines = [l for l in out.splitlines() if l and not l.startswith("ssdeep")]
    return lines[0] if lines else out


def yara_archivo(client, ruta: str, **_) -> dict:
    """Escanea la muestra con todas las reglas YARA de `/rules/*.yar`."""
    # yara imprime "NombreRegla <ruta>" por cada coincidencia.
    cmd = f'for r in /rules/*.yar; do [ -e "$r" ] && yara "$r" {ruta} 2>/dev/null; done'
    _, stdout, stderr = client.exec_command(cmd)
    stdout.channel.recv_exit_status()
    out = stdout.read().decode(errors="replace").strip()
    err = stderr.read().decode().strip()
    if err and not out:
        return {"matches": [], "error": err}
    matches = sorted({line.split()[0] for line in out.splitlines() if line.strip()})
    return {"matches": matches}


def yara_reglas(client) -> list[dict]:
    """Introspección: lista las reglas YARA cargadas en el sandbox (`/rules/*.yar`).

    No analiza ninguna muestra; sirve para la página "Reglas" de la web. Devuelve
    una entrada por archivo con sus reglas (nombre + descripción) y su contenido.
    """
    cmd = 'for f in /rules/*.yar; do [ -e "$f" ] && { echo "@@FILE@@$f"; cat "$f"; }; done'
    _, stdout, _ = client.exec_command(cmd)
    stdout.channel.recv_exit_status()
    texto = stdout.read().decode(errors="replace")

    archivos = []
    actual = None
    for line in texto.splitlines():
        if line.startswith("@@FILE@@"):
            actual = {"archivo": line[len("@@FILE@@"):], "reglas": [], "contenido": ""}
            archivos.append(actual)
            continue
        if actual is None:
            continue
        actual["contenido"] += line + "\n"
        stripped = line.strip()
        if stripped.startswith("rule "):
            nombre = stripped[5:].split("{")[0].split(":")[0].strip()
            actual["reglas"].append({"nombre": nombre, "descripcion": ""})
        elif "descripcion" in stripped and "=" in stripped and actual["reglas"]:
            desc = stripped.split("=", 1)[1].strip().strip('"').strip()
            actual["reglas"][-1]["descripcion"] = desc
    return archivos
