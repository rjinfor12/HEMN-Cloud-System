import shutil
import os

src = r"C:\Users\Junior T.I\.gemini\antigravity\brain\64d3ce78-534d-446b-ac79-7139022da910\tmm_crest_true_transparency_1771729611468.png"
dst = r"C:\Users\Junior T.I\.gemini\antigravity\scratch\data_analysis\logo.png"

if os.path.exists(src):
    shutil.copy2(src, dst)
    print("Brazão Ultra-Limpo (Transparência Real) atualizado.")
else:
    print("Erro: Logotipo novo não encontrado.")
