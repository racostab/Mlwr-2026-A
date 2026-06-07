# dinamico/ — Análisis dinámico (VM Kali)

Mientras el `sandbox` de Docker hace análisis **estático**, esta carpeta reúne
todo lo del análisis **dinámico**: ejecutar la muestra en una VM Kali aislada y
observar su comportamiento, más el control y provisioning de esa VM.

Va en una VM de VirtualBox (no en Docker) porque el análisis dinámico necesita
un kernel propio aislado. La definición de la VM está en
`dinamico/maquina_virtual/Vagrantfile`.

## Estructura

| Carpeta / archivo                          | Qué hace                                                        |
|--------------------------------------------|-----------------------------------------------------------------|
| `maquina_virtual/Vagrantfile`              | Definición de la VM Kali (memoria, red, provisioning).          |
| `user_data/provision_kali.sh`              | Provisioning de la VM (lo invoca el `Vagrantfile` al `vagrant up`): usuario, llaves, herramientas. |
| `reglas_firewall/aislar_host.sh`           | Firewall host-only: aísla el host de la VM (`vboxnet0`).        |
| `scripts/red_aislada.py`                   | API de VirtualBox (`VBoxManage`): asegura la red host-only, **quita el NAT** de la VM y la arranca aislada (`preparar_aislada`). |
| `scripts/analizador_dinamico.py`           | Orquesta el análisis: deja la VM aislada (vía `red_aislada`), sube la muestra por SFTP, la ejecuta acotada por tiempo y trae un volcado de memoria. |
| `scripts/control_maquina_virtual.sh`       | Control de la VM con `VBoxManage` (`start/stop/suspend/resume`). |
| `scripts/ssh_maquina_virtual.sh`           | Abre una sesión SSH a la VM Kali (lee `config.json`).          |
| `sftp/`                                    | Puntero: la transferencia SFTP usa `compartido/sftp`.          |

## Uso

```bash
(cd dinamico/maquina_virtual && vagrant up)                       # crea/provisiona la VM
python3 dinamico/scripts/analizador_dinamico.py /ruta/muestra 20  # análisis dinámico (20 s)
bash dinamico/scripts/ssh_maquina_virtual.sh                      # SSH a la VM
bash dinamico/scripts/control_maquina_virtual.sh stop kali        # apagar la VM
```

## Configuración

Lee la sección `kali` de `config.json` (usuario, llave, `vm_name`) vía
`compartido.configuracion`. La VM aislada vive en `192.168.56.10:22` (red
host-only); ver `config.example.json`.

## Aislamiento (dos capas)

1. **Red host-only sin NAT.** El `Vagrantfile` da a la VM una IP fija
   (`192.168.56.10`) en la red privada `vboxnet0`. Vagrant provisiona por NAT
   (para clonar la box e instalar llaves) y luego `red_aislada.py` le **quita ese
   NAT**, así la VM se queda sin internet. `setup.sh` lo hace automáticamente al
   decir "sí" a Kali.
2. **Firewall del host.** `analizador_dinamico.py` aplica
   `reglas_firewall/aislar_host.sh` **antes** de ejecutar la muestra: descarta lo
   que la VM inicie hacia el host (solo deja pasar las respuestas a las sesiones
   SSH/SFTP que abre el host). Si `vboxnet0` existe pero el firewall no se puede
   aplicar, aborta (mejor no ejecutar que hacerlo con el host expuesto).

> Las herramientas dinámicas (strace, ltrace, gdb, tcpdump, procdump…) viven en
> la VM, no aquí.
