from PIL import Image

def remove_dark_background(img_path, out_png, out_ico):
    img = Image.open(img_path)
    img = img.convert("RGBA")
    
    datas = img.getdata()
    
    # Tolerância para o que consideramos "preto" ou muito escuro
    new_data = []
    for item in datas:
        r, g, b, a = item
        # Se for totalmente preto ou cinza muito escuro
        if r < 30 and g < 30 and b < 30:
            new_data.append((0, 0, 0, 0)) # Transparente
        else:
            new_data.append(item)
            
    img.putdata(new_data)
    img.save(out_png, "PNG")
    print(f"Salvo PNG: {out_png}")
    
    size = (256, 256)
    img_ico = img.resize(size, Image.Resampling.LANCZOS)
    img_ico.save(out_ico, format='ICO', sizes=[(256, 256)])
    print(f"Salvo ICO: {out_ico}")

if __name__ == "__main__":
    generated_path = r"C:\Users\Junior T.I\.gemini\antigravity\brain\64d3ce78-534d-446b-ac79-7139022da910\hemn_logo_dark_mode_optimized_1771799803405.png"
    target_png = r"C:\Users\Junior T.I\scratch\data_analysis\logo.png"
    target_ico = r"C:\Users\Junior T.I\scratch\data_analysis\logo.ico"
    
    try:
        remove_dark_background(generated_path, target_png, target_ico)
    except Exception as e:
        print(f"Erro ao processar imagem: {e}")
