import json
from pathlib import Path

_ROOT = Path(__file__).parent.parent
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


def docker() -> dict:
    return get()["docker"]


def kali() -> dict:
    return get()["kali"]
