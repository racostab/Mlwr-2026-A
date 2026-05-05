import os
import tempfile
import sys
from pathlib import Path

from fastapi import FastAPI, UploadFile, Query
from fastapi.middleware.cors import CORSMiddleware

sys.path.insert(0, str(Path(__file__).parent))

from core.ssh import conectar as ssh_conectar, subir
from docker.debian import (
    hash_archivo, file_archivo, strings_archivo,
    entropia_archivo, ssdeep_archivo,
)

app = FastAPI(title="Malware Lab Engine")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

DEBIAN_HOST = os.environ.get("DEBIAN_HOST", "127.0.0.1")
DEBIAN_PORT = int(os.environ.get("DEBIAN_PORT", "2223"))
DEBIAN_USER = os.environ.get("DEBIAN_USER", "root")
KEY_PATH    = os.environ.get("KEY_PATH", os.path.expanduser("~/.ssh/id_rsa"))


def _client():
    return ssh_conectar(DEBIAN_HOST, DEBIAN_PORT, DEBIAN_USER, KEY_PATH, label="Debian")


def _upload(client, file: UploadFile) -> str:
    content = file.file.read()
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(content)
        local = tmp.name
    remoto = f"/tmp/{file.filename}"
    subir(client, local, remoto)
    os.unlink(local)
    return remoto


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/static/analyze")
async def analyze(
    file: UploadFile,
    min_len: int = Query(4, description="Longitud mínima para strings"),
):
    client = _client()
    remoto = _upload(client, file)
    result = {
        "filename": file.filename,
        "hash":     hash_archivo(client, remoto),
        "file":     file_archivo(client, remoto),
        "strings":  strings_archivo(client, remoto, min_len).splitlines(),
        "entropy":  entropia_archivo(client, remoto),
        "ssdeep":   ssdeep_archivo(client, remoto),
    }
    client.close()
    return result
