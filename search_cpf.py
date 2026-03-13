import pandas as pd
import os
import glob

# Parâmetros de busca
cpf_alvo = "09752279473"
cpf_formatado = "097.522.794-73"
search_dir = r"C:\Users\Junior T.I\OneDrive\Área de Trabalho"

def search_in_files():
    # Busca recursiva em todos os subdiretórios
    files = glob.glob(os.path.join(search_dir, "**", "*.xlsx"), recursive=True) + \
            glob.glob(os.path.join(search_dir, "**", "*.csv"), recursive=True)
    
    print(f"Iniciando busca em {len(files)} arquivos...")
    
    for file in files:
        file_name = os.path.basename(file)
        print(f"  Pesquisando em {file_name}...")
        
        try:
            if file.endswith('.xlsx'):
                # Lê apenas as primeiras colunas para otimizar ou colunas específicas se soubermos
                # Como não sabemos, vamos ler colunas que costumam ter documentos
                df = pd.read_excel(file)
            else:
                df = pd.read_csv(file, sep=None, engine='python', encoding='latin-1')

            # Converter todo o dataframe para string para busca global
            mask = df.astype(str).apply(lambda x: x.str.contains(cpf_alvo) | x.str.contains(cpf_formatado)).any(axis=1)
            results = df[mask]

            if not results.empty:
                print(f"\n[!] ENCONTRADO em {file_name}:")
                print(results.to_string())
                print("-" * 50)
                
        except Exception as e:
            # print(f"    Erro ao ler {file_name}: {e}")
            pass

if __name__ == "__main__":
    search_in_files()
