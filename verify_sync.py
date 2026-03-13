import sys
import os
sys.path.append(os.getcwd())
import pandas as pd
from data_analysis.consolidation_engine import ConsolidationEngine

def test_engine(engine_file, db_path):
    print(f"\n--- Verificando Engine em: {engine_file} ---")
    engine = ConsolidationEngine(target_dir=".", output_file="test.xlsx")
    
    # Teste 1: Só Nome
    print(f"\n[Teste 1] Busca Apenas Nome: ROGERIO ELIAS DO NASCIMENTO JUNIOR")
    df1 = engine.search_cnpj_by_name_cpf(db_path, "ROGERIO ELIAS DO NASCIMENTO JUNIOR", "")
    if df1 is not None and not df1.empty:
        print(f"Sucesso: {len(df1)} registros encontrados.")
    else:
        print("Falha: Nenhum registro encontrado apenas por nome.")

    # Teste 2: Combo Nome + CPF (Simulando o erro do usuário)
    print(f"\n[Teste 2] Busca Combo (Nome + CPF): ROGERIO ELIAS DO NASCIMENTO JUNIOR + 09752279473")
    df2 = engine.search_cnpj_by_name_cpf(db_path, "ROGERIO ELIAS DO NASCIMENTO JUNIOR", "09752279473")
    if df2 is not None and not df2.empty:
        print(f"Sucesso: {len(df2)} registros encontrados via Combo.")
    else:
        print("Falha: Nenhum registro encontrado via Combo.")

    # Teste 3: CPF Mascarado vs Completo (Caso o CPF no DB esteja mascarado)
    # (Este teste depende do que está no DB, mas valida a lógica do motor)
    
if __name__ == "__main__":
    engine_file = r"C:\Users\Junior T.I\.gemini\antigravity\scratch\data_analysis\consolidation_engine.py"
    db_path = r"C:\HEMN_SYSTEM_DB\cnpj.db"
    
    if not os.path.exists(db_path):
        print(f"ERRO: Banco de dados não encontrado em {db_path}")
        sys.exit(1)
        
    test_engine(engine_file, db_path)
