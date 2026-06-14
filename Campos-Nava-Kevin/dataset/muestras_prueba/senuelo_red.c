/*
 * senuelo_red.c — SEÑUELO BENIGNO DE RED (NO ES MALWARE)
 * ======================================================
 *
 * Sirve para VALIDAR EL AISLAMIENTO y la captura de red ANTES de detonar
 * malware real. A diferencia de `senuelo_botnet` (que no tocaba la red), este
 * *intenta activamente* salir a internet hacia destinos de PRUEBA.
 *
 * Es inofensivo: solo abre sockets e intenta `connect()`. NO envia datos, NO
 * descarga nada, NO ejecuta nada. Si una conexion llegara a establecerse, solo
 * imprime "FUGA" y cierra el socket.
 *
 * Resultado esperado en una jaula bien hecha: TODOS los intentos fallan
 * (bloqueado/inalcanzable) y el codigo de salida es 0. Si alguno CONECTA, hay
 * fuga: revisa NAT/host-only/firewall (red.py + firewall.py + verificacion.py).
 *
 * En strace veras socket()/connect() y, en el pcap del host, los SYN que el
 * firewall debe descartar. Eso prueba a la vez el aislamiento y la captura.
 *
 * Uso:  ./senuelo_red [rondas]      (def: 5)
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <errno.h>
#include <fcntl.h>
#include <time.h>
#include <sys/socket.h>
#include <sys/select.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <netdb.h>

/*
 * Destinos de PRUEBA. Los dos primeros son rangos de documentacion (RFC 5737):
 * no son hosts reales, asi que no "molestan" a nadie. El tercero (8.8.8.8) es
 * un servicio real y publico: si la VM logra alcanzarlo, el aislamiento esta
 * ROTO de verdad (hay salida a internet).
 */
struct objetivo { const char *ip; int puerto; const char *desc; };
static const struct objetivo OBJETIVOS[] = {
    {"203.0.113.5", 1337, "C2 falso (TEST-NET-3, RFC 5737)"},
    {"192.0.2.66",    80, "panel HTTP falso (TEST-NET-1, RFC 5737)"},
    {"8.8.8.8",       53, "DNS publico real (prueba de fuga real)"},
};
#define N_OBJ (sizeof(OBJETIVOS) / sizeof(OBJETIVOS[0]))

/* connect() no bloqueante con timeout. Devuelve 0 si conecto, -1 si no. */
static int intentar(const char *ip, int puerto, int timeout_s)
{
    int fd = socket(AF_INET, SOCK_STREAM, 0);
    if (fd < 0)
        return -1;
    fcntl(fd, F_SETFL, O_NONBLOCK);

    struct sockaddr_in sa;
    memset(&sa, 0, sizeof sa);
    sa.sin_family = AF_INET;
    sa.sin_port = htons(puerto);
    inet_pton(AF_INET, ip, &sa.sin_addr);

    int r = connect(fd, (struct sockaddr *)&sa, sizeof sa);
    if (r == 0) { close(fd); return 0; }                 /* conecto de inmediato */
    if (errno != EINPROGRESS) { close(fd); return -1; }  /* error inmediato => no */

    fd_set w;
    FD_ZERO(&w);
    FD_SET(fd, &w);
    struct timeval tv = { timeout_s, 0 };
    r = select(fd + 1, NULL, &w, NULL, &tv);
    if (r <= 0) { close(fd); return -1; }                /* timeout/err => bloqueado */

    int err = 0;
    socklen_t l = sizeof err;
    getsockopt(fd, SOL_SOCKET, SO_ERROR, &err, &l);
    close(fd);
    return err == 0 ? 0 : -1;
}

int main(int argc, char **argv)
{
    int rondas = (argc > 1) ? atoi(argv[1]) : 5;
    if (rondas <= 0)
        rondas = 5;

    printf("=== SENUELO DE RED (benigno) ===\n");
    printf("Intenta conectar a destinos de PRUEBA que DEBEN estar bloqueados.\n");
    printf("Si TODOS fallan => la jaula aisla bien. Si alguno conecta => FUGA.\n\n");
    fflush(stdout);

    int fugas = 0;
    for (int ronda = 1; ronda <= rondas; ronda++) {
        for (size_t i = 0; i < N_OBJ; i++) {
            int ok = intentar(OBJETIVOS[i].ip, OBJETIVOS[i].puerto, 2);
            printf("[ronda %d] %s:%d (%s) -> %s\n", ronda,
                   OBJETIVOS[i].ip, OBJETIVOS[i].puerto, OBJETIVOS[i].desc,
                   ok == 0 ? "*** CONECTO (FUGA!) ***"
                           : "bloqueado/inalcanzable (ok)");
            if (ok == 0)
                fugas++;
            fflush(stdout);
        }
        struct timespec s = {1, 0};
        nanosleep(&s, NULL);
    }

    /* Resolucion DNS que en la jaula deberia fallar (sin resolutor / sin salida). */
    struct addrinfo *res = NULL;
    int g = getaddrinfo("c2.senuelo-lab.invalid", "80", NULL, &res);
    printf("\nDNS c2.senuelo-lab.invalid -> %s\n",
           g == 0 ? "*** RESOLVIO (revisar) ***" : "no resolvio (ok)");
    if (res)
        freeaddrinfo(res);

    printf("\n=== Resumen: %d fuga(s). %s ===\n", fugas,
           fugas == 0 ? "Jaula CERRADA, captura OK." : "REVISA EL AISLAMIENTO.");
    return fugas == 0 ? 0 : 1;
}
