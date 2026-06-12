# Plan — habilitar el análisis dinámico y el grafo MITRE

Hoja de ruta del laboratorio: qué se hizo, **qué hacer antes de detonar la primera
muestra real**, cómo correr el dinámico y los próximos pasos del grafo ATT&CK.

## 1. Estado actual (esta iteración)

Lado **dinámico** (host, fuera de Docker):

- **Snapshot limpio reproducible** — `dinamico/analizador/snapshot.py`. Cada
  detonación restaura el estado base (`restaurar_limpio`) → ninguna muestra hereda
  residuos de la anterior. Comandos en `control_maquina_virtual.sh snapshot|restaurar`.
- **Validación del gate de aislamiento** — `dinamico/scripts/validar_aislamiento.sh`
  (camino feliz + camino de fallo con el NAT, sin exponer la VM a internet) y un
  canario benigno para una prueba de extremo a extremo.
- **Servicio host** — `dinamico/analizador/servicio_dinamico.py` (FastAPI, `:8002`).
  Es el puente para que la web (en Docker) dispare detonaciones sin meter
  VBoxManage/iptables en un contenedor. Detona **en serie** (la VM es única).
- **Post-análisis del volcado** — `post_analisis.py`: el volcado pasa por el motor
  ESTÁTICO (reusa `/rules/`, sin duplicar reglas YARA).
- **Mapa MITRE ATT&CK** — `mitre.py`: `strace.log` + YARA del volcado → técnicas y
  grafo táctica→técnica (`mitre.json`).

Lado **estático** (sin tocar Dockerfiles, solo reglas):

- Reglas YARA nuevas/ampliadas en `estatico/sandbox/reglas_yara/`: `packers.yar`
  (UPX binario, MPRESS, gzexe, Ezuri, Go/garble), `ofuscacion.yar` y `entropia.yar`.
  **Requiere reconstruir el sandbox**: `docker compose up -d --build sandbox`.

Lado **web** (Django):

- Página **Análisis dinámico** (`/dynamic/`): readiness de la jaula, subir muestra,
  cola de jobs con estado en vivo.
- Constructor de **experimentos/lotes** reescrito con **Alpine.js** (añadir/quitar
  experimentos, comandos y chips de forma reactiva). El contrato con el backend no
  cambia (`file_<id>`, `mode_<id>`…).

## 2. ANTES de detonar la primera muestra real (orden obligatorio)

1. **Levantar el estático** (para el post-análisis del volcado):
   ```bash
   docker compose up -d --build        # reconstruye sandbox con las YARA nuevas
   ```
2. **Crear el snapshot limpio** (una vez, con la VM recién provisionada):
   ```bash
   bash dinamico/scripts/control_maquina_virtual.sh snapshot kali-malware-lab
   ```
3. **Validar el gate de aislamiento** (feliz + fallo + canario):
   ```bash
   bash dinamico/scripts/validar_aislamiento.sh kali-malware-lab
   python3 dinamico/analizador/analizador_dinamico.py /tmp/canario_aislamiento.sh 10
   ```
   En `dynamic_output/<ts>/stdout.log` NO debe aparecer ninguna `FUGA`; en
   `strace.log` los `connect()` a 1.1.1.1/8.8.8.8 deben fallar.

Solo si los tres pasos pasan limpios → es seguro detonar malware real.

## 3. Cómo correr el dinámico

**CLI (host):**
```bash
python3 dinamico/analizador/analizador_dinamico.py <muestra> 20
```

**Desde la web:** arrancar el servicio host y entrar a la página.
```bash
pip install -e ".[dinamico]"                 # fastapi + uvicorn + multipart
bash dinamico/scripts/servicio_dinamico.sh   # :8002 (el contenedor web lo alcanza
                                             #  por host.docker.internal)
```
Web → http://localhost:8000 → **Análisis dinámico**.

## 4. Flujo de datos de una detonación

```
muestra
  └─▶ restaurar snapshot limpio → aislar (host-only, sin NAT) → firewall host
        → GATE (verificación): si hay fuga, ABORTA sin detonar
        → detonar bajo strace (acotado por tiempo) → volcado de memoria
  └─▶ dynamic_output/<ts>/
        ├─ strace.log, stdout.log, stderr.log, *.core/*.dmp
        ├─ post_analisis.json   (YARA/strings del volcado, vía motor estático)
        └─ mitre.json           (técnicas ATT&CK + grafo táctica→técnica)
```

## 5. Próximos pasos (grafo MITRE en la web)

- **Vista web del grafo**: activar el item «MITRE ATT&CK» (hoy deshabilitado en
  `base.html`) y dibujar `mitre.json` (nodos táctica→técnica). Opciones de render:
  una matriz ATT&CK simple en HTML/CSS, o un grafo con una librería ligera
  (p. ej. Cytoscape.js por CDN, como Alpine).
- **Afinar las reglas** de `mitre.py` con strace reales (hoy es el andamiaje):
  más técnicas, mejor desambiguación de C2 vs. discovery, sub-técnicas.
- **Correlación estático↔dinámico**: enlazar el reporte estático de una muestra
  con su detonación (mismo sha256) para una ficha única por muestra.
- **Endurecer el servicio host**: autenticación simple web↔servicio y límite de
  tamaño/concurrencia de volcados.
