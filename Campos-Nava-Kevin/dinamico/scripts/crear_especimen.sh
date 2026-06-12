#!/bin/bash
# Genera un ESPÉCIMEN DE PRUEBA BENIGNO (ELF) para validar el pipeline dinámico
# de extremo a extremo SIN detonar malware real.
#
# A diferencia del canario bash (/tmp/canario_aislamiento.sh, que solo prueba
# egress y termina enseguida), este espécimen ejercita las tres cosas que el lab
# necesita observar:
#
#   1. OFUSCACIÓN: lleva su "config C2" cifrada con XOR. En el binario en disco
#      `strings` NO revela la IP ni el dominio del C2; se desofusca en runtime y
#      se mantiene viva en el heap → aparece EN CLARO en el volcado de memoria
#      (procdump/gcore) y la cazan strings/yara del post-análisis. Es justo el
#      caso "empacado en disco, en claro en memoria" que motiva post_analisis.py.
#   2. LLAMADA A CASA: intenta connect() al C2 falso y a DNS públicos reales. En
#      la VM aislada TODO debe fallar; se ve en strace (connect → ENETUNREACH) y
#      en tu tcpdump del host (no sale tráfico de la VM hacia internet).
#   3. VIDA LARGA: late en bucle (sleep) sosteniendo la config desofuscada en
#      memoria hasta que el runner lo mata tras el volcado (así el dump siempre
#      cae con el proceso vivo, sea cual sea el tiempo de detonación).
#
# Todas las IP/dominios "C2" usan rangos de DOCUMENTACIÓN (RFC 5737, TLD .test):
# no enrutan ni resuelven a ningún sistema real. El binario no borra, cifra,
# persiste ni daña nada: solo imprime, intenta conexiones (que fallan) y duerme.
#
# Uso:  bash dinamico/scripts/crear_especimen.sh
set -e

SRC=/tmp/especimen_benigno.c
BIN=/tmp/especimen_benigno
TPL="$(mktemp)"
trap 'rm -f "$TPL"' EXIT

# Secretos benignos que irán OFUSCADOS dentro del binario (rangos reservados).
MARKER="ESPECIMEN-BENIGNO-DESOFUSCADO-EN-MEMORIA"
C2_IP="203.0.113.66"               # RFC 5737 TEST-NET-3: no enruta
C2_DOM="c2.canario-benigno.test"   # TLD .test reservado: nunca resuelve
C2_CMD="BEACON|id=canario|cmd=noop"

# ---------------------------------------------------------------------------
# 1. Plantilla C con la config como placeholders (@MARKER@, @IP@, @DOM@, @CMD@);
#    python los sustituye por los bytes XOR. Así el .c (y el binario) contienen
#    SOLO bytes cifrados: el texto en claro nunca toca el disco.
# ---------------------------------------------------------------------------
cat > "$TPL" <<'EOF'
/*
 * especimen_benigno.c — MUESTRA DE PRUEBA BENIGNA para el análisis dinámico.
 * Generado por dinamico/scripts/crear_especimen.sh. NO es malware.
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <netdb.h>
#include <errno.h>

/* Config "C2" cifrada con XOR: en disco solo viven estos bytes (C2 oculto). */
static const unsigned char KEY = 0x5a;
static const unsigned char cfg_marker[] = { /*@MARKER@*/ };
static const unsigned char cfg_c2_ip[]  = { /*@IP@*/ };
static const unsigned char cfg_c2_dom[] = { /*@DOM@*/ };
static const unsigned char cfg_c2_cmd[] = { /*@CMD@*/ };

/* xor_decrypt / decode_config: nombres reconocibles a propósito para que la
 * regla YARA Ofuscacion_XOR_Brute también dispare sobre el binario. */
static char *xor_decrypt(const unsigned char *src, size_t n) {
    char *out = malloc(n + 1);
    if (!out) return NULL;
    for (size_t i = 0; i < n; i++)
        out[i] = (char)(src[i] ^ KEY);
    out[n] = '\0';
    return out;                 /* se conserva a propósito: persiste en el heap */
}

struct config { char *marker, *ip, *dom, *cmd; };

static struct config decode_config(void) {
    struct config c;
    c.marker = xor_decrypt(cfg_marker, sizeof cfg_marker);
    c.ip     = xor_decrypt(cfg_c2_ip,  sizeof cfg_c2_ip);
    c.dom    = xor_decrypt(cfg_c2_dom, sizeof cfg_c2_dom);
    c.cmd    = xor_decrypt(cfg_c2_cmd, sizeof cfg_c2_cmd);
    return c;
}

/* connect() acotado por timeout. Devuelve 0 si CONECTÓ (sería fuga), <0 si no. */
static int intentar_tcp(const char *ip, int puerto) {
    int s = socket(AF_INET, SOCK_STREAM, 0);
    if (s < 0) return -1;
    struct timeval tv = { 3, 0 };
    setsockopt(s, SOL_SOCKET, SO_SNDTIMEO, &tv, sizeof tv);
    setsockopt(s, SOL_SOCKET, SO_RCVTIMEO, &tv, sizeof tv);
    struct sockaddr_in a;
    memset(&a, 0, sizeof a);
    a.sin_family = AF_INET;
    a.sin_port   = htons(puerto);
    inet_pton(AF_INET, ip, &a.sin_addr);
    int r = connect(s, (struct sockaddr *)&a, sizeof a);
    close(s);
    return r;
}

