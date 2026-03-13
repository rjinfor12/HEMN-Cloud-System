import pandas as pd
import os

input_path = r"C:\Users\Junior T.I\OneDrive\Área de Trabalho\sp.csv"
output_path = r"C:\Users\Junior T.I\.gemini\antigravity\scratch\data_analysis\test_split_out.xlsx"

try:
    print("Iniciando chunk read...")
    encoding_to_use = 'utf-8'
    sep = ';'
    
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            first_line = f.readline()
            sep = ';' if ';' in first_line else ','
    except UnicodeDecodeError:
        encoding_to_use = 'latin1'
        with open(input_path, 'r', encoding='latin1') as f:
            first_line = f.readline()
            sep = ';' if ';' in first_line else ','
            
    # Try reading the first 10 rows
    df = pd.read_csv(input_path, nrows=10, sep=sep, encoding=encoding_to_use, on_bad_lines='skip', dtype=str)
    print("DataFrame original lido. Colunas:")
    print(df.columns.tolist())
    print("\nHead:")
    print(df.head(2))
    
    # Write to excel
    print("\nWriting to excel...")
    with pd.ExcelWriter(output_path, engine='xlsxwriter', engine_kwargs={'options': {'constant_memory': True}}) as writer:
        df.to_excel(writer, sheet_name="Sub_Lote 1", index=False)
        
    print(f"Salvo em {output_path}")
    
    # Ler de volta para verificar
    df_ver = pd.read_excel(output_path, dtype=str)
    print("\nLendo excel salvo:")
    print(df_ver.head(2))
    
except Exception as e:
    print(f"Erro: {e}")
