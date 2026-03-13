from PIL import Image
import os

def convert_to_ico(png_path, ico_path):
    if not os.path.exists(png_path):
        print(f"Erro: {png_path} não encontrado.")
        return
    
    img = Image.open(png_path)
    # Definir tamanhos padrão para ícones do Windows
    icon_sizes = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    img.save(ico_path, format='ICO', sizes=icon_sizes)
    print(f"Sucesso: Ícone gerado em {ico_path}")

if __name__ == "__main__":
    # Converter o logo processado (sem fundo) para ICO
    src = r"C:\Users\Junior T.I\.gemini\antigravity\scratch\data_analysis\logo.png"
    dst = r"C:\Users\Junior T.I\.gemini\antigravity\scratch\data_analysis\logo_elite.ico"
    convert_to_ico(src, dst)
