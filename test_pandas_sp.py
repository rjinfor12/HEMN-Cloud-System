import pandas as pd
input_path = r"C:\Users\Junior T.I\OneDrive\Área de Trabalho\sp.csv"

try:
    with open(input_path, 'r', encoding='utf-8', errors='replace') as f:
        first_line = f.readline()
    sep = ';' if ';' in first_line else ','
    
    print(f"Detected Sep: {sep}")
    
    # Simulate the exact read_csv call from the code
    # The actual code uses encoding='utf-8' without errors parameter, which might crash,
    # but let's see. If it read it, maybe it read it weirdly.
    df = pd.read_csv(input_path, nrows=5, sep=sep, encoding='utf-8', on_bad_lines='skip', dtype=str)
    
    print("Columns:", df.columns.tolist())
    print("\nData:")
    print(df.head())
except Exception as e:
    print(f"UTF-8 Error: {e}")
    # Try with other encodings
    for enc in ['utf-8-sig', 'latin1', 'cp1252']:
        try:
            print(f"\nTrying {enc}...")
            df = pd.read_csv(input_path, nrows=5, sep=';', encoding=enc, dtype=str)
            print("Columns:", df.columns.tolist())
            print(df.head())
            break
        except Exception as e2:
            print(f"{enc} Error: {e2}")
