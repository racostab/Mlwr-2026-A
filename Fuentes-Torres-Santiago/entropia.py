import os
import math
from collections import Counter

def calcular_entropia(datos):
    """Calcula la entropía de un conjunto de datos."""
    frecuencias = Counter(datos)  # Cuenta las ocurrencias de cada carácter
    total_datos = len(datos)  # Longitud total de los datos
    probabilidades = [freq / total_datos for freq in frecuencias.values()]  # Probabilidades de cada carácter
    # Calcula la entropía utilizando la fórmula de Shannon
    entropia = -sum(p * math.log2(p) for p in probabilidades if p > 0)
    return entropia


def listar_archivos_directorio(directorio):
    """Lista los archivos en el directorio especificado."""
    try:
        archivos = [f for f in os.listdir(directorio) if os.path.isfile(os.path.join(directorio, f))]
        return archivos
    except FileNotFoundError:
        print(f"El directorio {directorio} no fue encontrado.")
        return []


def leer_archivo(nombre_archivo):
    """Lee el contenido de un archivo de texto."""
    try:
        with open(nombre_archivo, 'r', encoding='utf-8') as archivo:
            return archivo.read()
    except FileNotFoundError:
        print(f"El archivo {nombre_archivo} no fue encontrado.")
        return None
    except Exception as e:
        print(f"Error al leer el archivo {nombre_archivo}: {e}")
        return None

def seleccionar_archivo(archivos):
    """Permite al usuario seleccionar un archivo de la lista de archivos disponibles."""
    if not archivos:
        print("No hay archivos disponibles para elegir.")
        return None
    print("Selecciona un archivo para analizar:")
    for i, archivo in enumerate(archivos, 1):
        print(f"{i}. {archivo}")
    
    # Solicita al usuario que elija un archivo
    try:
        seleccion = int(input(f"Introduce el número del archivo (1-{len(archivos)}): "))
        if 1 <= seleccion <= len(archivos):
            return archivos[seleccion - 1]
        else:
            print("Selección inválida. Inténtalo de nuevo.")
            return None
    except ValueError:
        print("Entrada no válida. Debes introducir un número.")
        return None

def analizar_entropia_archivo(directorio):
    """Permite seleccionar un archivo y calcular su entropía."""
    archivos = listar_archivos_directorio(directorio)
    archivo_seleccionado = seleccionar_archivo(archivos)

    if archivo_seleccionado:
      
        contenido = leer_archivo(os.path.join(directorio, archivo_seleccionado))
        if contenido:
            entropia = calcular_entropia(contenido)
            print(f"La entropía del archivo '{archivo_seleccionado}' es: {entropia}")
        else:
            print("No se pudo leer el archivo seleccionado.")
    else:
        print("No se seleccionó ningún archivo válido.")

# uso
if __name__ == "__main__":
    # Directorio donde se encuentran los archivos
    directorio = input("Introduce el directorio donde se encuentran los archivos: ")
    analizar_entropia_archivo(directorio)