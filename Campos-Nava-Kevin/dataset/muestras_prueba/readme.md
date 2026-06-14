# dataset/muestras_prueba/ — Muestras señuelo BENIGNAS

Binarios ELF de **prueba** para ejercitar el pipeline del laboratorio sin riesgo.
Por fuera parecen botnets (cadenas de C2, comandos DDoS/IRC, firmas Mirai/Gafgyt
→ disparan `strings` y YARA), pero por dentro **no hacen nada peligroso**. Sirven
para validar cada parte del flujo *antes* de detonar malware real.

> **No son malware.** Ninguno descarga, ejecuta, persiste ni exfiltra. El de red
> solo *intenta* conectar (debe ser bloqueado) y reporta.

## Compilar

```bash
bash dataset/muestras_prueba/compilar.sh   # compila los tres e imprime sus sha256
```

## Las muestras y qué valida cada una

| Binario            | Qué hace al correr                                   | Qué parte del lab valida |
|--------------------|------------------------------------------------------|--------------------------|
| `senuelo_botnet`   | Imprime banner y duerme. Cero syscalls peligrosas.   | Flujo completo inerte; estático (`strings`/YARA sobre el binario). |
| `senuelo_red`      | Intenta `connect()` a IPs de prueba + DNS `.invalid`. NO envía datos. | **Aislamiento** (jaula cerrada) + **captura de red** (pcap/strace). |
| `senuelo_memoria`  | "Desempaca" sus IOCs al **heap** y duerme.           | **Volcado de memoria**: los IOCs salen en el dump (no solo en estático). |

### Notas de interpretación

- **`senuelo_red`** debe terminar con `0 fuga(s)` y todos los intentos
  `bloqueado/inalcanzable`. Si algo **CONECTA** (sobre todo `8.8.8.8:53`), el
  aislamiento está roto: revisa `red.py` / `firewall.py` / `verificacion.py`.
- **`senuelo_memoria`** resuelve el punto ciego de `senuelo_botnet`: el `.rodata`
  (solo lectura, respaldado por archivo) lo excluye el `coredump_filter` por
  defecto; el heap (memoria anónima) sí entra al core. Por eso aquí los IOCs sí
  aparecen en el volcado. Busca el marcador `INICIO_CONFIG_C2_SENUELO` en el dump.
- Las técnicas MITRE **T1055** (`mprotect`) y **T1057** (`readlinkat /proc/self/exe`)
  que pueden salir son **falsos positivos** del arranque de glibc, no de estos
  binarios.
