import pandas as pd
import os

desktop_path = r"C:\Users\Junior T.I\OneDrive\Área de Trabalho"
file_pr_p1 = os.path.join(desktop_path, "PR P1.xlsx")
file_cobertura = os.path.join(desktop_path, "COBERTURA PR.xlsx")

def check_columns():
    print(f"--- Colunas de {os.path.basename(file_pr_p1)} ---")
    df1 = pd.read_excel(file_pr_p1, nrows=5)
    print(df1.columns.tolist())
    
    print(f"\n--- Colunas de {os.path.basename(file_cobertura)} ---")
    df2 = pd.read_excel(file_cobertura, nrows=5)
    print(df2.columns.tolist())

if __name__ == "__main__":
    check_columns()
