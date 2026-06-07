/*
 * Indicadores de red y command-and-control (C2).
 */

rule Red_Sockets
{
    meta:
        descripcion = "Uso de sockets de red"
    strings:
        $sock = "socket"
        $conn = "connect"
        $send = "sendto"
        $recv = "recvfrom"
    condition:
        2 of them
}

rule Red_HTTP_Cliente
{
    meta:
        descripcion = "Descarga por HTTP (posible dropper)"
    strings:
        $http = "http://"
        $host = "Host:"
        $get  = "GET /"
        $ua   = "User-Agent:"
        $wget = "wget"
        $curl = "curl"
    condition:
        2 of them
}

rule Red_IRC_C2
{
    meta:
        descripcion = "Canal de control por IRC"
    strings:
        $a = "PRIVMSG"
        $b = "JOIN "
        $c = "USER "
        $d = "NICK "
    condition:
        2 of them
}

rule Red_DNS_Dinamico
{
    meta:
        descripcion = "Dominios de DNS dinamico (C2 barato)"
    strings:
        $a = ".no-ip."
        $b = ".ddns.net"
        $c = ".duckdns.org"
        $d = ".dyndns."
    condition:
        any of them
}

rule Red_Descarga_Shell
{
    meta:
        descripcion = "Cadena tipica de descarga+ejecucion"
    strings:
        $a = "chmod +x"
        $b = "tftp"
        $c = "wget http"
        $d = "/tmp/"
    condition:
        2 of them
}
