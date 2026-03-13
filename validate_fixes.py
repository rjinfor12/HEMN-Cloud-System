import pandas as pd
from consolidation_engine import ConsolidationEngine
import os
import sqlite3

# Config - Using production DB now
db_path = r"C:\HEMN_SYSTEM_DB\cnpj.db"
print(f"Using DB: {db_path}")

if not os.path.exists(db_path):
    print("FATAL: DB NOT FOUND AT EXPECTED PATH")
    exit(1)

engine = ConsolidationEngine(target_dir=".", output_file="test_out.csv")

# Create test input
# We'll use "ROGERIO LOPES" which is a known socio in the BR base usually.
test_data = pd.DataFrame({
    'CLIENTE': ['ROGERIO LOPES', 'CLIENTE SEM TELEFONE'],
    'DOC': ['', ''] 
})
test_input = "val_test_input.csv"
test_data.to_csv(test_input, index=False, sep=';', encoding='utf-8-sig')

print("--- Testing Batch Search (only_with_phone=True) ---")
engine.search_cnpj_batch(db_path, test_input, 'CLIENTE', 'DOC', "val_test_output.csv", only_with_phone=True)

if os.path.exists("val_test_output.csv"):
    res = pd.read_csv("val_test_output.csv", sep=';')
    print(f"Results with phone filter: {len(res)} rows")
    if not res.empty:
        # Check for empty phones
        empty_phones = res[res['TELEFONE'].fillna('').astype(str).str.strip() == '']
        print(f"Rows with EMPTY phone: {len(empty_phones)}")
        if len(empty_phones) == 0:
            print("SUCCESS: No empty phones found in batch result.")
else:
    print("No output file generated (maybe no matches found with phone).")

print("\n--- Testing Manual Search (only_with_phone=True) ---")
df_manual = engine.search_cnpj_by_name_cpf(db_path, "ROGERIO LOPES", only_with_phone=True)
if df_manual is not None:
    print(f"Manual Results: {len(df_manual)} rows")
    empty_phones_manual = df_manual[df_manual['telefone_novo'].fillna('').astype(str).str.strip() == '']
    print(f"Manual Rows with EMPTY phone: {len(empty_phones_manual)}")
    if len(empty_phones_manual) == 0:
        print("SUCCESS: No empty phones found in manual search.")
else:
    print("Manual search returned None (expected if socio not found or no phones).")
