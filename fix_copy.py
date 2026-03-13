import shutil
import os

src = r"C:\Users\Junior T.I\.gemini\antigravity\scratch\data_analysis\main_gui.py"
dst = r"C:\Users\Junior T.I\scratch\data_analysis\main_gui.py"

if os.path.exists(src):
    shutil.copy2(src, dst)
    print(f"Interface corrigida copiada para {dst}")
else:
    print("Erro: Fonte não encontrada.")
