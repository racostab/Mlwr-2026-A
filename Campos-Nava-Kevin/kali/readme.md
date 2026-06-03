# kali/ — Análisis dinámico (VM Kali)

Mientras el `sandbox` de Docker hace análisis **estático**, esta VM Kali sirve
para análisis **dinámico**: ejecutar la muestra y observar su comportamiento
(`strace`, `ltrace`, `gdb`, `tcpdump`, `tshark`, `binwalk`...).

Va en una VM de VirtualBox y **no** en Docker, porque el análisis dinámico
necesita un kernel propio aislado.

## Conexión

La VM expone SSH en el **puerto 2222 del host** (→ 22 de la VM). Los datos de
conexión están en `config.json` (raíz del proyecto), bloque `kali`:

```json
"kali": {
  "host": "127.0.0.1",
  "port": 2222,
  "user": "kali",
  "key_path": "~/.ssh/id_rsa",
  "vm_name": "kali-malware-lab"
}
```

> Copia `config.example.json` → `config.json` si aún no existe. `config.json`
> está en `.gitignore`.

## Red aislada (host-only)

Para análisis dinámico la VM usa una red **host-only** (`vboxnet0`,
`192.168.56.0/24`): el host la alcanza por SSH, pero la VM **no tiene salida a
internet**, así que la muestra no puede llamar a su C2. Con esta configuración
`config.json` apunta directo a la IP de la VM en el puerto 22 (no al forward NAT
2222):

```json
"kali": {
  "host": "192.168.56.101",
  "port": 22,
  "user": "kali",
  "key_path": "~/.ssh/id_rsa",
  "vm_name": "kali"
}
```

Cómo se configuró (con la VM apagada, VirtualBox ≥ 7):

```bash
# 1. crear la interfaz host-only (si no existe) con su IP de host
VBoxManage hostonlyif create
VBoxManage hostonlyif ipconfig vboxnet0 --ip 192.168.56.1 --netmask 255.255.255.0
# (el servidor DHCP de vboxnet0 reparte 192.168.56.101–254)

# 2. pasar el adaptador 1 de NAT a host-only (persistente)
VBoxManage modifyvm kali --nic1 hostonly --hostonlyadapter1 vboxnet0

# 3. arrancar y leer la IP que tomó por DHCP (necesita Guest Additions)
VBoxManage startvm kali --type headless
VBoxManage guestproperty get kali "/VirtualBox/GuestInfo/Net/0/V4/IP"
```

> **Revertir a NAT** (si necesitaras internet en la VM): con la VM apagada,
> `VBoxManage modifyvm kali --nic1 nat` y vuelve a poner `host: 127.0.0.1`,
> `port: 2222` en `config.json`.
>
> La IP `.101` es la primera concesión DHCP; suele mantenerse para la misma MAC.
> Si cambiara, vuelve a leerla con el `guestproperty get` de arriba.

### Firewall: aislar el host de la VM

Host-only **no** aísla del host: la VM alcanza tu laptop en `192.168.56.1`. Un
botnet suele escanear su subred y hacer fuerza bruta SSH para propagarse, así que
hay que blindar al host. `kali/isolate_host.sh` aplica reglas de iptables que
**descartan toda conexión que inicie la VM hacia el host** (permitiendo las
respuestas a las sesiones que abre el host, para que SSH/SFTP sigan).

```bash
bash kali/isolate_host.sh        # pide sudo
```

> Las reglas de iptables y la interfaz `vboxnet0` **no sobreviven a reiniciar el
> host**: vuelve a correr el script al reanudar el lab. Ejecútalo **antes** de
> lanzar `dynamic.py` con una muestra real.

`setup.sh` ya lo ejecuta automáticamente al final, **si** detecta la interfaz
`vboxnet0` (es decir, si la VM dinámica ya existe). Ojo: `vboxnet0` solo aparece
una vez que la VM host-only ha arrancado al menos una vez tras encender el host;
si corres `setup.sh` antes de arrancar la VM, este paso se salta y tendrás que
correr `bash kali/isolate_host.sh` a mano después de levantar la VM.

Además, `dynamic.py` lo aplica por su cuenta justo antes de ejecutar cada
muestra (tras levantar la VM): si existe `vboxnet0` pero el firewall falla,
**aborta** en vez de correr el malware con el host expuesto. Por eso `dynamic.py`
puede pedirte sudo al arrancar.

