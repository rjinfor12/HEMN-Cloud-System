import sys
import os
import time

# Adicionar o diretório atual ao path para importar a engine
sys.path.append(os.getcwd())

from data_analysis.consolidation_engine import ConsolidationEngine

def test_engine_v15():
    # Caminho REAL do banco de dados 41GB
    db_path = r"C:\HEMN_SYSTEM_DB\cnpj.db"
    target_dir = r"C:\Users\Junior T.I\.gemini\antigravity\scratch\data_analysis"
    output_file = "manual_search_test_v15.xlsx"
    
    # Mock log callback
    def mock_log(msg):
        print(f"[{time.strftime('%H:%M:%S')}] {msg}")

    # Remove o arquivo de teste anterior se existir
    if os.path.exists(output_file):
        os.remove(output_file)

    engine = ConsolidationEngine(target_dir, output_file, log_callback=mock_log)
    
    name = "ROGERIO ELIAS DO NASCIMENTO JUNIOR"
    cpf = "09752279473"
    
    print(f"\n--- [TESTE PERFORMANCE & ACUMULO] ---")
    start_time = time.time()
    
    # IMPORTANTE: A engine espera o db_path como primeiro argumento
    results = engine.search_cnpj_by_name_cpf(db_path, name, cpf)
    
    end_time = time.time()
    duration = end_time - start_time
    
    print(f"\nBusca finalizada em {duration:.2f} segundos.")
    
    if not results.empty:
        print(f"Sucesso: {len(results)} registros encontrados.")
        print(results[['cnpj_basico', 'razao_social', 'cnpj_cpf_socio']])
        
        # Verificar se ambos os CNPJs básicos estão presentes
        expected = {'18528540', '38262186'}
        found = set(results['cnpj_basico'].astype(str))
        missed = expected - found
        
        if not missed:
            print("\n>>> SUCESSO TOTAL: Todos os registros esperados foram encontrados!")
        else:
            print(f"\n>>> FALHA: Registros não encontrados: {missed}")
    else:
        print("\n>>> FALHA: Nenhum registro encontrado.")

if __name__ == "__main__":
    test_engine_v15()
