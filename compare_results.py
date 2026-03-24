import pandas as pd
import sys

def compare():
    input_file = r"C:\Users\Junior T.I\OneDrive\Área de Trabalho\testeof.xlsx"
    output_file = r"C:\Users\Junior T.I\Downloads\Enriquecido_dff3359e.xlsx"
    
    try:
        print(f"--- Lendo Arquivo de Entrada: {input_file} ---")
        df_in = pd.read_excel(input_file).fillna('')
        
        print(f"--- Lendo Arquivo de Saída (Enriquecido): {output_file} ---")
        try:
            df_out = pd.read_excel(output_file).fillna('')
        except:
            df_out = pd.read_excel(output_file + ".xlsx").fillna('')

        print(f"\n--- Dados de Entrada (Primeiras 10 linhas) ---")
        # Mostrar colunas que parecem ser CPF e Nome
        cols_to_show = [c for c in df_in.columns if any(x in c.upper() for x in ['CPF', 'DOC', 'NOME', 'CLIENTE'])]
        if not cols_to_show: cols_to_show = df_in.columns.tolist()[:2]
        print(df_in[cols_to_show].head(10))
        
        print(f"\n--- Dados de Saída (Primeiras 10 linhas) ---")
        cols_to_show_out = ['CHAVE DO SOCIO', 'CNPJ', 'RAZAO_SOCIAL']
        print(df_out[cols_to_show_out].head(10))
        
        print("\n--- Contagem de CPFs Únicos no Input ---")
        cpf_cols = [c for c in df_in.columns if 'CPF' in c.upper() or 'DOC' in c.upper()]
        if cpf_cols:
            print(df_in[cpf_cols[0]].nunique())
        else:
            print("Coluna de CPF não identificada no input.")
        
        print("\n--- Contagem de Chaves Únicas no Output ---")
        if 'CHAVE DO SOCIO' in df_out.columns:
            print(df_out['CHAVE DO SOCIO'].nunique())
        else:
            print("Coluna 'CHAVE DO SOCIO' não encontrada no output.")
            
    except Exception as e:
        print(f"Erro ao ler arquivos: {e}")

if __name__ == "__main__":
    compare()
