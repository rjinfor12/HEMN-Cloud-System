import os
import pandas as pd
from cloud_engine import CloudEngine

def test_expansion():
    engine = CloudEngine()
    
    # Criar um arquivo dummy com um CNPJ conhecido (Não MEI)
    # Vou usar um CNPJ de exemplo que tenha sócios. 
    # Para o teste, vou usar um que eu saiba que existe ou apenas um aleatório para ver se a query não quebra.
    
    # Vamos tentar o CNPJ 00.000.000/0001-91 (Banco do Brasil - tem sócios/diretores?)
    # Ou melhor, vamos criar um dataframe com uma coluna 'CPF' contendo um CNPJ.
    
    test_file = '/tmp/test_input.xlsx'
    df = pd.DataFrame({
        'NOME': ['EMPRESA TESTE'],
        'CPF': ['00000000000191'] # Banco do Brasil
    })
    df.to_excel(test_file, index=False)
    
    output_dir = '/tmp/test_output'
    os.makedirs(output_dir, exist_ok=True)
    
    print("Iniciando enriquecimento de teste (NAO MEI)...")
    tid = engine.start_enrich(test_file, output_dir, 'NOME', 'CPF', perfil='NAO MEI')
    
    # Aguardar a thread (como é um teste simples, vou rodar o método privado síncronamente)
    engine._run_enrich(tid, test_file, output_dir, 'NOME', 'CPF', perfil='NAO MEI')
    
    # Verificar resultado
    status = engine.get_task_status(tid)
    print(f"Status: {status['status']}")
    print(f"Mensagem: {status['message']}")
    
    if status['status'] == 'COMPLETED':
        res_file = status['result_file']
        df_res = pd.read_excel(res_file)
        print(f"Colunas: {df_res.columns.tolist()}")
        print(f"Linhas encontradas: {len(df_res)}")
        if 'CHAVE DO SOCIO' in df_res.columns:
            print("Coluna CHAVE DO SOCIO presente!")
            print("Exemplos de Chave:")
            print(df_res['CHAVE DO SOCIO'].head().tolist())
        else:
            print("ERRO: Coluna CHAVE DO SOCIO não encontrada.")
    else:
        print("ERRO: Task falhou.")

if __name__ == "__main__":
    test_expansion()
