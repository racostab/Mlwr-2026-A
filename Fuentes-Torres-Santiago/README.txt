markdown# Laboratorio de Análisis Estático de Malware
**Fuentes Torres Santiago — Mlwr-2026-A**

---

## Descripción

Laboratorio de análisis estático de archivos sospechosos.
Arquitectura cliente-servidor donde el servidor automatiza
el levantamiento de Docker y ejecuta el análisis en un
contenedor aislado.

---

## Estructura del proyecto
entrega2/
├── alma_srv.py          Servidor del laboratorio
├── alma_clt.py          Cliente CLI
├── config.py            Configuración global
├── laboratorio.py       Análisis estático integrado
├── Dockerfile           Imagen del contenedor de análisis
│
├── modulos/             Módulos de análisis
│   ├── hashes.py        MD5, SHA1, SHA256
│   ├── entropia.py      Entropía de Shannon
│   ├── tipo_archivo.py  Tipo por magic bytes
│   ├── cadenas.py       Strings del binario
│   └── ssdeep.py        Fuzzy hashing / similitud
│
├── experimentos/        Archivos a analizar (colocar aquí)
└── resultados/          Resultados generados

---

## Requisitos

- Windows 10/11
- Python 3.x
- Docker Desktop instalado y corriendo
- VirtualBox (para análisis dinámico — Prototipo 4)

---

## Instalación

### 1. Clonar el repositorio
```bash
git clone <url-repositorio>
cd Fuentes-Torres-Santiago/entrega2
```

### 2. Construir la imagen Docker
```bash
docker build -t lab-malware .
```

La imagen incluye:
- Python 3
- `file` — detección de tipo de archivo
- `exiftool` — metadata
- `strings` — cadenas de binarios
- `ssdeep` — fuzzy hashing nativo

---

## Uso

### Iniciar el servidor
```bash
python alma_srv.py
```
El servidor queda escuchando en `localhost:9999`.
Mantenerlo corriendo en una terminal aparte.

---

### Analizar un archivo
```bash
python alma_clt.py analizar [archivo]
```

El archivo puede ser:
- Nombre solo → lo busca en `experimentos/`
- Ruta completa → `C:\ruta\al\archivo.exe`

**Ejemplos:**
```bash
# Archivo en experimentos/
python alma_clt.py analizar malware.exe

# Ruta completa
python alma_clt.py analizar C:\muestras\sospechoso.exe
```

**El servidor automáticamente:**
1. Verifica que Docker esté corriendo
2. Verifica que la imagen `lab-malware` exista
3. Crea o inicia el contenedor `ciber-lab`
4. Copia el archivo al contenedor
5. Ejecuta el análisis completo:
   - `file` — tipo de archivo
   - `exiftool` — metadata
   - `strings` — cadenas legibles
   - `ssdeep` — fuzzy hash
   - Python — MD5, SHA1, SHA256, entropía
6. Regresa los resultados
7. Elimina el archivo del contenedor

---

### Analizar todos los archivos de una carpeta
```bash
python alma_clt.py analizar-dir [carpeta]
```

**Ejemplos:**
```bash
# Carpeta en experimentos/
python alma_clt.py analizar-dir experimentos

# Carpeta específica
python alma_clt.py analizar-dir C:\muestras
```

Al finalizar todos los análisis, compara automáticamente
la similitud entre todos los archivos usando ssdeep:
COMPARACIÓN DE SIMILITUD (SSDEEP)
archivo1.exe  vs  archivo2.exe
Similitud: 87%  —  ⚠ MUY SIMILARES — posible variante

**Niveles de alerta:**
| Similitud | Nivel |
|-----------|-------|
| 80-100%   | ⚠ MUY SIMILARES — posible variante de malware |
| 50-79%    | ~ PARCIALMENTE SIMILARES |
| 0-49%     | OK — archivos diferentes |

---

### Controlar VirtualBox
```bash
python alma_clt.py vm list
python alma_clt.py vm start ciber
python alma_clt.py vm stop  ciber
python alma_clt.py vm pause ciber
python alma_clt.py vm resume ciber
python alma_clt.py vm status ciber
```

### Controlar Docker
```bash
python alma_clt.py docker list
python alma_clt.py docker start ciber-lab
python alma_clt.py docker stop  ciber-lab
python alma_clt.py docker exec  whoami
python alma_clt.py docker logs  ciber-lab
```

### Verificar conexión
```bash
python alma_clt.py ping
```

---

## Flujo completo
Windows
│
├── alma_clt.py analizar archivo.exe
│       │
│       └── alma_srv.py (localhost:9999)
│               │
│               ├── Verifica Docker
│               ├── Levanta ciber-lab (lab-malware)
│               ├── Copia archivo → contenedor
│               ├── Ejecuta: file, exiftool, strings, ssdeep, python
│               ├── Elimina archivo del contenedor
│               └── Regresa resultados → alma_clt.py
│
└── Resultado mostrado en pantalla

---

## Configuración

Editar `config.py` para cambiar:

| Variable | Default | Descripción |
|----------|---------|-------------|
| `SRV_HOST` | `localhost` | Host del servidor |
| `SRV_PORT` | `9999` | Puerto del servidor |
| `DOCKER_IMAGEN` | `lab-malware` | Imagen Docker |
| `DOCKER_CONTENEDOR` | `ciber-lab` | Nombre del contenedor |
| `VM_NOMBRE` | `ciber` | VM de VirtualBox |
| `SSH_ALIAS` | `ciber-vm` | Alias SSH |

---

## Módulos independientes

Cada módulo puede usarse por separado:

```bash
python modulos/hashes.py       archivo.exe
python modulos/entropia.py     archivo.exe
python modulos/tipo_archivo.py archivo.exe
python modulos/cadenas.py      archivo.exe --min 6
python modulos/ssdeep.py       archivo1.exe archivo2.exe
python modulos/ssdeep.py       --dir carpeta/
```

---

## Estado del proyecto

| Prototipo | Descripción | Estado |
|-----------|-------------|--------|
| P1 | Contenedores + Cliente/Servidor | ✅ |
| P2 | Estructura de carpetas y config | ✅ |
| P3 | Análisis Estático / Docker | ✅ |
| P4 | Análisis Dinámico / Hipervisor | ⏳ Pendiente |