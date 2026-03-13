import shutil
import os

src_dir = r"C:\Users\Junior T.I\.gemini\antigravity\scratch\data_analysis"
dst_dir = r"C:\Users\Junior T.I\scratch\data_analysis"

files_to_copy = ["consolidation_engine.py", "logo.png", "logo.ico"]

print(f"Iniciando cópia de arquivos de {src_dir} para {dst_dir}...")

for filename in files_to_copy:
    src_path = os.path.join(src_dir, filename)
    dst_path = os.path.join(dst_dir, filename)
    
    if os.path.exists(src_path):
        try:
            shutil.copy2(src_path, dst_path)
            print(f"Sucesso: {filename} copiado.")
        except Exception as e:
            print(f"Erro ao copiar {filename}: {e}")
    else:
        print(f"Aviso: {filename} não encontrado na origem.")

print("Processo concluído.")
