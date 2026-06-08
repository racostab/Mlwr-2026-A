# dinamico/ — Análisis dinámico (VM Kali)

Mientras el `sandbox` de Docker hace análisis **estático**, esta carpeta reúne
todo lo del análisis **dinámico**: ejecutar la muestra en una VM Kali aislada y
observar su comportamiento, más el control y provisioning de esa VM.

Va en una VM de VirtualBox (no en Docker) porque el análisis dinámico necesita
un kernel propio aislado. La definición de la VM está en
`dinamico/maquina_virtual/Vagrantfile`.

## Estructura

Igual que `estatico/` separa el código en paquetes por responsabilidad
(`catalogo/` con fachada + `motor/`), aquí el código Python vive en el paquete
**`analizador/`** (con su fachada `aislamiento.py`) y las operaciones de mano
(shell) en **`scripts/`**.

| Carpeta / archivo                          | Qué hace                                                        |
|--------------------------------------------|-----------------------------------------------------------------|
| `maquina_virtual/Vagrantfile`              | Definición de la VM Kali (memoria, red, provisioning).          |
| `user_data/provision_kali.sh`              | Provisioning de la VM (lo invoca el `Vagrantfile` al `vagrant up`): usuario, llaves, herramientas. |
| `reglas_firewall/aislar_host.sh`           | Reglas iptables del **firewall del host** (firewall local): aísla el host de la VM (`vboxnet0`). |
| **`analizador/`**                          | **Motor del dinámico** (Python, por responsabilidad + fachada). Ver `analizador/readme.md`. |
| `analizador/red.py`                        | `VBoxManage`: red host-only y **quita el NAT** de la VM (`preparar_aislada`). |
| `analizador/firewall.py`                   | Aplica/comprueba el **firewall del host** (envuelve `aislar_host.sh`). |
| `analizador/verificacion.py`               | **Gate de pre-vuelo (todo crítico)**: prueba con hechos la jaula (NAT off, host-only, **firewall confirmado**, **internet inalcanzable**). Lanza `NoAislada`. |
| `analizador/ejecucion.py`                  | Sube la muestra, la ejecuta acotada por tiempo y vuelca memoria. |
| `analizador/aislamiento.py`                | **FACHADA de la jaula**: el runner importa el aislamiento SIEMPRE desde aquí. |
| `analizador/analizador_dinamico.py`        | **Entry/orquestador (CLI)**: ata aislamiento + ejecución. |
| `scripts/configurar_dinamico.sh`           | **Orquestación de setup**: prepara TODO en un paso (vagrant up → aislar → firewall → **verificar**). Lo invoca `setup.sh`; también suelto. |
| `scripts/control_maquina_virtual.sh`       | Control de la VM con `VBoxManage` (`start/stop/suspend/resume`). |
| `scripts/ssh_maquina_virtual.sh`           | Abre una sesión SSH a la VM Kali (lee `config.json`).          |
| `sftp/`                                    | Puntero: la transferencia SFTP usa `compartido/sftp`.          |

## Uso

```bash
bash dinamico/scripts/configurar_dinamico.sh                        # prepara TODO: crea+aísla+verifica la VM
python3 dinamico/analizador/analizador_dinamico.py /ruta/muestra 20 # análisis dinámico (20 s)
bash dinamico/scripts/ssh_maquina_virtual.sh                        # SSH a la VM
bash dinamico/scripts/control_maquina_virtual.sh stop kali          # apagar la VM
```

> `setup.sh` ya llama a `configurar_dinamico.sh` si dices "sí" a Kali: no hay que
> correrlo a mano salvo para (re)preparar el lab por separado. Crear la VM a pelo
> con `vagrant up` la deja **con NAT (internet)**; usa el módulo para que quede
> aislada y verificada.

## Configuración

Lee la sección `kali` de `config.json` (usuario, llave, `vm_name`) vía
`compartido.configuracion`. La VM aislada vive en `192.168.56.10:22` (red
host-only); ver `config.example.json`.

## Aislamiento (tres capas)

1. **Red host-only sin NAT** (`analizador/red.py`). El `Vagrantfile` da a la VM
   una IP fija (`192.168.56.10`) en la red privada `vboxnet0`. Vagrant provisiona
   por NAT (para clonar la box e instalar llaves) y luego `red.py` le **quita ese
   NAT** (deja `nic1` en `null`), así la VM se queda sin internet. `setup.sh` lo
   hace automáticamente al decir "sí" a Kali.
2. **Firewall del host / firewall local** (`analizador/firewall.py`). Aplica
   `reglas_firewall/aislar_host.sh` **antes** de ejecutar la muestra: descarta lo
   que la VM inicie hacia el host (solo deja pasar las respuestas a las sesiones
   SSH/SFTP que abre el host). Si `vboxnet0` existe pero el firewall no se puede
   aplicar, aborta (mejor no ejecutar que hacerlo con el host expuesto).
3. **Verificación de pre-vuelo (gate duro, todo crítico)** (`analizador/verificacion.py`).
   Antes de subir/ejecutar la muestra, el runner llama a `aislamiento.verificar()`
   (fachada → `verificacion`), que **prueba de verdad** que la jaula está cerrada.
   Las cuatro comprobaciones son **críticas** (cualquiera que falle aborta con
   `NoAislada`): NAT desconectado, host-only presente, **firewall confirmado**
   (lee el `DROP` con `sudo -n`; si no lo puede confirmar, no detona) y —la prueba
   de fuego— que **la VM no alcanza internet** (intenta TCP a `1.1.1.1`/`8.8.8.8:53`
   y DNS desde dentro; todo debe fallar). Se puede correr suelto para diagnóstico:

   ```bash
   python3 dinamico/analizador/verificacion.py kali-malware-lab
   ```

> Las herramientas dinámicas (strace, ltrace, gdb, tcpdump, procdump…) viven en
> la VM, no aquí.
