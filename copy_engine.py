
import os

# Caminho de origem relativo (considerando que estou em C:\Users\Junior T.I\scratch\data_analysis)
# C:\Users\Junior T.I\.gemini\antigravity\scratch\data_analysis
src = os.path.join("..", "..", ".gemini", "antigravity", "scratch", "data_analysis", "data_assets", "prefix_anatel.csv")
dst = os.path.join("data_assets", "prefix_anatel.csv")

if os.path.exists(src):
    try:
        with open(src, 'rb') as f_src:
            with open(dst, 'wb') as f_dst:
                f_dst.write(f_src.read())
        print(f"Sucesso ao copiar {src} para {dst}")
    except Exception as e:
        print(f"Erro: {e}")
else:
    print(f"Origem não encontrada: {src}")
