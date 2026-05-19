import json
import os
from contextlib import contextmanager

import psycopg

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://lab:lab@db:5432/lab")


@contextmanager
def _conn():
    with psycopg.connect(DATABASE_URL) as c:
        yield c


def save_sample(sha256: str, filename: str, size: int) -> None:
    with _conn() as c, c.cursor() as cur:
        cur.execute(
            "INSERT INTO samples (sha256, filename, size) VALUES (%s, %s, %s) "
            "ON CONFLICT (sha256) DO NOTHING",
            (sha256, filename, size),
        )


def list_samples() -> list[dict]:
    with _conn() as c, c.cursor() as cur:
        cur.execute(
            "SELECT sha256, filename, size, uploaded_at FROM samples ORDER BY uploaded_at DESC"
        )
        return [
            {"sha256": r[0], "filename": r[1], "size": r[2], "uploaded_at": r[3].isoformat()}
            for r in cur.fetchall()
        ]


def get_sample(sha256: str) -> dict | None:
    with _conn() as c, c.cursor() as cur:
        cur.execute(
            "SELECT sha256, filename, size, uploaded_at FROM samples WHERE sha256=%s",
            (sha256,),
        )
        r = cur.fetchone()
        if r is None:
            return None
        return {"sha256": r[0], "filename": r[1], "size": r[2], "uploaded_at": r[3].isoformat()}


def get_report(sha256: str, kind: str):
    with _conn() as c, c.cursor() as cur:
        cur.execute(
            "SELECT payload FROM reports WHERE sha256=%s AND kind=%s",
            (sha256, kind),
        )
        r = cur.fetchone()
        return r[0] if r else None


def save_report(sha256: str, kind: str, payload) -> None:
    with _conn() as c, c.cursor() as cur:
        cur.execute(
            "INSERT INTO reports (sha256, kind, payload) VALUES (%s, %s, %s) "
            "ON CONFLICT (sha256, kind) DO UPDATE SET payload=EXCLUDED.payload, created_at=now()",
            (sha256, kind, json.dumps(payload)),
        )
