/*
 * Criptografía y ransomware.
 */

rule Cripto_Strings
{
    meta:
        descripcion = "Referencias a primitivas criptograficas"
    strings:
        $a = "AES"
        $b = "RC4"
        $c = "XTEA"
        $d = "ChaCha20"
        $e = "RSA"
        $f = "base64"
    condition:
        2 of them
}

rule Ransom_Nota
{
    meta:
        descripcion = "Cadenas tipicas de nota de rescate"
    strings:
        $a = "your files have been encrypted" nocase
        $b = "bitcoin" nocase
        $c = "decrypt" nocase
        $d = "ransom" nocase
        $e = ".onion"
    condition:
        2 of them
}

rule Ransom_Extensiones
{
    meta:
        descripcion = "Recorre el sistema de archivos para cifrar"
    strings:
        $a = "readdir"
        $b = "opendir"
        $c = ".encrypted"
        $d = ".locked"
        $e = "rename"
    condition:
        3 of them
}

rule Minero_Cripto
{
    meta:
        descripcion = "Indicios de criptominero"
    strings:
        $a = "stratum+tcp"
        $b = "xmrig" nocase
        $c = "minerd"
        $d = "cryptonight" nocase
        $e = "pool."
    condition:
        any of them
}
