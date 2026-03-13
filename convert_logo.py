from PIL import Image
import os

img_path = r"C:\Users\Junior T.I\.gemini\antigravity\scratch\data_analysis\logo.png"
ico_path = r"C:\Users\Junior T.I\.gemini\antigravity\scratch\data_analysis\logo.ico"

if os.path.exists(img_path):
    img = Image.open(img_path)
    # Redimensionar para tamanhos padrão de ícone se necessário, mas o save('ico') do PIL já lida com múltiplos tamanhos
    img.save(ico_path, format='ICO', sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    print(f"Ícone criado com sucesso em: {ico_path}")
else:
    print(f"Erro: Logotipo não encontrado em {img_path}")
