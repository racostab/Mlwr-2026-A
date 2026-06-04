
import requests
import time
import os

API_URL = "http://localhost:5000"

def flujo_analisis_malware(archivo_malware):
    print("[1] Iniciando VM Kali...")
    requests.post(f"{API_URL}/vm/start")
    time.sleep(30)  # Esperar boot
    
    print("[2] Levantando contenedores de análisis...")
    requests.post(f"{API_URL}/docker/up")
    time.sleep(5)
    
    print("[3] Copiando muestra a contenedor...")
    nombre_archivo = os.path.basename(archivo_malware)
    # Aquí usarías SCP o paramiko para copiar el archivo
    
    print("[4] Ejecutando análisis estático...")
    respuesta = requests.post(f"{API_URL}/docker/exec", json={
        "contenedor": "malware_analisis_estatico",
        "comando": f"python3 /scripts/analisis_estatico.py /analisis/{nombre_archivo}"
    })
    
    print("[5] Resultados:", respuesta.json())
    
    print("[6] Limpiando...")
    requests.post(f"{API_URL}/docker/down")
    requests.post(f"{API_URL}/vm/stop")

if __name__ == "__main__":
    flujo_analisis_malware("muestra_sospechosa.exe")