"""Primeros pasos del grafo MITRE ATT&CK desde el análisis dinámico.

Toma las DOS fuentes que ya produce una detonación y las traduce a técnicas
ATT&CK (con su táctica), generando un grafo táctica→técnica que la web podrá
dibujar:

  1. `strace.log`        → syscalls observadas (connect, execve, ptrace, memfd…).
  2. `post_analisis.json`→ coincidencias YARA del volcado (packing, anti-VM…).

Diseño a propósito SIMPLE y ampliable: una tabla de reglas `(detector → técnica)`.
Cada detector es un conjunto de subcadenas; si aparecen en las líneas de strace
(o como nombre de regla YARA), se anota la técnica con su evidencia. Añadir una
técnica = una entrada más en `REGLAS_SYSCALL` o `REGLAS_YARA`. No pretende ser un
clasificador exhaustivo: es el andamiaje del grafo, afinable con muestras reales.

    python3 dinamico/analizador/mitre.py dynamic_output/<ts>/   # imprime el JSON
"""
import json
import re
from pathlib import Path

# (id_tecnica, nombre, tactica, [subcadenas que la disparan en strace])
# Las subcadenas se buscan en crudo sobre cada línea de strace.log.
REGLAS_SYSCALL = [
    ("T1059.004", "Intérprete de shell (sh/bash)", "execution",
        ['execve("/bin/sh', 'execve("/bin/bash', '"/bin/sh"', '"sh", "-c"']),
    ("T1071",     "Protocolo de capa de aplicación (C2)", "command-and-control",
        ['connect(', 'sendto(', 'sendmsg(']),
    ("T1095",     "Protocolo no-aplicativo (sockets crudos)", "command-and-control",
        ['socket(AF_INET, SOCK_RAW', 'SOCK_RAW']),
    ("T1071.004", "DNS", "command-and-control",
        ['/etc/resolv.conf', 'getaddrinfo', 'res_query', ':53']),
    ("T1620",     "Carga reflexiva de código (fileless)", "defense-evasion",
        ['memfd_create', 'execveat']),
    ("T1055",     "Inyección / código RWX en memoria", "defense-evasion",
        ['mprotect(', 'PROT_EXEC|PROT_WRITE', 'PROT_WRITE|PROT_EXEC']),
    ("T1622",     "Evasión de depurador (ptrace)", "defense-evasion",
        ['ptrace(', 'PTRACE_TRACEME']),
    ("T1497",     "Evasión de VM/sandbox", "defense-evasion",
        ['/sys/class/dmi', 'product_name', 'cpuinfo', 'hypervisor']),
    ("T1070.004", "Borrado de indicadores (auto-borrado/logs)", "defense-evasion",
        ['unlink("', 'unlinkat(', '/var/log/wtmp', '/var/log/secure']),
    ("T1053.003", "Tarea programada (cron)", "persistence",
        ['/etc/cron', '/var/spool/cron', 'crontab']),
    ("T1543.002", "Servicio systemd (persistencia)", "persistence",
        ['/etc/systemd/system', '.service', '/etc/init.d']),
    ("T1547.001", "Arranque (rc.local / profile / bashrc)", "persistence",
        ['/etc/rc.local', '/etc/profile', '.bashrc', '/etc/init']),
    ("T1082",     "Descubrimiento de información del sistema", "discovery",
        ['uname(', 'gethostname', '/proc/cpuinfo', '/proc/version']),
    ("T1083",     "Descubrimiento de archivos y directorios", "discovery",
        ['getdents', 'openat(AT_FDCWD, "/etc', 'readdir']),
    ("T1057",     "Descubrimiento de procesos", "discovery",
        ['/proc/', 'readlink("/proc']),
    ("T1105",     "Transferencia de herramientas (descarga/escritura)", "command-and-control",
        ['wget', 'curl', 'tftp', '/dev/shm/', 'O_CREAT|O_WRONLY']),
    ("T1027.002", "Empaquetado de software (desempaque en runtime)", "defense-evasion",
        ['mmap(NULL', 'PROT_EXEC', 'memfd_create']),
    ("T1489",     "Detención de servicios / kill", "impact",
        ['kill(', 'tgkill(', 'killall']),
]

