import pandas as pd
import os
from consolidation_engine import ConsolidationEngine

db_path = r"C:\Users\Junior T.I\OneDrive\Área de Trabalho\cruzar\cnpj.db"

def verify_batch():
    print("Iniciando verificação da busca MASSIVA...")
    
    # Criar planilha de teste
    test_input = "teste_massivo.xlsx"
    test_output = "resultado_massivo.xlsx"
    
    data = {
        'NOME': ['rogerio elias do nascimento junior'],
        'CPF': ['09752279473']
    }
    df_test = pd.DataFrame(data)
    df_test.to_excel(test_input, index=False)
    print(f"Planilha de teste criada: {test_input}")
    
    engine = ConsolidationEngine(target_dir=".", output_file=test_output)
    
    print("\nExecutando busca massiva...")
    engine.search_cnpj_batch(db_path, test_input, 'NOME', 'CPF', test_output)
    
    if os.path.exists(test_output):
        df_res = pd.read_excel(test_output)
        print(f"\nBusca massiva concluída. Linhas geradas: {len(df_res)}")
        print(df_res[['NOME', 'RAZAO_SOCIAL', 'CNPJ', 'SITUACAO']])
        
        # Verificar se os 3 vínculos estão presentes
        cnpjs_encontrados = df_res['CNPJ'].astype(str).tolist()
        vinculos_esperados = ["18528540000108", "23573445000166", "38262186000120"]
        
        found_all = True
        for v in vinculos_esperados:
            if v not in cnpjs_encontrados:
                print(f"FALHA: Vínculo {v} não encontrado no lote.")
                found_all = False
        
        if found_all:
            print("\nSUCESSO TOTAL NO LOTE: Todos os 3 vínculos foram localizados na planilha de saída!")
    else:
        print("\nERRO: Planilha de saída não foi gerada.")

if __name__ == "__main__":
    verify_batch()
