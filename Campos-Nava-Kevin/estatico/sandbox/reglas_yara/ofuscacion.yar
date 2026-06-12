/*
 * Ofuscacion: cadenas cifradas, carga dinamica de codigo, resolucion de
 * simbolos en runtime y auto-modificacion. Pistas de que el binario esconde su
 * comportamiento real (frecuente en botnets ELF empacados/ofuscados).
 *
 * Reglas basadas en cadenas (sin modulos): compilan en cualquier build de YARA.
 */

rule Ofuscacion_Carga_Dinamica
{
    meta:
        descripcion = "Resuelve/carga codigo en runtime (dlopen/dlsym/dlmopen)"
    strings:
        $a = "dlopen"
        $b = "dlsym"
        $c = "dlmopen"
        $d = "RTLD_NOW"
        $e = "RTLD_LAZY"
    condition:
        2 of them
}

rule Ofuscacion_Codigo_En_Memoria
{
    meta:
        descripcion = "Escribe y ejecuta codigo en memoria (RWX): desempaque/inyeccion"
    strings:
        $a = "mprotect"
        $b = "mmap"
        $c = "PROT_EXEC"
        $d = "PROT_WRITE"
        $e = "memfd_create"
    condition:
        3 of them
}

rule Ofuscacion_Ejecucion_Sin_Fichero
{
    meta:
        descripcion = "Ejecucion fileless: memfd_create + execveat sobre /proc/self/fd"
    strings:
        $a = "memfd_create"
        $b = "execveat"
        $c = "/proc/self/fd/"
    condition:
        $a and ($b or $c)
}

rule Ofuscacion_Base64_Embebido
{
    meta:
        descripcion = "Indicios de payload/config en Base64 dentro del binario"
    strings:
        // Alfabeto base64 de referencia y rutinas tipicas de (de)codificacion.
        $tbl = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
        $fn1 = "base64"
        $fn2 = "b64decode"
    condition:
        $tbl or any of ($fn*)
}

rule Ofuscacion_XOR_Brute
{
    meta:
        descripcion = "Cadenas tipicas ofuscadas con XOR: 'xor', tablas de decodificacion"
    strings:
        $a = "xor_decrypt"
        $b = "decrypt_string"
        $c = "deobfuscate"
        $d = "decode_config"
    condition:
        any of them
}

rule Ofuscacion_Cifrado_Embebido
{
    meta:
        descripcion = "Rutinas de cifrado simetrico embebidas (ocultar C2/config)"
    strings:
        $a = "AES" nocase
        $b = "RC4" nocase
        $c = "ChaCha20" nocase
        $d = "Salsa20" nocase
        $e = "Blowfish" nocase
    condition:
        any of them
}

rule Ofuscacion_Binario_Stripped_Sospechoso
{
    meta:
        descripcion = "ELF sin seccion de simbolos pero con cargador dinamico (tipico de packers)"
    strings:
        $elf     = { 7F 45 4C 46 }         // \x7FELF
        $interp  = "/lib"
        $dynamic = "memfd_create"
        $symtab  = ".symtab"
    condition:
        $elf at 0 and $dynamic and not $symtab
}
