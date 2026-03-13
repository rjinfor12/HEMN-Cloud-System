import pandas as pd
import os

target_dir = r"C:\Users\Junior T.I\Downloads\BASE NOVA_26\OI_NOVO"
file_path = os.path.join(target_dir, "FIBRA OI_PF_AC_1301.xlsx")

def peek_columns():
    df = pd.read_excel(file_path, nrows=5)
    print(f"Lendo: {file_path}")
    print("\n--- Nomes das Colunas ---")
    print(df.columns.tolist())
    print("\n--- Primeiros 5 Registros ---")
    print(df.head())

if __name__ == "__main__":
    peek_columns()
