# dataset/ — Catálogo de muestras botnet ELF

Genera un **dataset de metadatos** de malware tipo botnet en formato ELF,
construido automáticamente desde [MalwareBazaar](https://bazaar.abuse.ch/) (abuse.ch).

Replica las columnas de la hoja `Samples` del ejemplo de referencia
(`docs/Malware-botnet_v1.xlsx`, de Acosta Bermejo Raúl), pero como CSV + JSON
para poder versionarlo en git y consumirlo desde código.

> **Solo cataloga metadatos.** El dataset guarda hashes, familia, arquitectura y
> la URL de origen de cada muestra — **no descarga binarios**. Cada muestra queda
> referenciada por su `sha256` en MalwareBazaar; la descargas tú, dentro del
> entorno aislado del lab, cuando vayas a analizarla.

## Requisitos

- Python 3 con `requests` (`pip install requests`).
- Una **Auth-Key gratuita** de abuse.ch — MalwareBazaar exige autenticación en
  todas las consultas a su API:
  1. Regístrate en https://auth.abuse.ch/
  2. Copia tu Auth-Key del perfil.

## Uso

```bash
export MB_AUTH_KEY=<tu-key>
python3 dataset/scripts/build_dataset.py
```

Opciones:

```bash
# Familias concretas y más muestras por familia
python3 dataset/scripts/build_dataset.py --families Mirai Gafgyt Mozi --limit 300

# Acumular sobre un dataset previo en vez de sobrescribir
python3 dataset/scripts/build_dataset.py --merge

# Pasar la key sin variable de entorno
python3 dataset/scripts/build_dataset.py --auth-key <tu-key>
```

| Opción        | Por defecto                                  | Qué hace                                   |
|---------------|----------------------------------------------|--------------------------------------------|
| `--families`  | Mirai, Gafgyt, Bashlite, Tsunami, Mozi, XorDDoS, Hajime, Kaiji | firmas de familia a consultar |
| `--limit`     | 100                                          | muestras a pedir por familia (máx. 1000)   |
| `--auth-key`  | `$MB_AUTH_KEY`                               | Auth-Key de abuse.ch                       |
| `--out-dir`   | `dataset/`                                   | dónde escribir los archivos de salida      |
| `--merge`     | desactivado                                  | unir con el JSON existente (dedup por hash)|

## Cómo funciona

1. Por cada familia consulta MalwareBazaar (`query=get_siginfo`).
2. Filtra y se queda **solo con las muestras `file_type = elf`** (Necurs, Emotet
   y Qbot se omiten: son PE de Windows).
3. Deduplica por `sha256`, ordena por familia y fecha, y numera.
4. Escribe `botnet_elf.csv` y `botnet_elf.json`.

La arquitectura del procesador (`arm`, `mips`, `x86_64`...) se deduce de los
tags de cada muestra.

## Salida

### `botnet_elf.csv`

Columnas alineadas con la hoja `Samples` del ejemplo:

`no, familia, anio, md5, sha1, sha256, url_origen, existe, virustotal,
porc_deteccion, procesador, so_formato, cve, cve_link, first_seen, file_name,
file_size, tags, reporter`

### `botnet_elf.json`

Catálogo completo, con más campos por muestra (`ssdeep`, `tlsh`, `telfhash`,
`mime`, `last_seen`) y una cabecera con la fecha de generación y las familias
consultadas. Pensado para consumirlo desde el `engine` o la CLI.

## Campos a rellenar a mano

Dos columnas quedan vacías porque no las da MalwareBazaar:

- **`porc_deteccion`** — el ratio de detección de VirusTotal (p. ej. `44/65`).
  El campo `virustotal` ya trae el enlace directo al informe; el ratio requiere
  una API key de VirusTotal.
- **`cve` / `cve_link`** — la vulnerabilidad explotada, que se determina durante
  el análisis de la muestra.
