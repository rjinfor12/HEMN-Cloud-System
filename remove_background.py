from PIL import Image
import os

def make_transparent(img_path, output_path):
    img = Image.open(img_path).convert("RGBA")
    datas = img.getdata()

    new_data = []
    # Magenta Chroma Key (#FF00FF)
    # Vamos usar uma pequena tolerância caso a compressão tenha alterado levemente a cor
    # Subsitui o quase preto por transparente, com threshold um pouco maior p/ anti-aliasing
    for item in datas:
        # Se for muito próximo de Preto
        if item[0] < 30 and item[1] < 30 and item[2] < 30:
            new_data.append((255, 255, 255, 0)) # Totalmente transparente
        else:
            new_data.append(item)

    img.putdata(new_data)
    img.save(output_path, "PNG")
    print(f"Sucesso: Fundo removido e salvo em {output_path}")

if __name__ == "__main__":
    src = r"C:\Users\Junior T.I\.gemini\antigravity\brain\64d3ce78-534d-446b-ac79-7139022da910\hemn_logo_raw_1771781047440.png"
    dst = r"C:\Users\Junior T.I\.gemini\antigravity\scratch\data_analysis\logo.png"
    make_transparent(src, dst)
