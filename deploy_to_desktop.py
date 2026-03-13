import shutil
import os

src = r"C:\Users\Junior T.I\.gemini\antigravity\scratch\data_analysis\dist\HEMN SYSTEM.exe"
dst = r"C:\Users\Junior T.I\OneDrive\Área de Trabalho\HEMN SYSTEM.exe"

try:
    if os.path.exists(dst):
        os.remove(dst)
    shutil.copy2(src, dst)
    print(f"Sucesso: {src} copiado para {dst}")
except Exception as e:
    print(f"Erro ao copiar: {e}")
