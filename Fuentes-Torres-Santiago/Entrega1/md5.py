import sys
import hashlib
'por libreria'
texto = " ".join(sys.argv[1:])
print(hashlib.md5(texto.encode()).hexdigest())