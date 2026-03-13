import pandas as pd
df = pd.read_excel(r'C:\Users\Junior T.I\.gemini\antigravity\scratch\data_analysis\test_split_engine.xlsx', sheet_name='Sub_Lote 1', nrows=5, dtype=str)
print("Colunas:")
print(df.columns)
print("Dados:")
print(df.head())
