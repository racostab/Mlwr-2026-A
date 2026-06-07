/*
 * Anti-análisis: anti-debug, anti-VM y evasión.
 */

rule AntiDebug_Ptrace
{
    meta:
        descripcion = "Anti-debug via ptrace(PTRACE_TRACEME)"
    strings:
        $a = "ptrace"
        $b = "PTRACE_TRACEME"
        $c = "TracerPid"
    condition:
        any of them
}

rule AntiAnalisis_Proc
{
    meta:
        descripcion = "Inspecciona /proc para detectar analisis"
    strings:
        $a = "/proc/self/status"
        $b = "/proc/self/maps"
        $c = "/proc/self/cmdline"
    condition:
        any of them
}

rule AntiVM_Strings
{
    meta:
        descripcion = "Cadenas de deteccion de maquina virtual / sandbox"
    strings:
        $a = "VMware" nocase
        $b = "VirtualBox" nocase
        $c = "QEMU" nocase
        $d = "hypervisor" nocase
        $e = "/sys/class/dmi/id/product_name"
    condition:
        any of them
}

rule Evasion_Borra_Huellas
{
    meta:
        descripcion = "Borra logs o su propio binario"
    strings:
        $a = "/var/log/wtmp"
        $b = "/var/log/secure"
        $c = "history -c"
        $d = "unlink"
        $e = "rm -rf"
    condition:
        2 of them
}
