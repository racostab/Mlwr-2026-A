from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import servicios
from rutas import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    servicios.SAMPLES_DIR.mkdir(parents=True, exist_ok=True)
    yield


app = FastAPI(title="Malware Lab Engine", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.include_router(router)
