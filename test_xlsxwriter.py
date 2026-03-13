import pandas as pd
import xlsxwriter
import time

input_path = r"C:\Users\Junior T.I\OneDrive\Área de Trabalho\sp.csv"
output_path = r"C:\Users\Junior T.I\.gemini\antigravity\scratch\data_analysis\test_xlsxwriter.xlsx"

try:
    print("Iniciando chunk read...")
    df = pd.read_csv(input_path, nrows=50, sep=';', encoding='latin1', dtype=str)
    
    print("Escrevendo manualmente via xlsxwriter row_by_row...")
    start = time.time()
    
    workbook = xlsxwriter.Workbook(output_path, {'constant_memory': True})
    worksheet = workbook.add_worksheet('Sub_Lote 1')
    
    # Header
    worksheet.write_row(0, 0, df.columns.tolist())
    
    # Rows
    for r_idx, row_data in enumerate(df.itertuples(index=False), 1):
        worksheet.write_row(r_idx, 0, row_data)
        
    workbook.close()
    print(f"Tempo: {time.time() - start:.2f}s")
    
    # Ler de volta para verificar
    df_ver = pd.read_excel(output_path, dtype=str)
    print("\nLendo excel salvo:")
    print(df_ver.head(2))
    
except Exception as e:
    print(f"Erro: {e}")
