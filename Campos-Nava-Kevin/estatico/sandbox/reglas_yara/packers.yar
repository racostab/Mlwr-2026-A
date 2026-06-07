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
