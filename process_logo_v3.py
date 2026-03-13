from PIL import Image

def remove_bg(img_path, out_path, is_dark_bg=False):
    img = Image.open(img_path).convert("RGBA")
    datas = img.getdata()
    
    # Tolerância de Cor
    tol = 30
    
    # Detecta a cor do canto superior esquerdo pra servir de base de apagamento
    bg_color = datas[0]
    bg_r, bg_g, bg_b, _ = bg_color
    
    new_data = []
    for item in datas:
        r, g, b, a = item
        
        # Se for próxima o suficiente da cor do fundo do canto (preto ou branco)
        if abs(r - bg_r) < tol and abs(g - bg_g) < tol and abs(b - bg_b) < tol:
            new_data.append((0, 0, 0, 0))
        else:
            new_data.append(item)
            
    img.putdata(new_data)
    # Redimensionamento suave padronizado pra UI
    img = img.resize((350, 350), Image.Resampling.LANCZOS)
    img.save(out_path, "PNG")
    print(f"[{'Escura/Neon' if is_dark_bg else 'Claro/DarkNavy'}] Salvo em: {out_path}")
    return img

if __name__ == "__main__":
    light_logo = r"C:\Users\Junior T.I\.gemini\antigravity\brain\64d3ce78-534d-446b-ac79-7139022da910\hemn_logo_light_v3_1771800257000.png"
    dark_logo = r"C:\Users\Junior T.I\.gemini\antigravity\brain\64d3ce78-534d-446b-ac79-7139022da910\hemn_logo_dark_v3_1771800280673.png"
    
    out_light = r"C:\Users\Junior T.I\scratch\data_analysis\logo.png"
    out_dark = r"C:\Users\Junior T.I\scratch\data_analysis\logo_dark.png"
    out_ico = r"C:\Users\Junior T.I\scratch\data_analysis\logo.ico"
    
    try:
        # Processa Logo Claro (Fundo Branco Original -> Textos Escuros)
        img_l = remove_bg(light_logo, out_light, is_dark_bg=False)
        # Salva o ícone global baseado na logo clara
        img_ico = img_l.resize((256, 256), Image.Resampling.LANCZOS)
        img_ico.save(out_ico, format='ICO', sizes=[(256, 256)])
        
        # Processa Logo Escura (Fundo Preto Original -> Textos Neons)
        remove_bg(dark_logo, out_dark, is_dark_bg=True)
        
    except Exception as e:
        print(f"Erro: {e}")
