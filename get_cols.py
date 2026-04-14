import pandas as pd
import sys

def get_columns(path):
    df = pd.read_excel(path, nrows=1)
    return df.columns.tolist()

if __name__ == "__main__":
    cnpj_path = r"C:\Users\Junior T.I\Downloads\GOIAS.xlsx"
    vivo_path = r"C:\Users\Junior T.I\OneDrive\Área de Trabalho\NV COKPIT\COBERTURA GO.xlsx"
    
    print("CNPJ Columns:")
    print(get_columns(cnpj_path))
    
    print("\nVivo Columns:")
    print(get_columns(vivo_path))
