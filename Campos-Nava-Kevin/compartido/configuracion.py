import json
import os
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
_cfg  = None


def get() -> dict:
    global _cfg
    if _cfg is None:
        path = _ROOT / "config.json"
        if not path.exists():
            raise FileNotFoundError(
                "config.json no encontrado.\n"
                "Copia config.example.json → config.json y edita los valores."
            )
        with path.open() as f:
            _cfg = json.load(f)
    return _cfg


def kali() -> dict:
    cfg = dict(get()["kali"])
    # `key_path` admite ~, ruta absoluta o ruta relativa al repo (p. ej.
    # "lab_keys/id_rsa"); esto último se resuelve contra la raíz para que no
    # dependa de desde dónde se ejecute.
    kp = cfg.get("key_path", "")
    if kp and not kp.startswith("~") and not os.path.isabs(kp):
        cfg["key_path"] = str(_ROOT / kp)
    return cfg
