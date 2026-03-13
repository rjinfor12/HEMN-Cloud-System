import pandas as pd
import xlsxwriter

out_path = r"C:\Users\Junior T.I\.gemini\antigravity\scratch\data_analysis\test_namedtuple.xlsx"
df = pd.DataFrame({"CNPJ": ["123"], "RAZÃO SOCIAL": ["TESTE LTDA"]})

with xlsxwriter.Workbook(out_path) as wb:
    ws = wb.add_worksheet()
    ws.write_row(0, 0, df.columns.tolist())
    for r_data in df.itertuples(index=False):
        print("Writing:", type(r_data), r_data)
        ws.write_row(1, 0, r_data)
        
df2 = pd.read_excel(out_path)
print("Result:")
print(df2)