Aun así, *ningún* aislamiento es perfecto (escapes de hipervisor, Guest
Additions). Buenas prácticas extra: toma un **snapshot** limpio antes de ejecutar
y revierte después; mantén el portapapeles/arrastrar-soltar en `disabled`.

## Cómo levantar la VM

### Opción A — Vagrant *(recomendada)*

Automatiza todo. Ver `vagrant/readme.md`.

```bash
vagrant up        # primera vez descarga el box (~3 GB)
vagrant halt      # apagar
vagrant destroy   # eliminar
```

Vagrant instala tu llave pública `~/.ssh/id_rsa.pub` dentro de la VM, que es la
que espera `config.json` por defecto (`key_path: ~/.ssh/id_rsa`).

### Opción B — VirtualBox manual (`.ova`)

1. VirtualBox → *Archivo → Importar servicio virtualizado* → selecciona el `.ova`.
2. Con la VM apagada: *Configuración → Red → Adaptador 1 → Avanzado → Reenvío de
   puertos*. Agrega la regla:

   | Nombre | Protocolo | Puerto anfitrión | Puerto invitado |
   |--------|-----------|------------------|-----------------|
   | SSH    | TCP       | 2222             | 22              |

3. Inicia la VM.
4. Copia tu llave pública (genera una con `ssh-keygen -t rsa -b 4096` si no
   tienes):

   ```bash
   sshpass -p kali ssh-copy-id -i ~/.ssh/id_rsa.pub -p 2222 \
       -o StrictHostKeyChecking=no kali@127.0.0.1
   ```

## Scripts

### `kali.sh` — shell SSH a la VM

Abre una sesión SSH leyendo los datos de `config.json` (necesita `jq`):

```bash
bash kali/kali.sh
```

### `cli.sh` — control de la VM con `VBoxManage`

Enciende/apaga la VM usando la CLI de VirtualBox:

```bash
./cli.sh start   <vm_name>
./cli.sh stop    <vm_name>
./cli.sh suspend <vm_name>
./cli.sh resume  <vm_name>
```

### `api.py` — control de la VM con el SDK de VirtualBox

Lo mismo que `cli.sh`, pero por la API de Python (`vboxapi`):

```bash
python3 api.py start|stop|pause|resume [vm_name]
```

Si `vboxapi` no está instalado, avisa y sugiere usar `cli.sh`. El `vm_name` por
defecto sale de `config.json`.

### `dynamic.py` — análisis dinámico automatizado (procdump)

Hace todo el flujo dinámico en un comando: enciende la VM, ejecuta la muestra
y captura un **volcado de memoria** con `procdump`.

```bash
python3 kali/dynamic.py <ruta_local> [segundos_ejecucion]   # por defecto 20s
```

Pasos: enciende la VM `kali` (headless) → espera SSH → sube la muestra por SFTP →
la ejecuta en segundo plano bajo `timeout` → `procdump -n 1 <PID>` (o `gcore` si
falla) → trae el volcado y los logs a `./dynamic_output/<timestamp>/`.

> **Ejecuta la muestra de verdad.** Úsalo solo en la VM desechable y aislada.
> La VM queda encendida al terminar (apágala con `cli.sh stop kali`).

#### Requisitos en la VM (instálalos una vez)

`procdump` no viene en Kali por defecto y el volcado necesita `ptrace` sobre
procesos no-descendientes + `sudo` no interactivo. Conéctate
(`bash kali/kali.sh`) y ejecuta **dentro de la VM**:

```bash
# 1. procdump — está en los propios repos de Kali, no hace falta el repo de Microsoft
sudo apt-get update
sudo apt-get install -y procdump

# 2. permitir el volcado de memoria
echo 'kernel.yama.ptrace_scope=0' | sudo tee /etc/sysctl.d/10-ptrace.conf
sudo sysctl -p /etc/sysctl.d/10-ptrace.conf
echo 'kali ALL=(ALL) NOPASSWD: ALL' | sudo tee /etc/sudoers.d/kali-lab
sudo chmod 440 /etc/sudoers.d/kali-lab
```

Si `procdump` te diera problemas, `gcore` (de `gdb`, ya instalado) cumple la
misma función y `dynamic.py` lo usa como alternativa automática.
