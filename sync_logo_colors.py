from PIL import Image
import colorsys

def create_light_theme_logo(in_path, out_path):
    img = Image.open(in_path).convert("RGBA")
    datas = img.getdata()
    
    new_data = []
    for item in datas:
        r, g, b, a = item
        
        # Ignora transparencia total
        if a == 0:
            new_data.append(item)
            continue
            
        # Converte RGB para HSV pra preservar a cor, mas reduzir brutalmente o brilho
        h, s, v = colorsys.rgb_to_hsv(r/255.0, g/255.0, b/255.0)
        
        # O tema claro pede cores escuras (Dark Navy, Charcoal)
        # Então vamos reduzir a saturação um pouco e o brilho massivamente
        v_new = 0.25 # Brilho baixo (escuro)
        s_new = min(1.0, s * 1.2) # Saturar um pouquinho os azuis/roxos que sobrarem
        
        # Transforma de volta pra RGB
        r_new, g_new, b_new = colorsys.hsv_to_rgb(h, s_new, v_new)
        
        # Para os letreiros muito claros (branco do neon vira cinza escuro), diminuiremos também.
        # Mas vamos forçar a cor inteira para um azul carbono muito elegante.
        # Misturando a cor original escurecida com um azul profundo:
        navy_r, navy_g, navy_b = 20, 30, 60
        
        final_r = int((r_new * 255 * 0.5) + (navy_r * 0.5))
        final_g = int((g_new * 255 * 0.5) + (navy_g * 0.5))
        final_b = int((b_new * 255 * 0.5) + (navy_b * 0.5))
        
        # Conserta a gama (se passar de 255)
        final_r = max(0, min(255, final_r))
        final_g = max(0, min(255, final_g))
        final_b = max(0, min(255, final_b))
        
        # Se for quase branco, não deixe virar chumbo neutro, ponha um toque de azul
        if r > 200 and g > 200 and b > 200:
            final_r, final_g, final_b = 25, 35, 65
            
        new_data.append((final_r, final_g, final_b, a))
        
    img.putdata(new_data)
    img.save(out_path, "PNG")
    print(f"Logo Sincronizada (Dark Edition): {out_path}")

if __name__ == "__main__":
    # Usa a logo_dark (Neon brilhante) como molde para extrair 100% da sua forma
    base_neon_logo = r"C:\Users\Junior T.I\scratch\data_analysis\logo_dark.png"
    target_light_logo = r"C:\Users\Junior T.I\scratch\data_analysis\logo.png"
    target_ico = r"C:\Users\Junior T.I\scratch\data_analysis\logo.ico"
    
    try:
        create_light_theme_logo(base_neon_logo, target_light_logo)
        
        # Aproveita e gera o ICO dessa logo nova também pros atalhos claros
        img = Image.open(target_light_logo).convert("RGBA")
        img_ico = img.resize((256, 256), Image.Resampling.LANCZOS)
        img_ico.save(target_ico, format='ICO', sizes=[(256, 256)])
        
    except Exception as e:
        print(f"Erro: {e}")
