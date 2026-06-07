FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends openssh-client \
 && rm -rf /var/lib/apt/lists/*
COPY estatico/user_data/motor/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Paquete compartido (conexión SSH/SFTP + configuración), instalado como librería.
COPY pyproject.toml /pkg/pyproject.toml
COPY compartido /pkg/compartido
RUN pip install --no-cache-dir /pkg

# Catálogo de análisis estático (solo lo necesita el motor; no es librería compartida).
COPY estatico/catalogo catalogo

# Código del motor (API REST).
COPY estatico/motor/repositorio.py repositorio.py
COPY estatico/motor/servicios.py   servicios.py
COPY estatico/motor/rutas.py       rutas.py
COPY estatico/motor/principal.py   principal.py
CMD ["uvicorn", "principal:app", "--host", "0.0.0.0", "--port", "8001"]
