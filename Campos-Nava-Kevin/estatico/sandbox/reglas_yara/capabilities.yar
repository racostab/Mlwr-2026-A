/*
 * Capacidades y comportamiento: ejecución, persistencia, privilegios.
 */

rule Cap_Shell_Embebida
{
    meta:
        descripcion = "Referencias a shells o ejecucion de comandos"
    strings:
        $sh   = "/bin/sh"
        $bash = "/bin/bash"
        $sys  = "system"
        $exec = "execve"
        $popen = "popen"
    condition:
        2 of them
}

rule Cap_Persistencia
{
    meta:
        descripcion = "Mecanismos de persistencia (cron, rc, systemd)"
    strings:
        $a = "/etc/rc.local"
        $b = "/etc/crontab"
        $c = "/etc/cron."
        $d = "/etc/init.d/"
        $e = "systemctl"
        $f = ".service"
        $g = "/etc/rc.d/"
    condition:
        2 of them
}

rule Cap_Privilegios
{
    meta:
        descripcion = "Escalada o manejo de privilegios"
    strings:
        $a = "setuid"
        $b = "setgid"
        $c = "/etc/passwd"
        $d = "/etc/shadow"
        $e = "sudoers"
    condition:
        2 of them
}

rule Cap_Autoarranque_Proc
{
    meta:
        descripcion = "Manipula procesos / se oculta"
    strings:
        $a = "prctl"
        $b = "PR_SET_NAME"
        $c = "setsid"
        $d = "daemon"
        $e = "fork"
    condition:
        3 of them
}

rule Cap_Keylogger_Input
{
    meta:
        descripcion = "Acceso a dispositivos de entrada (posible keylogger)"
    strings:
        $a = "/dev/input/event"
        $b = "EVIOCGNAME"
        $c = "/dev/input/mice"
    condition:
        any of them
}
