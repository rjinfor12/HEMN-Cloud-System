import os
import ctypes.wintypes

CSIDL_DESKTOP = 0
buf = ctypes.create_unicode_buffer(ctypes.wintypes.MAX_PATH)
ctypes.windll.shell32.SHGetSpecialFolderPathW(None, buf, CSIDL_DESKTOP, False)

print(f"Desktop: {buf.value}")
