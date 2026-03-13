from PIL import Image

def generate_perfect_logos(dark_source_path, out_dark, out_light, out_ico):
    # Abrimos a imagem original que estava num fundo PURE BLACK (#000000)
    img = Image.open(dark_source_path).convert("RGBA")
    datas = img.getdata()
    
    dark_theme_data = []
    light_theme_data = []
    
    for item in datas:
        r, g, b, a = item
        
        # Como o fundo é preto, a "força" do pixel dita o quanto ele é opaco (luz pura)
        # O Pixel mais claro entre RGB define a transparência.
        max_light = max(r, g, b)
        
        if max_light == 0:
            # Preto absoluto = totalmente transparente
            dark_theme_data.append((0, 0, 0, 0))
            light_theme_data.append((0, 0, 0, 0))
            continue
            
        # Calcula a cor real daquele pixel se ele estivesse iluminado 100%
        # Usamos clamp para garantir que fique entre 0 e 255
        alpha = max_light
        real_r = int((r / alpha) * 255)
        real_g = int((g / alpha) * 255)
        real_b = int((b / alpha) * 255)
        
        # A Logo DARK usa as cores Neons brilhantes normais, só que com o novo alpha perfeito
        dark_theme_data.append((real_r, real_g, real_b, alpha))
        
        # A Logo LIGHT precisa pintar a mesma forma com cores Escuras sem alterar o brilho e contraste da forma
        # Vamos mapear as cores CIANO/ROXO para algo Azul Marinho
        # Mudar tudo para um azul marinho chique preservando a topologia da logo
        # Em vez de inverter o neon, vamos chapar um azul forte e deixar o Alpha desenhar a forma
        light_r = 15
        light_g = 35
        light_b = 65
        
        # O texto na logo Neon geralmente é muito claro/branco (r, g, b > 200). 
        # Vamos pintar o texto de cinza chumbo
        if real_r > 200 and real_g > 200 and real_b > 200:
            light_r = 40
            light_g = 45
            light_b = 55
            
        light_theme_data.append((light_r, light_g, light_b, alpha))

    # Cria e salva Logo Escura (completamente limpa de borroes cinzas)
    img_dark_final = Image.new("RGBA", img.size)
    img_dark_final.putdata(dark_theme_data)
    img_dark_final = img_dark_final.resize((350, 350), Image.Resampling.LANCZOS)
    img_dark_final.save(out_dark, "PNG")
    
    # Cria e salva Logo Clara (Sombra exata em Marinho)
    img_light_final = Image.new("RGBA", img.size)
    img_light_final.putdata(light_theme_data)
    img_light_final = img_light_final.resize((350, 350), Image.Resampling.LANCZOS)
    img_light_final.save(out_light, "PNG")
    
    # Ícone do App
    img_ico = img_light_final.resize((256, 256), Image.Resampling.LANCZOS)
    img_ico.save(out_ico, format='ICO', sizes=[(256, 256)])
    
    print("Processamento Alpha concluído com perfeição.")

if __name__ == "__main__":
    dark_logo_neon = r"C:\Users\Junior T.I\.gemini\antigravity\brain\64d3ce78-534d-446b-ac79-7139022da910\hemn_logo_dark_v3_1771800280673.png"
    
    target_light = r"C:\Users\Junior T.I\scratch\data_analysis\logo.png"
    target_dark = r"C:\Users\Junior T.I\scratch\data_analysis\logo_dark.png"
    target_ico = r"C:\Users\Junior T.I\scratch\data_analysis\logo.ico"
    
    try:
        generate_perfect_logos(dark_logo_neon, target_dark, target_light, target_ico)
    except Exception as e:
        print(e)
