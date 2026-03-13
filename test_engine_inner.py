import sys
sys.path.append(r"C:\Users\Junior T.I\scratch\data_analysis")
from consolidation_engine import ConsolidationEngine
import pandas as pd

def print_log(msg):
    print(msg)

# We want to patch itertuples or just read engine source line by line.
# Actually I'll copy the exact code block from split_large_file here to debug.

input_path = r"C:\Users\Junior T.I\scratch\data_analysis\sp_small.csv"

# Mock block
import xlsxwriter
iterator = pd.read_csv(input_path, chunksize=10, sep=';', encoding='utf-8', on_bad_lines='skip', dtype=str)

# Just run exactly what the engine does
for chunk in iterator:
    cols = chunk.columns.tolist()
    print("Writing headers:", cols)
    chunk = chunk.fillna('').astype(str)
    
    first_tuple = next(chunk.itertuples(index=False))
    print("First tuple class:", type(first_tuple))
    print("First tuple row:", first_tuple)
    
    list_tuple = list(first_tuple)
    print("Tuple as list:", list_tuple)
    break
