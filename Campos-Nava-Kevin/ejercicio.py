import os
import subprocess

os.system("date")

resultado = subprocess.run(["date"], capture_output=True, text=True)

print(f"Salida: {resultado.stdout}")
print(f"Errores: {resultado.stderr}")
print(f"Código de salida: {resultado.returncode}")