/*
 * Empaquetadores y ofuscadores.
 */

rule UPX_Empaquetado
{
    meta:
        descripcion = "Indicios del empaquetador UPX"
    strings:
        $upx0 = "UPX!"
        $upx1 = "UPX0"
        $upx2 = "UPX1"
        $upx3 = "$Info: This file is packed with the UPX"
    condition:
        any of them
}

rule UPX_Alterado
{
    meta:
        descripcion = "UPX con cabeceras modificadas a mano (evasion)"
    strings:
        $upx_sig = "UPX!"
        $stub    = "PROT_EXEC|PROT_WRITE failed"
    condition:
        $stub and not $upx_sig
}

rule Packer_aPLib
{
    meta:
        descripcion = "Compresion aPLib (usada por algunos packers)"
    strings:
        $ap = "aPLib"
        $a2 = "aP32"
    condition:
        any of them
}

rule Packer_Generico_Strings
{
    meta:
        descripcion = "Cadenas tipicas de runtime de empaquetadores"
    strings:
        $a = "PROT_EXEC"
        $b = "mprotect"
        $c = "memfd_create"
    condition:
        2 of them
}

rule UPX_Magia_Binaria
{
    meta:
        descripcion = "Firma binaria UPX! en el stub (no solo la cadena ASCII)"
    strings:
        $magic = { 55 50 58 21 }           // 'UPX!'
        $l0    = { 55 50 58 30 }           // 'UPX0'
        $l1    = { 55 50 58 31 }           // 'UPX1'
    condition:
        $magic and ($l0 or $l1)
}

rule Packer_MPRESS
{
    meta:
        descripcion = "Empaquetador MPRESS"
    strings:
        $a = "MPRESS" nocase
        $b = ".MPRESS1"
        $c = ".MPRESS2"
    condition:
        any of them
}

rule Packer_gzexe
{
    meta:
        descripcion = "Auto-extraible gzexe (script + binario gzip embebido)"
    strings:
        $sh   = "#!/bin/sh"
        $gz   = "gzip"
        $skip = "tail -n +"
        $lead = "leading garbage"
    condition:
        $sh at 0 and 2 of ($gz, $skip, $lead)
}

rule Packer_Ezuri_Loader
{
    meta:
        descripcion = "Crypter/loader Ezuri (ELF en memoria via memfd, comun en Go/C)"
    strings:
        $a = "memfd_create"
        $b = "/proc/self/fd/"
        $c = "ld-linux"
    condition:
        $a and ($b or $c)
}

rule Packer_Go_Garble
{
    meta:
        descripcion = "Indicios de ofuscacion de binarios Go (garble): runtime Go sin symtab clara"
    strings:
        $go   = "go.buildid"
        $rt   = "runtime.main"
        $garb = "_garble"
    condition:
        $go and ($garb or not $rt)
}
