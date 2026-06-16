# Reporte de IOCs — XorDDoS

**Muestra:** `2baf73eae1c5135acf10290b063d0a65827611ba6874a326883d9be3b238a1b6.elf`
**Fecha de análisis:** 2026-06-14
**Job dinámico:** `dynamic_output/20260614-214413/` (dump: `dump_0.505`, 26 MB)

> Indicadores *defangueados* (`[.]`, `hxxp`) para manejo seguro. Los IOCs en claro
> salieron del **volcado de memoria** (config desempacada), no del binario en disco.

---

## Identificación

| Campo | Valor |
|---|---|
| Familia | **XorDDoS** (Linux/Xor.DDoS) — YARA: `XorDDoS` |
| Tipo | ELF 32-bit, estático, *stripped*; bot DDoS con rootkit LKM |
| Disfraz de proceso | renombrado a `uptime`; relocalizado a `/tmp/witpunnhsu` |
| Clave XOR (cifra strings/config) | `BB2FA36AAA9541F0` |
| YARA (todas) | `AntiAnalisis_Proc`, `Cap_Persistencia`, `Cap_Shell_Embebida`, `ELF_32bit`, `ELF_Ejecutable`, `ELF_Sin_Secciones`, `Red_HTTP_Cliente`, `Red_Sockets`, `XorDDoS` |

## Hashes

| Artefacto | SHA-256 |
|---|---|
| Muestra | `2baf73eae1c5135acf10290b063d0a65827611ba6874a326883d9be3b238a1b6` |
| Volcado de memoria | `bd997ed89ebf78d5eca7cca39b6d2484fe0caa4cf71aff51e490d21481f1abe5` |

---

## Red / C2

| Indicador | Detalle |
|---|---|
| `soft8[.]gddos[.]com` | C2 (puerto 25) |
| `baidu[.]gddos[.]com` | C2 (puerto 25) |
| `pcdown[.]gddos[.]com` | descarga de config |
| `103[.]233[.]83[.]245` | C2 por IP (puerto 25) |
| `hxxp://pcdown[.]gddos[.]com:8080/cfg[.]rar` | URL de configuración |
| `soft8.gddos.com:25\|103.233.83.245:25\|baidu.gddos.com:25` | lista C2 cruda |
| `8[.]8[.]8[.]8`, `8[.]8[.]4[.]4` | resolvers DNS hardcodeados |

**User-Agent:** `Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.2; SV1; TencentTraveler ; .NET CLR 1.1.4322)`
**Cabecera:** `Accept-Language: zh-cn` (origen chino)
**Protocolo de comandos:** campos `info=`, `denyip=`, `filename=`, `rmfile=`, `md5=`; plantillas `%u:%s|`, `%d--%s_%d:%s|`.
**Recon de sistema:** `/proc/net/tcp`, `/proc/meminfo`, `/proc/cpuinfo`, `/proc/stat`.

> Corroborado en el `strace`: `connect()` a `103.233.83.245:25` y DNS de
> `soft8.gddos.com`/`baidu.gddos.com` a `8.8.8.8`/`8.8.4.4` — todos `ENETUNREACH`
> por el aislamiento de la VM (no hubo fuga).

## Persistencia

| Mecanismo | Valor |
|---|---|
| Cron (cada 3 min, root) | `*/3 * * * * root /etc/cron.hourly/gcc.sh` |
| Inyección a crontab | `sed -i '/\/etc\/cron.hourly\/gcc.sh/d' /etc/crontab && echo '*/3 * * * * root /etc/cron.hourly/gcc.sh' >> /etc/crontab` |
| Script dropeado | `/etc/cron.hourly/gcc.sh` |
| Init scripts | `/etc/init.d/witpunnhsu`, `/etc/rc%d.d/S90%s`, `/etc/rc.d/rc%d.d/S90%s` |
| Registro de servicio | `chkconfig --add`, `update-rc.d defaults` |
| PID file | `/var/run/gcc.pid` |

## Archivos / artefactos en disco

| Ruta | Rol |
|---|---|
| `/tmp/witpunnhsu` | copia ejecutada (nombre aleatorio por corrida) |
| `/tmp/uxoldbzmwi`, `/bin/uxoldbzmwi`, `/usr/bin/uxoldbzmwi` | rutas alternativas de auto-copia |
| `/lib/libudev.so` -> `/lib/libudev.so.6` | firma XorDDoS (se hace pasar por libudev) |
| `/proc/rs_dev` | dispositivo del rootkit LKM |

## Evasión / anti-forense

- `HISTFILE=/dev/null`, `MYSQL_HISTFILE=/dev/null` (borra historial de shell).
- Rootkit por módulo de kernel: `insmod` / `remove` / `/proc/rs_dev`.
- Lista de nombres-señuelo con que se disfraza el proceso: `bash`, `su`, `ps -ef`,
  `ls`, `ls -la`, `top`, `netstat -an`, `netstat -antop`, `grep "A"`, `sleep 1`,
  `cd /etc`, `ifconfig eth0`, `ifconfig`, `route -n`, `gnome-terminal`, `id`, `who`,
  `whoami`, `pwd`, `uptime`.
- Shell embebida que levanta interfaces antes de actuar:
  ```sh
  #!/bin/sh
  PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:/usr/X11R6/bin
  for i in `cat /proc/net/dev|grep :|awk -F: {'print $1'}`; do ifconfig $i up& done
  cp /lib/libudev.so /lib/libudev.so.6
  ```

## Datos del volcado (radare)

- Core x86-32, 12 mapeos; `static true`, `stripped true`, `canary false`, `nx false`.
- Registros al volcar: `eip = 0x08067740` (dentro del `.text` desempacado, base `0x8048000`).
- *(El disasm `@ rip` falló porque en un core de 32-bit el registro es `eip`; detalle de la herramienta, el core es válido.)*

## MITRE ATT&CK (12 técnicas)

| ID | Técnica | Táctica |
|---|---|---|
| T1071 / T1071.004 | Application Layer Protocol / DNS | Command and Control |
| T1027.002 | Software Packing | Defense Evasion |
| T1055 | Process Injection (RWX) | Defense Evasion |
| T1070.004 | Indicator Removal: File Deletion | Defense Evasion |
| T1059.004 | Unix Shell | Execution |
| T1053.003 | Scheduled Task: Cron | Persistence |
| T1543.002 | Create/Modify System Process: systemd/init | Persistence |
| T1547.001 | Boot/Logon Autostart: rc/init | Persistence |
| T1057 | Process Discovery | Discovery |
| T1082 | System Information Discovery | Discovery |
| T1083 | File and Directory Discovery | Discovery |
