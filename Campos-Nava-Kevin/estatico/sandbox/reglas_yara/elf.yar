/*
 * Formato ELF y características del binario.
 */

rule ELF_Ejecutable
{
    meta:
        descripcion = "Binario ELF (formato ejecutable de Linux)"
    condition:
        uint32(0) == 0x464c457f
}

rule ELF_64bit
{
    meta:
        descripcion = "ELF de 64 bits"
    condition:
        uint32(0) == 0x464c457f and uint8(4) == 2
}

rule ELF_32bit
{
    meta:
        descripcion = "ELF de 32 bits"
    condition:
        uint32(0) == 0x464c457f and uint8(4) == 1
}

rule ELF_Estatico
{
    meta:
        descripcion = "Binario enlazado estaticamente (sin libc dinamica) - comun en botnets"
    strings:
        $interp = "/lib/ld-linux"
        $glibc  = "GLIBC"
    condition:
        uint32(0) == 0x464c457f and none of them
}

rule ELF_Sin_Secciones
{
    meta:
        descripcion = "ELF con tabla de secciones eliminada (anti-analisis)"
    condition:
        uint32(0) == 0x464c457f and uint16(0x3c) == 0
}
