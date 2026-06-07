# estatico/catalogo/ — Catálogo de análisis estático

La **única fuente de verdad** de qué comandos existen. La API del motor (`/tools`,
`/samples/{sha}/run/{tool}`) y la web leen de aquí. El motor lo copia dentro de su
imagen e importa como `catalogo.analizador_estatico`.

## Archivos

| Archivo                   | Responsabilidad                                                         |
|---------------------------|-------------------------------------------------------------------------|
| `analizadores.py`         | Una función por herramienta: `fn(client, ruta, **opts)`. Se ejecutan por SSH dentro del sandbox. Incluye `yara_reglas` (introspección de reglas). |
| `comando_guiado.py`       | El comando suelto que escribe el usuario (`comando_personalizado`) + las sugerencias de `comandos.json`. Rechaza metacaracteres de shell. |
| `registro.py`             | El `CATALOGO` (dataclass `Analizador`), `POR_DEFECTO` y `catalogo_publico()`. |
| `analizador_estatico.py`  | **Fachada**: reexporta lo que usa el motor. Importa siempre desde aquí. |
| `comandos.json`           | Lista blanca de comandos sugeridos en la web.                           |

## Añadir un análisis nuevo

1. Escribe `def mi_analisis(client, ruta, **opts) -> ...:` en `analizadores.py`.
2. Añade una línea al `CATALOGO` en `registro.py`:
   `Analizador("mi_id", "Mi etiqueta", mi_analisis)`.

Aparece solo en `/tools`, en los checkboxes de la web y en el endpoint genérico.
Marca `cacheable=False` si depende de parámetros, u `oculto=True` para no listarlo.

## Por qué `client.exec_command` y no ejecución local

`ruta` es la ubicación de la muestra **dentro del sandbox** (la subió el motor por
SFTP, ver `compartido/sftp/conexion.py`). Los analizadores nunca tocan el binario
en el host: lo inspeccionan por SSH en el contenedor aislado.
