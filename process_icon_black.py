from PIL import Image

def extract_alpha_from_black(img_path, out_path_1, out_path_2, out_ico):
    img = Image.open(img_path).convert("RGBA")
    datas = img.getdata()
    
    new_data = []
    
    for item in datas:
        r, g, b, a = item
        
        # Max light represents how "far" from black the pixel is
        max_light = max(r, g, b)
        
        if max_light < 5:
            # Preto absoluto
            new_data.append((0, 0, 0, 0))
            continue
            
        # O alpha é a luminosidade do pixel
        alpha = max_light
        real_r = int((r / alpha) * 255)
        real_g = int((g / alpha) * 255)
        real_b = int((b / alpha) * 255)
        
        # Usamos exatamente a mesma cor vibrante para os DOIS temas, com o alpha perfeito
        new_data.append((real_r, real_g, real_b, alpha))

    final_img = Image.new("RGBA", img.size)
    final_img.putdata(new_data)
    
    # Fazer um crop no bbox pra remover toda margem
    bbox = final_img.getbbox()
    if bbox:
        final_img = final_img.crop(bbox)
        
    final_img = final_img.resize((350, 350), Image.Resampling.LANCZOS)
    
    # Salvar a mesta imagem pros dois paineis
    final_img.save(out_path_1, "PNG")
    final_img.save(out_path_2, "PNG")
    
    # Ícone do App
    img_ico = final_img.resize((256, 256), Image.Resampling.LANCZOS)
    img_ico.save(out_ico, format='ICO', sizes=[(256, 256)])
    
    print("Ícone extraído perfeitamente sem fundos e sem texto.")

if __name__ == "__main__":
    dark_logo_neon = r"C:\Users\Junior T.I\.gemini\antigravity\brain\64d3ce78-534d-446b-ac79-7139022da910\hemn_icon_only_1771801031108.png"
    
    target_light = r"C:\Users\Junior T.I\scratch\data_analysis\logo.png"
    target_dark = r"C:\Users\Junior T.I\scratch\data_analysis\logo_dark.png"
    target_ico = r"C:\Users\Junior T.I\scratch\data_analysis\logo.ico"
    
    try:
        extract_alpha_from_black(dark_logo_neon, target_light, target_dark, target_ico)
    except Exception as e:
        print(e)
