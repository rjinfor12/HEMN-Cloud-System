from PIL import Image

def remove_dynamic_bg(img_path, out_png):
    img = Image.open(img_path).convert("RGBA")
    datas = img.getdata()
    
    # Pega a cor do pixel (0,0) como a cor do fundo
    bg_color = datas[0]
    bg_r, bg_g, bg_b, _ = bg_color
    
    # Tolerância para variação da cor do fundo
    tol = 40
    
    new_data = []
    for item in datas:
        r, g, b, a = item
        
        # Distância da cor atual para a cor de fundo
        if abs(r - bg_r) < tol and abs(g - bg_g) < tol and abs(b - bg_b) < tol:
            # Substitui por totalmente transparente
            new_data.append((0, 0, 0, 0))
        else:
            # Preserva os pixels da logo (Cores neon/claros)
            new_data.append(item)
            
    img.putdata(new_data)
    
    # Se precisar de redimensionamento para ficar igual a logo original
    img = img.resize((500, 500), Image.Resampling.LANCZOS)
    img.save(out_png, "PNG")
    print(f"Salvo PNG Transparente: {out_png}")

if __name__ == "__main__":
    generated_path = r"C:\Users\Junior T.I\.gemini\antigravity\brain\64d3ce78-534d-446b-ac79-7139022da910\hemn_logo_dark_mode_optimized_1771799803405.png"
    target_png = r"C:\Users\Junior T.I\scratch\data_analysis\logo_dark.png"
    
    try:
        remove_dynamic_bg(generated_path, target_png)
    except Exception as e:
        print(f"Erro: {e}")
