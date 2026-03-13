import os

file_path = r"c:\Users\Junior T.I\.gemini\antigravity\scratch\data_analysis\cloud_engine_vps.py"

replacements = {
    "├í": "á",
    "├¡": "í",
    "├ç": "Ç",
    "├â": "Ã",
    "├│": "ó",
    "├ë": "É",
    "├ú": "ã",
    "├║": "ú",
    "├¬": "ê",
    "├ô": "Ô",
    "├º": "ç",
    "├Á": "õ",
    "├┤": "ô",
    "├Ü": "Ú",
    "├Ç": "À",
    "├È": "È",
    "├ä": "Ä",
}

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

for old, new in replacements.items():
    content = content.replace(old, new)

# Special cases like Solu├º├Áes -> Soluções (some might have been double corrupted)
content = content.replace("├º├Áes", "ções")
content = content.replace("├º├úo", "ção")
content = content.replace("├ç├âO", "ÇÃO")

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Encoding repair completed.")
