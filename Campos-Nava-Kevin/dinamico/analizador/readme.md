# dinamico/analizador/ — Motor del análisis dinámico

Todo el código Python del lado dinámico, **dividido por responsabilidad** y con
una **fachada**, igual que `estatico/catalogo/`: añadir/entender una pieza es
mirar un solo archivo pequeño, y quien consume el aislamiento importa siempre
desde la fachada.

## Archivos

| Archivo                  | Responsabilidad                                                                 |
|--------------------------|---------------------------------------------------------------------------------|
| `red.py`                 | **Red** de la VM con `VBoxManage`: red host-only `vboxnet0` y **quitar el NAT** (sin internet). |
| `firewall.py`            | **Firewall del host** (firewall local): aplica/comprueba `reglas_firewall/aislar_host.sh` (corta lo que la VM inicie hacia el host). |
| `verificacion.py`        | **Gate de pre-vuelo**: prueba con hechos que la jaula está cerrada (NAT off, host-only, firewall confirmado, internet inalcanzable). Lanza `NoAislada`. |
| `ejecucion.py`           | **Ejecución**: sube la muestra, la corre acotada por tiempo bajo **strace** (syscalls), vuelca memoria (procdump→gcore) y trae resultados (strace.log + stdout/stderr + volcado). |
| **`aislamiento.py`**     | **FACHADA de la jaula**: re-exporta `preparar_aislada`, `aplicar_firewall`, `verificar`, `NoAislada`… El runner importa SIEMPRE desde aquí. |
| `analizador_dinamico.py` | **Entry/orquestador (CLI)**: ata aislamiento + ejecución. Es lo que se corre a mano. |

## Las tres capas del aislamiento (la "jaula")

```
preparar_aislada()  →  aplicar_firewall()  →  verificar()
   red.py                firewall.py            verificacion.py
(host-only, sin NAT)   (firewall del host)   (gate duro: aborta si hay fuga)
```

La fachada `aislamiento.py` es la única dependencia del runner para la jaula
(como el motor estático depende solo de `catalogo.analizador_estatico`):

```python
import aislamiento
ip = aislamiento.preparar_aislada(vm)       # 1. red host-only, sin NAT
aislamiento.aplicar_firewall()              # 2. firewall del host
aislamiento.verificar(vm, client=cliente)   # 3. gate: NoAislada si hay fuga
```

## Uso

```bash
python3 dinamico/analizador/analizador_dinamico.py <muestra> 20   # análisis completo
python3 dinamico/analizador/verificacion.py kali-malware-lab      # solo verificar la jaula
python3 dinamico/analizador/aislamiento.py  kali-malware-lab      # solo aislar (imprime la IP)
```

> Las operaciones de mano de la VM (crear/aislar el lab, controlar y SSH) son
> shell y viven en `dinamico/scripts/`. El transporte SFTP es el compartido
> (`compartido/sftp/conexion.py`).
