
import os
import pandas as pd
from consolidation_engine import ConsolidationEngine

PATH_DB_CNPJ = r"C:\HEMN_SYSTEM_DB\cnpj.db"

def test_search():
    engine = ConsolidationEngine(target_dir="", output_file="")
    name = "ROGERIO ELIAS DO NASCIMENTO JUNIOR"
    cpf = "09752279473"
    
    print(f"Testing search for: {name} | {cpf}")
    if not os.path.exists(PATH_DB_CNPJ):
        print(f"ERROR: Database not found at {PATH_DB_CNPJ}")
        return

    df = engine.search_cnpj_by_name_cpf(PATH_DB_CNPJ, name, cpf)
    
    if df is None:
        print("Result: None")
    elif df.empty:
        print("Result: Empty DataFrame")
    else:
        print(f"Result: Found {len(df)} records")
        print(df[['razao_social', 'cnpj_completo', 'situacao']])

if __name__ == "__main__":
    test_search()
