from PIL import Image, ImageDraw, ImageFont
import os

def create_ad():
    # Use a clean system font commonly available on Windows
    font_path = "C:\\Windows\\Fonts\\segoeuib.ttf"
    font_regular_path = "C:\\Windows\\Fonts\\segoeui.ttf"
    
    # Fallback if Segoe is missing
    if not os.path.exists(font_path):
        font_path = "C:\\Windows\\Fonts\\arialbd.ttf"
        font_regular_path = "C:\\Windows\\Fonts\\arial.ttf"

    img_path = r"C:\Users\Junior T.I\.gemini\antigravity\brain\c4f60ece-5add-49a6-9342-0b4e3f5ce214\vivo_clean_bg_1775066721064.png"
    img = Image.open(img_path).convert("RGBA")
    width, height = img.size

    overlay = Image.new('RGBA', img.size, (0,0,0,0))
    d_overlay = ImageDraw.Draw(overlay)
    
    d_overlay.rectangle([0, 0, width, height*0.15], fill=(30, 0, 50, 150))
    d_overlay.rectangle([0, height*0.75, width, height], fill=(62, 0, 102, 230))
    
    img = Image.alpha_composite(img, overlay)
    draw = ImageDraw.Draw(img)

    font_huge = ImageFont.truetype(font_path, int(width * 0.065))
    font_large = ImageFont.truetype(font_path, int(width * 0.05))
    font_medium = ImageFont.truetype(font_regular_path, int(width * 0.035))
    font_price = ImageFont.truetype(font_path, int(width * 0.075))

    def draw_text_with_shadow(dr, position, text, font, text_color, shadow_color=(0,0,0,255)):
        x, y = position
        shadow_offset = 3
        dr.text((x+shadow_offset, y+shadow_offset), text, font=font, fill=shadow_color, align="center")
        dr.text((x, y), text, font=font, fill=text_color, align="center")

    headline = "TER APENAS 1 INTERNET\nCUSTA MUITO CARO"
    bbox1 = draw.multiline_textbbox((0, 0), headline, font=font_huge, align="center")
    tw1 = bbox1[2] - bbox1[0]
    draw_text_with_shadow(draw, ((width - tw1) / 2, height * 0.02), headline, font_huge, (255, 255, 255))

    sub = "Sua internet caiu?\nAs suas vendas NAO param."
    bbox2 = draw.multiline_textbbox((0, 0), sub, font=font_large, align="center")
    tw2 = bbox2[2] - bbox2[0]
    th2 = bbox2[3] - bbox2[1]

    d_overlay2 = Image.new('RGBA', img.size, (0,0,0,0))
    rect_y = height * 0.5 - 20
    d_overlay2_draw = ImageDraw.Draw(d_overlay2)
    d_overlay2_draw.rectangle([width/2 - tw2/2 - 30, rect_y, width/2 + tw2/2 + 30, rect_y + th2 + 40], fill=(222, 11, 146, 220)) 
    img = Image.alpha_composite(img, d_overlay2)
    
    draw = ImageDraw.Draw(img)
    draw_text_with_shadow(draw, ((width - tw2) / 2, rect_y + 20), sub, font_large, (255, 255, 255))

    footer1 = "O BACKUP INTELIGENTE VIVO"
    footer2 = "Por apenas R$ 99,90 / mes"
    
    bbox_f1 = draw.textbbox((0, 0), footer1, font=font_medium)
    tw_f1 = bbox_f1[2] - bbox_f1[0]
    draw_text_with_shadow(draw, ((width - tw_f1) / 2, height * 0.82), footer1, font_medium, (255, 255, 255))

    bbox_f2 = draw.textbbox((0, 0), footer2, font=font_price)
    tw_f2 = bbox_f2[2] - bbox_f2[0]
    draw_text_with_shadow(draw, ((width - tw_f2) / 2, height * 0.88), footer2, font_price, (255, 255, 0))

    final_path = r"C:\Users\Junior T.I\.gemini\antigravity\scratch\Anuncio_Vivo_Pronto_Final.png"
    img.save(final_path)
    print(f"Sucesso! Anuncio salvo em: {final_path}")

create_ad()
