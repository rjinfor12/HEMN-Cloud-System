import clickhouse_connect
import pandas as pd
import glob
import os
import sys

# ClickHouse connection details - UPDATED FOR VPS
CH_HOST = '129.121.45.136'
CH_PORT = 8123
CH_USER = 'default'
CH_PASS = ''
CH_DB = 'hemn' # Standard database name

def get_ch_client():
    return clickhouse_connect.get_client(
        host=CH_HOST,
        port=CH_PORT,
        username=CH_USER,
        password=CH_PASS,
        database=CH_DB
    )

def main():
    csv_dir = r"C:\Users\Junior T.I\OneDrive\Área de Trabalho\csv"
    if not os.path.exists(csv_dir):
        print(f"Erro: Diretorio {csv_dir} nao encontrado.")
        return

    client = get_ch_client()
    
    # Check if table exists, if not create it
    print("Verificando/Criando tabela 'leads' no ClickHouse...")
    client.command("""
    CREATE TABLE IF NOT EXISTS leads (
        cpf String,
        nome String,
        dt_nascimento String,
        tel_fixo1 String,
        celular1 String,
        uf String,
        regiao String
    ) ENGINE = MergeTree()
    ORDER BY cpf
    """)

    # Recursive search to find CSVs in subdirectories
    csv_files = glob.glob(os.path.join(csv_dir, "**", "*.csv"), recursive=True)
    # Sort files to prioritize Pernambuco (PE) as per user request, and then others
    csv_files.sort(key=lambda x: (not "NORDESTE" in x, not "PE" in x, x))
    print(f"Encontrados {len(csv_files)} arquivos CSV (priorizando Nordeste/PE).")

    if not csv_files:
        print("Nenhum arquivo CSV encontrado no diretorio especificado.")
        return

    for f in csv_files:
        print(f"\n--- Iniciando processamento de: {os.path.basename(f)} ---")
        try:
            # Processamento em blocos (chunks) para lidar com arquivos gigantes (GBs)
            chunks = pd.read_csv(f, sep=None, engine='python', chunksize=100000, dtype=str)
            
            total_rows = 0
            for i, chunk in enumerate(chunks):
                # Limpeza basica de CPF
                if 'cpf' in chunk.columns:
                    # Garantir que seja string, remover não-dígitos e preencher com zeros à esquerda
                    chunk['cpf'] = chunk['cpf'].astype(str).str.replace(r'\D', '', regex=True).str.zfill(11)
                
                # Preencher nulos para compatibilidade com ClickHouse String
                chunk = chunk.fillna('')
                
                # Selecionar apenas colunas que existem na tabela ClickHouse para evitar erro
                # Se a planilha tiver colunas extras, elas serao ignoradas
                cols_to_insert = [c for c in chunk.columns if c in ['cpf', 'nome', 'dt_nascimento', 'tel_fixo1', 'celular1', 'uf', 'regiao']]
                
                if not cols_to_insert:
                    print(f"Alerta: Bloco {i} do arquivo {os.path.basename(f)} nao possui colunas validas para a tabela 'leads'.")
                    continue
                
                client.insert_df('leads', chunk[cols_to_insert])
                total_rows += len(chunk)
                print(f"  > Bloco {i+1} inserido ({total_rows:,} registros processados...)")
                
            print(f"Sucesso: {os.path.basename(f)} concluido com {total_rows:,} registros.")
        except Exception as e:
            print(f"Erro fatal ao processar {f}: {e}")

if __name__ == "__main__":
    main()