# Coincidencias YARA (por subcadena en el NOMBRE de la regla) → técnica.
REGLAS_YARA = [
    ("T1027.002", "Empaquetado de software", "defense-evasion",
        ['UPX', 'Packer', 'MPRESS', 'Ezuri', 'gzexe', 'Empaquetado', 'Entropia']),
    ("T1027",     "Ofuscación de archivos/información", "defense-evasion",
        ['Ofuscacion', 'XOR', 'Base64', 'Cifrado', 'Garble']),
    ("T1497",     "Evasión de VM/sandbox", "defense-evasion",
        ['AntiVM', 'AntiAnalisis']),
    ("T1622",     "Evasión de depurador", "defense-evasion",
        ['AntiDebug', 'Ptrace']),
    ("T1070",     "Borrado de indicadores", "defense-evasion",
        ['Borra_Huellas', 'Evasion']),
    ("T1129",     "Módulos compartidos (carga dinámica)", "execution",
        ['Carga_Dinamica', 'dlopen']),
    ("T1071",     "Protocolo de capa de aplicación (C2)", "command-and-control",
        ['C2', 'network', 'Network']),
]

TACTICAS = {
    "execution": "Ejecución",
    "persistence": "Persistencia",
    "defense-evasion": "Evasión de defensas",
    "discovery": "Descubrimiento",
    "command-and-control": "Comando y control",
    "impact": "Impacto",
}


def _evidencia_strace(texto: str, agujas: list[str], max_lineas: int = 3) -> list[str]:
    """Líneas de strace (recortadas) donde aparece alguna de las `agujas`."""
    out: list[str] = []
    for linea in texto.splitlines():
        if any(a in linea for a in agujas):
            out.append(linea.strip()[:200])
            if len(out) >= max_lineas:
                break
    return out


def _nombres_reglas_yara(post: dict) -> list[str]:
    """Extrae los nombres de reglas YARA de un `post_analisis.json` cargado."""
    nombres: list[str] = []
    for datos in post.values():
        if not isinstance(datos, dict):
            continue
        yara = datos.get("yara")
        if isinstance(yara, dict):                     # {"matches": [...]}
            nombres += [m if isinstance(m, str) else m.get("rule", "")
                        for m in yara.get("matches", [])]
        elif isinstance(yara, list):
            nombres += [str(x) for x in yara]
        elif isinstance(yara, str):
            nombres += re.findall(r"^(\w+)", yara, re.M)
    return [n for n in nombres if n]


def mapear(carpeta: str | Path) -> dict:
    """Construye el mapa ATT&CK de una carpeta `dynamic_output/<ts>/`.

    Devuelve `{tecnicas, grafo}` y escribe `mitre.json`. Combina la evidencia de
    `strace.log` y de `post_analisis.json` por técnica (sin duplicar).
    """
    carpeta = Path(carpeta)
    strace = carpeta / "strace.log"
    texto = strace.read_text(errors="replace") if strace.exists() else ""

    post_path = carpeta / "post_analisis.json"
    post = json.loads(post_path.read_text()) if post_path.exists() else {}
    nombres_yara = _nombres_reglas_yara(post)

    detectadas: dict[str, dict] = {}

    def _anota(tid, nombre, tactica, evidencia):
        t = detectadas.setdefault(tid, {
            "id": tid, "nombre": nombre, "tactica": tactica,
            "tactica_es": TACTICAS.get(tactica, tactica), "evidencia": [],
        })
        for e in evidencia:
            if e and e not in t["evidencia"]:
                t["evidencia"].append(e)

    if texto:
        for tid, nombre, tactica, agujas in REGLAS_SYSCALL:
            ev = _evidencia_strace(texto, agujas)
            if ev:
                _anota(tid, nombre, tactica, ev)

    for tid, nombre, tactica, agujas in REGLAS_YARA:
        hits = [n for n in nombres_yara if any(a.lower() in n.lower() for a in agujas)]
        if hits:
            _anota(tid, nombre, tactica, [f"YARA: {h}" for h in dict.fromkeys(hits)])

    tecnicas = sorted(detectadas.values(), key=lambda t: (t["tactica"], t["id"]))

    # Grafo simple táctica→técnica para que la web lo dibuje.
    tacticas_presentes = {t["tactica"] for t in tecnicas}
    nodos = ([{"id": f"tac:{k}", "tipo": "tactica", "label": TACTICAS.get(k, k)}
              for k in sorted(tacticas_presentes)]
             + [{"id": t["id"], "tipo": "tecnica", "label": f'{t["id"]} {t["nombre"]}'}
                for t in tecnicas])
    aristas = [{"de": f'tac:{t["tactica"]}', "a": t["id"]} for t in tecnicas]

    resultado = {
        "tecnicas": tecnicas,
        "n_tecnicas": len(tecnicas),
        "grafo": {"nodos": nodos, "aristas": aristas},
    }
    (carpeta / "mitre.json").write_text(
        json.dumps(resultado, indent=2, ensure_ascii=False), encoding="utf-8")
    return resultado


if __name__ == "__main__":
    import sys

    carpeta = sys.argv[1] if len(sys.argv) > 1 else "."
    print(json.dumps(mapear(carpeta), indent=2, ensure_ascii=False))
