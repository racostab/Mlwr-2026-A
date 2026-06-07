# tests/ — Pruebas del lab

Dos niveles:

- **Unitarios** (no necesitan Docker): catálogo, paquete compartido y que el motor
  monte sus rutas. Corren en segundos.
- **Integración** (`test_integracion.py`): ejercita la cadena real
  web→engine→SFTP→sandbox. Se **salta solo** si el engine no responde, así que la
  suite pasa igual sin el lab levantado.

## Correr todo

Desde la raíz del repo, un solo comando (crea un venv aislado, instala lo justo y
corre pytest + `docker compose config` + `manage.py check`):

```bash
bash run_tests.sh
```

## Solo los unitarios, a mano

```bash
pip install -e . pytest          # compartido + pytest
pip install -r estatico/user_data/motor/requirements.txt   # para importar el motor
pytest tests -q
```

## Con el lab levantado (incluye integración)

```bash
docker compose up -d --build
pytest tests -q                  # ahora test_integracion.py SÍ corre
# o apuntando a otra URL:  ENGINE_URL=http://localhost:8001 pytest tests -q
```

## Qué cubre cada archivo

| Archivo                 | Qué valida                                                       |
|-------------------------|------------------------------------------------------------------|
| `test_catalogo.py`      | Integridad del `CATALOGO`, `por_defecto`, comando guiado seguro.  |
| `test_compartido.py`    | Existen `conectar`/`subir`/`asegurar_remoto`; `conectar` falla sin llave. |
| `test_motor.py`         | La app FastAPI monta sus rutas; `/health`, `/tools`, `/commands`. |
| `test_integracion.py`   | Subir muestra + correr `hash` en el sandbox (SFTP real).          |
| `test_dinamico_aislamiento.py` | **Opt-in.** Aislamiento de la VM Kali: SFTP aprobado, conexiones VM→host/internet rechazadas. |

## Test de aislamiento dinámico (VM Kali)

`test_dinamico_aislamiento.py` **no corre por defecto** (necesita VirtualBox y la
VM Kali). Se salta solo si no están, así que no estorba a la suite normal.

Qué valida, con la VM en una red host-only de VirtualBox + el firewall aplicado:

- ✅ **Entrada por SFTP**: el host sube y recupera un archivo de la VM (canal aprobado).
- ❌ **VM → host**: la VM intenta abrir conexiones al host (puertos 22, 8001) y el
  firewall las descarta.
- ❌ **VM → internet**: sin NAT (red host-only), la VM no tiene salida.

La preparación de la red aislada usa la API de VirtualBox (`VBoxManage`), en
`dinamico/scripts/red_aislada.py`: crea `vboxnet0`, pone la NIC de la VM en
host-only sin NAT, la arranca y lee su IP por Guest Additions.

```bash
# requiere VirtualBox; aplicar el firewall usa sudo (iptables)
LAB_DINAMICO=1 pytest tests/test_dinamico_aislamiento.py -v        # usa la VM ya existente
LAB_DINAMICO=1 LAB_DINAMICO_CREAR=1  pytest tests/test_dinamico_aislamiento.py -v   # la crea (vagrant)
LAB_DINAMICO=1 LAB_DINAMICO_APAGAR=1 pytest tests/test_dinamico_aislamiento.py -v   # la apaga al final
```
