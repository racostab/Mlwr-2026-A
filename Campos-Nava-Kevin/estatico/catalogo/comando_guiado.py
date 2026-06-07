"""Comando guiado: el analista escribe UN comando y se ejecuta sobre la muestra.

"Guiado" en serio: solo se permiten los binarios de la whitelist, que se deriva
de `comandos.json` (el primer token de cada comando predefinido). Cualquier otro
binario se rechaza ANTES de ejecutar. Además se prohíben los metacaracteres de
shell (para que sea un comando suelto, no una shell) y se valida con shlex.
"""
import json
import os
import shlex
from pathlib import Path

# Comandos predefinidos que la web ofrece como sugerencias (id, etiqueta, cmd).
_COMMANDS_JSON = Path(__file__).with_name("comandos.json")

# Metacaracteres de shell que encadenarían/redirigirían comandos. Se rechazan
# para ejecutar UN solo comando por vez, no una shell.
_METACARACTERES = set(";|&`$><\n\\\r")

# Whitelist de binarios permitidos (se calcula una vez desde comandos.json).
_PERMITIDOS: set[str] | None = None


def comandos_extra() -> list[dict]:
    """Lista [{id, etiqueta, cmd}] de comandos predefinidos (desde el JSON)."""
    try:
        return json.loads(_COMMANDS_JSON.read_text())["comandos"]
    except Exception:
        return []


def binarios_permitidos() -> set[str]:
    """Whitelist: el primer token (binario) de cada comando de comandos.json.

    Se compara por nombre base, así `/usr/bin/objdump` y `objdump` cuentan igual.
    """
    global _PERMITIDOS
    if _PERMITIDOS is None:
        permitidos = set()
        for c in comandos_extra():
            cmd = (c.get("cmd") or "").strip()
            if not cmd:
                continue
            try:
                primero = shlex.split(cmd)[0]
            except (ValueError, IndexError):
                continue
            permitidos.add(os.path.basename(primero))
        _PERMITIDOS = permitidos
    return _PERMITIDOS


def comando_personalizado(client, ruta: str, *, cmd: str = "", **_) -> str:
    """Ejecuta el comando indicado sobre la muestra, si pasa todas las validaciones.

    Orden: no vacío → sin metacaracteres → bien formado (shlex) → binario en la
    whitelist. Solo entonces se ejecuta, anexando la ruta de la muestra al final.
    """
    cmd = (cmd or "").strip()
    if not cmd:
        return "[!] Comando vacío."
    if any(ch in cmd for ch in _METACARACTERES):
        return "[!] No se permite encadenar/redirigir comandos ( ; | & $ ` > < \\ )."
    try:
        tokens = shlex.split(cmd)
    except ValueError as e:
        return f"[!] Comando inválido: {e}"
    if not tokens:
        return "[!] Comando vacío."

    binario = os.path.basename(tokens[0])
    permitidos = binarios_permitidos()
    if binario not in permitidos:
        return (
            f"[!] Comando no permitido: '{binario}'.\n"
            f"    Solo se permiten: {', '.join(sorted(permitidos))}."
        )

    full = f"{cmd} {shlex.quote(ruta)}"
    _, stdout, stderr = client.exec_command(full)
    stdout.channel.recv_exit_status()
    out = stdout.read().decode(errors="replace").rstrip("\n")
    err = stderr.read().decode(errors="replace").strip()
    cuerpo = out or err or "(sin salida)"
    return f"$ {full}\n\n{cuerpo}"
