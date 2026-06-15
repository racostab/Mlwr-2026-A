"""Post-análisis del volcado dinámico con el motor ESTÁTICO (reusa /rules).

¿Por qué? El volcado de memoria de la muestra suele traer en claro lo que el
binario empacado escondía en disco (IPs/dominios del C2, comandos, llaves). Esos
artefactos se cazan con YARA/strings — exactamente el análisis estático que ya
sabe hacer el motor. En vez de DUPLICAR las reglas YARA en `dinamico/`, mandamos
el volcado al motor (`POST /samples` → `run/yara`): así las reglas viven UNA sola
vez en `estatico/sandbox/reglas_yara/` (fuente de verdad) y se aplican igual al
disco y a la memoria.

Es best-effort: si el motor no está disponible, no rompe el análisis dinámico;
solo se omite el post-análisis y se deja constancia.
"""
import json
import os
from pathlib import Path

import requests

ENGINE_URL = os.environ.get("ENGINE_URL", "http://localhost:8001")
# Solo tiene sentido escanear los volcados de memoria (no el strace/stdout).
SUFIJOS_VOLCADO = (".core", ".dmp", ".elf")
# Prefijos de nombre que usan las herramientas de volcado: gcore → `core.<pid>`,
# procdump → `dump_<n>.<pid>` (sin extensión .core/.dmp, por eso no basta el sufijo).
PREFIJOS_VOLCADO = ("core", "dump")
# Herramientas estáticas que aportan sobre un volcado de memoria.
#   - yara/strings: cazan IOCs/firmas en la RAM desempacada.
#   - radare_dump:  desensambla el código en ejecución (disasm @ RIP) del core.
HERRAMIENTAS = ("yara", "strings", "radare_dump")


def _es_volcado(p: Path) -> bool:
    n = p.name.lower()
    # Por extensión (.core/.dmp/.elf) o por el nombre con que lo escriben gcore
    # (`core.*`) y procdump (`dump_*`). Los logs (strace/stdout/stderr.log) y el
    # propio post_analisis.json no casan ninguno de estos patrones.
    return (p.suffix.lower() in SUFIJOS_VOLCADO
            or n.startswith(PREFIJOS_VOLCADO)
            or "core" in n)


def analizar_volcado(destino: str | Path, engine_url: str | None = None) -> dict:
    """Pasa los volcados de `destino/` por el motor estático y guarda el resultado.

    Devuelve `{archivo: {tool: resultado}}` y escribe `post_analisis.json` en la
    misma carpeta. No lanza si el motor falla: deja el error en el resultado.
    """
    engine = (engine_url or ENGINE_URL).rstrip("/")
    destino = Path(destino)
    resultados: dict = {}

    volcados = [p for p in sorted(destino.glob("*")) if p.is_file() and _es_volcado(p)]
    if not volcados:
        resultados["_aviso"] = (
            "No se encontró ningún volcado de memoria que escanear. Suele pasar "
            "cuando la muestra es de vida corta y termina antes del volcado (p. ej. "
            "el canario bash de aislamiento): usa una muestra de vida larga, como el "
            "espécimen C 'especimen_benigno', que permanece viva hasta el volcado.")
        _guardar(destino, resultados)
        return resultados

    for vol in volcados:
        try:
            with vol.open("rb") as fh:
                up = requests.post(f"{engine}/samples",
                                   files={"file": (vol.name, fh)}, timeout=120)
            up.raise_for_status()
            sha = up.json()["sha256"]
            por_tool = {}
            for tool in HERRAMIENTAS:
                r = requests.get(f"{engine}/samples/{sha}/run/{tool}", timeout=180)
                r.raise_for_status()
                por_tool[tool] = r.json().get("result")
            resultados[vol.name] = {"sha256": sha, **por_tool}
        except Exception as e:  # noqa: BLE001 — best-effort
            resultados[vol.name] = {"error": str(e)}

    _guardar(destino, resultados)
    return resultados


def _guardar(destino: Path, resultados: dict) -> None:
    (destino / "post_analisis.json").write_text(
        json.dumps(resultados, indent=2, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    import sys

    carpeta = sys.argv[1] if len(sys.argv) > 1 else "."
    out = analizar_volcado(carpeta)
    print(json.dumps(out, indent=2, ensure_ascii=False))
