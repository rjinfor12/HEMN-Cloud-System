import pandas as pd
import os

input_path = r"C:\Users\Junior T.I\OneDrive\Área de Trabalho\sp.csv"
output_path = r"C:\Users\Junior T.I\.gemini\antigravity\scratch\data_analysis\test_split_out2.xlsx"

print("Lendo como latin-1...")
df = pd.read_csv(input_path, nrows=5, sep=';', encoding='latin1', dtype=str)
print("Colunas lidas:")
print(df.columns.tolist())

# Converter colunas e dados para string normalizada
df.columns = [c.encode('latin1').decode('utf-8', 'replace') if isinstance(c, str) else c for c in df.columns]
for col in df.columns:
    df[col] = df[col].apply(lambda x: x.encode('latin1').decode('utf-8', 'replace') if isinstance(x, str) else x)

print("Colunas normalizadas:")
print(df.columns.tolist())

print("\nWriting to excel...")
with pd.ExcelWriter(output_path, engine='xlsxwriter', engine_kwargs={'options': {'constant_memory': True}}) as writer:
    df.to_excel(writer, sheet_name="Sheet1", index=False)
    
df_ver = pd.read_excel(output_path, dtype=str)
print("\nLido:")
print(df_ver.head(2))
