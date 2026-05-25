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