static void probar_egress(const char *etiqueta, const char *ip, int puerto) {
    if (intentar_tcp(ip, puerto) == 0)
        printf("[especimen] CONECTO %s (%s:%d)  <-- FUGA\n", etiqueta, ip, puerto);
    else
        printf("[especimen] bloqueado %s (%s:%d): %s  (ok)\n",
               etiqueta, ip, puerto, strerror(errno));
    fflush(stdout);
}

static void probar_dns(const char *dom) {
    struct addrinfo *res = NULL;
    int r = getaddrinfo(dom, "443", NULL, &res);
    if (r == 0) {
        printf("[especimen] DNS resolvio %s  <-- FUGA\n", dom);
        freeaddrinfo(res);
    } else {
        printf("[especimen] DNS bloqueado %s: %s  (ok)\n", dom, gai_strerror(r));
    }
    fflush(stdout);
}

int main(void) {
    setvbuf(stdout, NULL, _IONBF, 0);
    puts("[especimen] MUESTRA DE PRUEBA BENIGNA — no hace nada dañino.");

    /* 1) Desofuscar la config: desde aquí el C2 vive EN CLARO en el heap. */
    struct config c = decode_config();
    printf("[especimen] config desofuscada en memoria:\n");
    printf("            marker = %s\n", c.marker);
    printf("            c2_ip  = %s\n", c.ip);
    printf("            c2_dom = %s\n", c.dom);
    printf("            c2_cmd = %s\n", c.cmd);

    /* 2) Llamar a casa: al C2 falso y a DNS públicos reales. En la VM aislada
     *    TODO debe fallar (lo confirman strace + tu tcpdump). */
    puts("[especimen] intentando salir a la red (todo deberia fallar)...");
    probar_egress("C2 falso", c.ip, 443);
    probar_egress("DNS Cloudflare", "1.1.1.1", 53);
    probar_egress("HTTPS Google", "8.8.8.8", 443);
    probar_dns(c.dom);
    probar_dns("example.com");

    /* 3) Latir sosteniendo la config desofuscada viva hasta que el runner nos
     *    mate tras el volcado (toca la config para que -O0 no la descarte). */
    puts("[especimen] entrando en bucle de beacon; sosteniendo config en memoria.");
    for (unsigned long i = 1; ; i++) {
        printf("[especimen] beacon #%lu (marker=%s)\n", i, c.marker);
        sleep(5);
    }
    return 0;   /* inalcanzable: lo termina el runner */
}
EOF

# ---------------------------------------------------------------------------
# 2. Sustituir placeholders por los bytes XOR (texto_plano ^ KEY).
# ---------------------------------------------------------------------------
KEY=0x5a MARKER="$MARKER" C2_IP="$C2_IP" C2_DOM="$C2_DOM" C2_CMD="$C2_CMD" \
python3 - "$TPL" "$SRC" <<'PY'
import os, sys
tpl, out = sys.argv[1], sys.argv[2]
key = int(os.environ["KEY"], 16)
def enc(s):
    return ", ".join("0x%02x" % (b ^ key) for b in s.encode())
repl = {
    "/*@MARKER@*/": enc(os.environ["MARKER"]),
    "/*@IP@*/":     enc(os.environ["C2_IP"]),
    "/*@DOM@*/":    enc(os.environ["C2_DOM"]),
    "/*@CMD@*/":    enc(os.environ["C2_CMD"]),
}
txt = open(tpl).read()
for k, v in repl.items():
    txt = txt.replace(k, v)
open(out, "w").write(txt)
PY

# ---------------------------------------------------------------------------
# 3. Compilar estático (corre en la VM sin depender de su libc) y SIN strip
#    (deja símbolos: la regla Ofuscacion_XOR_Brute caza decode_config/xor_decrypt).
# ---------------------------------------------------------------------------
gcc -static -O0 -o "$BIN" "$SRC"
chmod +x "$BIN"
echo "[+] Compilado: $BIN ($(file -b "$BIN" | cut -d, -f1,2))"

# ---------------------------------------------------------------------------
# 4. Probar la ofuscación: el C2 NO debe verse en disco, pero el marker SÍ
#    aparecerá en el volcado de memoria una vez detonado.
# ---------------------------------------------------------------------------
if strings -a "$BIN" | grep -qF "$C2_IP"; then
    echo "[!] FALLO: el C2 ($C2_IP) es visible en disco con strings (no se ofuscó)."
    exit 1
fi
echo "[+] ok: el C2 ($C2_IP) NO aparece en 'strings' del binario (config ofuscada)."

cat <<FIN

==================================================================
 Espécimen benigno listo.
==================================================================
 Detónalo de extremo a extremo (deja 25 s para que el dump caiga
 con el proceso vivo; el runner lo mata después):

     python3 dinamico/analizador/analizador_dinamico.py $BIN 25

 Qué revisar en dynamic_output/<ts>/ :
   - stdout.log    → ningún "<-- FUGA"; todos los egress "bloqueado (ok)".
   - strace.log    → los connect() a $C2_IP / 1.1.1.1 / 8.8.8.8 fallan
                     (ENETUNREACH/ETIMEDOUT/ECONNREFUSED).
   - el volcado    → 'strings <dump> | grep $MARKER' SÍ aparece, y también
                     $C2_IP y $C2_DOM: prueba de que el C2 ofuscado en disco
                     quedó EN CLARO en memoria.
   - post_analisis.json → yara/strings del motor sobre el volcado.

 Mientras corre, en el HOST puedes capturar SOLO el tráfico de la VM
 (sustituye vboxnet0 por tu interfaz host-only) para confirmar que no
 sale nada hacia internet:

     sudo tcpdump -ni vboxnet0 'not arp and not (src net 192.168.56.0/24 and dst net 192.168.56.0/24)'
==================================================================
FIN
