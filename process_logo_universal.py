from PIL import Image

def cut_white_bg(in_path, out_light, out_dark, out_ico):
    img = Image.open(in_path).convert("RGBA")
    datas = img.getdata()
    
    bg_color = datas[0] # White background from top-left
    bg_r, bg_g, bg_b, _ = bg_color
    tol = 30
    
    new_data = []
    for item in datas:
        r, g, b, a = item
        if abs(r - bg_r) < tol and abs(g - bg_g) < tol and abs(b - bg_b) < tol:
            new_data.append((0, 0, 0, 0)) # Transparente
        else:
            new_data.append(item)
            
    img.putdata(new_data)
    
    # Redimensionamento
    img = img.resize((350, 350), Image.Resampling.LANCZOS)
    
    # Salva a MESMA IMAGEM para ambos os temas!
    img.save(out_light, "PNG")
    img.save(out_dark, "PNG")
    print(f"Substituido ambos logo.png e logo_dark.png com a mesma imagem.")
    
    img_ico = img.resize((256, 256), Image.Resampling.LANCZOS)
    img_ico.save(out_ico, format='ICO', sizes=[(256, 256)])
    print(f"Salvo ICO: {out_ico}")

if __name__ == "__main__":
    generated_path = r"C:\Users\Junior T.I\.gemini\antigravity\brain\64d3ce78-534d-446b-ac79-7139022da910\hemn_logo_universal_1771800789750.png"
    target_light = r"C:\Users\Junior T.I\scratch\data_analysis\logo.png"
    target_dark = r"C:\Users\Junior T.I\scratch\data_analysis\logo_dark.png"
    target_ico = r"C:\Users\Junior T.I\scratch\data_analysis\logo.ico"
    
    try:
        cut_white_bg(generated_path, target_light, target_dark, target_ico)
    except Exception as e:
        print(f"Erro: {e}")
