FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends openssh-client \
 && rm -rf /var/lib/apt/lists/*
COPY engine/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY core/__init__.py    core/__init__.py
COPY core/ssh.py         core/ssh.py
COPY docker/__init__.py  docker/__init__.py
COPY docker/debian.py    docker/debian.py
COPY engine/db.py        db.py
COPY engine/main.py      main.py
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
