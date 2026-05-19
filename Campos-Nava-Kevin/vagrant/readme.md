# vagrant/ — Provisioning de la VM Kali

Automatiza la creación de la VM Kali para el análisis dinámico, para no tener que
importar y configurar un `.ova` a mano.

La definición de la VM está en el **`Vagrantfile`** (raíz del proyecto); esta
carpeta contiene el script que la configura por dentro.

## `Vagrantfile` (en la raíz)

Define la VM:

- Box `kalilinux/rolling`, hostname `kali-malware-lab`.
- 4 GB de RAM, 2 CPUs, sin GUI (headless).
- Reenvío de puertos: host **2222** → guest **22** (SSH).
- Copia tu `~/.ssh/id_rsa.pub` a `/tmp/host_key.pub` dentro de la VM.
- Lanza `vagrant/provision_kali.sh` para terminar la configuración.

## `provision_kali.sh`

Se ejecuta **dentro** de la VM durante `vagrant up` (la primera vez, o tras
`vagrant provision`). Hace:

1. Crea el usuario `kali` (contraseña `kali`, con `sudo`) si no existe.
2. Instala tu llave SSH (`/tmp/host_key.pub`) en `~/.ssh/authorized_keys` del
   usuario `kali`.
3. Endurece `sshd`: solo autenticación por llave pública, sin contraseñas.
4. Instala las herramientas de análisis dinámico:
   `strace`, `ltrace`, `gdb`, `tcpdump`, `tshark`, `netcat`, `binwalk`,
   `file`, `binutils`, `net-tools`, `procps`...

## Uso

Desde la raíz del proyecto:

```bash
vagrant up        # crea y provisiona la VM (primera vez: descarga ~3 GB)
vagrant halt      # apaga la VM
vagrant up        # la vuelve a encender
vagrant destroy   # elimina la VM por completo
```

Tras `vagrant up`, conéctate con:

```bash
ssh -i ~/.ssh/id_rsa -p 2222 kali@127.0.0.1
```
