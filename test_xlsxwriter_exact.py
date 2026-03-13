import pandas as pd
import xlsxwriter

input_path = r"C:\Users\Junior T.I\scratch\data_analysis\sp_small.csv"
output_path = r"C:\Users\Junior T.I\.gemini\antigravity\scratch\data_analysis\test_xlsxwriter_exact.xlsx"

iterator = pd.read_csv(input_path, chunksize=100, sep=';', encoding='utf-8', on_bad_lines='skip', dtype=str)

workbook = xlsxwriter.Workbook(output_path, {'constant_memory': True, 'nan_inf_to_errors': True})
worksheet = workbook.add_worksheet("Sub_Lote 1")

current_row = 1
header_written = False

for chunk in iterator:
    if not header_written:
        cols = chunk.columns.tolist()
        worksheet.write_row(0, 0, cols)
        header_written = True
        
    chunk = chunk.fillna('').astype(str)
    
    for r_data in chunk.itertuples(index=False):
        worksheet.write_row(current_row, 0, r_data)
        current_row += 1
        
workbook.close()

df2 = pd.read_excel(output_path, dtype=str)
print("Verifying Output:")
print(df2.head(2))
