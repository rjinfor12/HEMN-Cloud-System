import pandas as pd

input_path = r"C:\Users\Junior T.I\scratch\data_analysis\sp_small.csv"

print("------------- USING UTF-8 -------------")
try:
    df = pd.read_csv(input_path, nrows=5, sep=';', encoding='utf-8', on_bad_lines='skip', dtype=str)
    print("Cols:", df.columns.tolist())
    print(df.head(2))
except Exception as e:
    print("Erro utf-8:", e)

print("\n------------- USING LATIN1 -------------")
try:
    df = pd.read_csv(input_path, nrows=5, sep=';', encoding='latin1', on_bad_lines='skip', dtype=str)
    print("Cols:", df.columns.tolist())
    print(df.head(2))
except Exception as e:
    print("Erro latin1:", e)
