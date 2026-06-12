/*
 * Deteccion de empaquetado/ofuscacion por ENTROPIA.
 *
 * Un binario empacado o cifrado tiene los datos casi aleatorios → entropia alta
 * (cercana a 8 bits/byte). Es la senal mas robusta de packing aunque el packer
 * borre sus firmas ASCII.
 *
 * Usa el modulo `math` de YARA. Va en SU PROPIO archivo a proposito: el sandbox
 * escanea `/rules/*.yar` archivo por archivo con `2>/dev/null`, asi que si este
 * build de YARA no trae el modulo `math`, solo se pierde ESTE archivo y las
 * demas reglas siguen funcionando.
 */
import "math"

rule Empaquetado_Entropia_Alta
{
    meta:
        descripcion = "Entropia global muy alta (>7.2): el binario esta empacado o cifrado"
    condition:
        math.entropy(0, filesize) >= 7.2
}

rule Empaquetado_Entropia_ELF
{
    meta:
        descripcion = "ELF con entropia alta (>7.0): ELF empacado/cifrado"
    strings:
        $elf = { 7F 45 4C 46 }
    condition:
        $elf at 0 and math.entropy(0, filesize) >= 7.0
}
