
import hashlib
import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware

sys.path.insert(0, str(Path(__file__).parent))

from core.ssh import conectar as ssh_conectar
from docker.debian import (
    entropia_archivo,
    exiftool_archivo,
    file_archivo,
    hash_archivo,
    radare_archivo,
    readelf_archivo,
    ssdeep_archivo,
    strings_archivo,
    xxd_archivo,
)
from db import (
    get_report,
    get_sample,
    list_samples,
    save_report,
    save_sample,
)

SAMPLES_DIR  = Path(os.environ.get("SAMPLES_DIR", "/samples"))
SANDBOX_HOST = os.environ.get("SANDBOX_HOST", "sandbox")
SANDBOX_PORT = int(os.environ.get("SANDBOX_PORT", "22"))
SANDBOX_USER = os.environ.get("SANDBOX_USER", "root")
KEY_PATH     = os.environ.get("KEY_PATH", "/keys/id_rsa")


@asynccontextmanager
async def lifespan(app: FastAPI):
    SAMPLES_DIR.mkdir(parents=True, exist_ok=True)
    yield


app = FastAPI(title="Malware Lab Engine", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


def _ssh():
    return ssh_conectar(SANDBOX_HOST, SANDBOX_PORT, SANDBOX_USER, KEY_PATH, label="sandbox")


def _require_sample(sha256: str) -> str:
    p = SAMPLES_DIR / sha256
    if not p.exists():
        raise HTTPException(404, f"Sample {sha256} not found")
    return f"/samples/{sha256}"


def _cached(sha256: str, kind: str, fn):
    cached = get_report(sha256, kind)
    if cached is not None:
        return cached
    remoto = _require_sample(sha256)
    client = _ssh()
    try:
        result = fn(client, remoto)
    finally:
        client.close()
    save_report(sha256, kind, result)
    return result


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/samples")
async def upload(file: UploadFile):
    content = await file.read()
    sha256  = hashlib.sha256(content).hexdigest()
    dest    = SAMPLES_DIR / sha256
    if not dest.exists():
        dest.write_bytes(content)
    save_sample(sha256, file.filename, len(content))
    return {"sha256": sha256, "filename": file.filename, "size": len(content)}


@app.get("/samples")
def all_samples():
    return list_samples()


@app.get("/samples/{sha256}")
def one_sample(sha256: str):
    s = get_sample(sha256)
    if s is None:
        raise HTTPException(404, f"Sample {sha256} not found")
    return s


@app.get("/samples/{sha256}/hash")
def sample_hash(sha256: str):
    return _cached(sha256, "hash", hash_archivo)


@app.get("/samples/{sha256}/file")
def sample_file(sha256: str):
    return {"file": _cached(sha256, "file", file_archivo)}


@app.get("/samples/{sha256}/strings")
def sample_strings(sha256: str, min_len: int = Query(4, ge=1, le=512)):
    remoto = _require_sample(sha256)
    client = _ssh()
    try:
        result = strings_archivo(client, remoto, min_len)
    finally:
        client.close()
    return {"strings": result.splitlines(), "min_len": min_len}


@app.get("/samples/{sha256}/entropy")
def sample_entropy(sha256: str):
    return {"entropy": _cached(sha256, "entropy", entropia_archivo)}


@app.get("/samples/{sha256}/ssdeep")
def sample_ssdeep(sha256: str):
    return {"ssdeep": _cached(sha256, "ssdeep", ssdeep_archivo)}


@app.get("/samples/{sha256}/exiftool")
def sample_exiftool(sha256: str):
    return _cached(sha256, "exiftool", exiftool_archivo)


@app.get("/samples/{sha256}/readelf")
def sample_readelf(sha256: str):
    return {"readelf": _cached(sha256, "readelf", readelf_archivo)}


@app.get("/samples/{sha256}/xxd")
def sample_xxd(sha256: str, length: int = Query(4096, ge=0, le=1_048_576)):
    remoto = _require_sample(sha256)
    client = _ssh()
    try:
        result = xxd_archivo(client, remoto, length)
    finally:
        client.close()
    return {"xxd": result, "length": length}


@app.get("/samples/{sha256}/radare")
def sample_radare(sha256: str):
    return {"radare": _cached(sha256, "radare", radare_archivo)}
