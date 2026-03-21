import os
import sys

# Forçar UTF-8 no print
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

import ctypes.wintypes

CSIDL_DESKTOP = 0
buf = ctypes.create_unicode_buffer(ctypes.wintypes.MAX_PATH)
ctypes.windll.shell32.SHGetSpecialFolderPathW(None, buf, CSIDL_DESKTOP, False)
desktop = buf.value

print(f"DEBUG: Desktop path is: {desktop}")

def check_file(filename):
    path = os.path.join(desktop, filename)
    if os.path.exists(path):
        size = os.path.getsize(path)
        print(f"FOUND: {filename} ({size} bytes)")
        return True
    else:
        print(f"NOT FOUND: {filename}")
        return False

# Listar arquivos que começam com 'Propaganda' para ver o que tem lá
print("Listing 'Propaganda' files on Desktop:")
try:
    for f in os.listdir(desktop):
        if f.startswith("Propaganda"):
            size = os.path.getsize(os.path.join(desktop, f))
            print(f" - {f} ({size} bytes)")
except Exception as e:
    print(f"Error listing directory: {e}")

check_file("Propaganda_HEMN_Mobile.webp")
check_file("Propaganda_HEMN_Computador.webp")
check_file("Propaganda_HEMN_Mobile.mp4")
check_file("Propaganda_HEMN_Computador.mp4")
