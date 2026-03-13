from PIL import Image

def remove_white_background(img_path, out_png, out_ico):
    # Load image and convert to RGBA
    img = Image.open(img_path)
    img = img.convert("RGBA")
    
    datas = img.getdata()
    
    # Tolerância para o que consideramos "branco" ou muito claro
    new_data = []
    for item in datas:
        # Pega r, g, b, a
        r, g, b, a = item
        # Se for branco puro ou muito próximo com alta luminosidade (fundo)
        if r > 240 and g > 240 and b > 240:
            new_data.append((255, 255, 255, 0)) # Fica transparente
        else:
            new_data.append(item)
            
    img.putdata(new_data)
    
    # O ideal no app é que a logo seja num formato agradável,
    # caso seja muito grande vamos redimensionar se necessário.
    
    # Save as PNG
    img.save(out_png, "PNG")
    print(f"Salvo PNG: {out_png}")
    
    # Para o ICO, uma imagem quadrada funciona melhor.
    # Fazemos um crop no centro (ou só redimensionamos pra 256x256).
    size = (256, 256)
    img_ico = img.resize(size, Image.Resampling.LANCZOS)
    img_ico.save(out_ico, format='ICO', sizes=[(256, 256)])
    print(f"Salvo ICO: {out_ico}")

if __name__ == "__main__":
    generated_path = r"C:\Users\Junior T.I\.gemini\antigravity\brain\64d3ce78-534d-446b-ac79-7139022da910\hemn_logo_redesign_1771799534922.png"
    target_png = r"C:\Users\Junior T.I\scratch\data_analysis\logo.png"
    target_ico = r"C:\Users\Junior T.I\scratch\data_analysis\logo.ico"
    
    try:
        remove_white_background(generated_path, target_png, target_ico)
    except Exception as e:
        print(f"Erro ao processar imagem: {e}")
