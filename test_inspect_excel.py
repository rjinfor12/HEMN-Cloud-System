import pandas as pd
output_path = r"C:\Users\Junior T.I\.gemini\antigravity\scratch\data_analysis\test_split_out2.xlsx"
df_ver = pd.read_excel(output_path)
print("Columns read:", df_ver.columns.tolist())
print("Row 0:", df_ver.iloc[0].tolist())
