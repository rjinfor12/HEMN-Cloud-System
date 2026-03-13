import pandas as pd
import os

desktop_path = r"C:\Users\Junior T.I\OneDrive\Área de Trabalho"
file_pr_p1 = os.path.join(desktop_path, "PR P1.xlsx")

def peek_data():
    df = pd.read_excel(file_pr_p1, nrows=10)
    print("--- Primeiras 10 linhas de PR P1.xlsx ---")
    print(df.to_string())

if __name__ == "__main__":
    peek_data()
