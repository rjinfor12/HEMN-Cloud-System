import os
import ctypes.wintypes

CSIDL_DESKTOP = 0
buf = ctypes.create_unicode_buffer(ctypes.wintypes.MAX_PATH)
ctypes.windll.shell32.SHGetSpecialFolderPathW(None, buf, CSIDL_DESKTOP, False)
desktop = buf.value

files = [
    "Propaganda_HEMN_Mobile.webp",
    "Propaganda_HEMN_Computador.webp",
    "Propaganda_HEMN_Mobile.mp4",
    "Propaganda_HEMN_Computador.mp4"
]

print(f"Desktop path: {desktop}")
for f in files:
    path = os.path.join(desktop, f)
    if os.path.exists(path):
        size = os.path.getsize(path)
        print(f"File: {f}, Size: {size} bytes")
    else:
        print(f"File: {f} NOT FOUND")
