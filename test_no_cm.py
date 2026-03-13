import pandas as pd

input_path = r"C:\Users\Junior T.I\OneDrive\Área de Trabalho\sp.csv"
output_path = r"C:\Users\Junior T.I\.gemini\antigravity\scratch\data_analysis\test_no_cm.xlsx"

try:
    df = pd.read_csv(input_path, nrows=5, sep=';', encoding='latin1', dtype=str)
    
    # Write to excel WITHOUT constant_memory
    print("Writing without constant_memory...")
    with pd.ExcelWriter(output_path, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name="Sub_Lote 1", index=False)
        
    print(f"Salvo em {output_path}")
    
    # Ler de volta para verificar
    df_ver = pd.read_excel(output_path, dtype=str)
    print("\nLendo excel salvo:")
    print(df_ver.head(2))
    
except Exception as e:
    print(f"Erro: {e}")
