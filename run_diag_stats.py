import paramiko, os

host = '129.121.45.136'
port = 22022
user = 'root'
key_path = os.path.expanduser('~/.ssh/id_rsa')

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, port=port, username=user, key_filename=key_path)

def run(cmd):
    stdin, stdout, stderr = client.exec_command(cmd)
    stdout.channel.recv_exit_status()
    return stdout.read().decode('utf-8', errors='replace') + stderr.read().decode('utf-8', errors='replace')

diag_script = r"""
import pandas as pd
import clickhouse_connect
import re

try:
    client = clickhouse_connect.get_client(host='localhost', port=8123, username='default', password='')
    
    # 1. COUNT PURE DATA
    print("--- 1. COUNTS ---")
    cnt_mei_ce = client.query("SELECT count() FROM hemn.estabelecimento estab JOIN hemn.empresas e ON estab.cnpj_basico = e.cnpj_basico WHERE estab.uf = 'CE' AND estab.situacao_cadastral = '02' AND e.natureza_juridica = '2135'").result_rows[0][0]
    print(f"Total MEI CE ATIVA (sem filtro tel): {cnt_mei_ce:,}")
    
    cnt_claro = client.query("SELECT count() FROM hemn.estabelecimento estab JOIN hemn.empresas e ON estab.cnpj_basico = e.cnpj_basico WHERE estab.uf = 'CE' AND estab.situacao_cadastral = '02' AND e.natureza_juridica = '2135' AND (estab.telefone1 != '' OR estab.telefone2 != '')").result_rows[0][0]
    print(f"Total MEI CE ATIVA (com qualquer tel): {cnt_claro:,}")

    # 2. RUN FULL LOGIC ON SAMPLE
    q = '''
        SELECT e.razao_social as NOME_DA_EMPRESA, 
               concat(estab.cnpj_basico, estab.cnpj_ordem, estab.cnpj_dv) as CNPJ, 
               estab.situacao_cadastral as SITUACAO_CADASTRAL,
               estab.cnae_fiscal as CNAE, 
               estab.logradouro as LOGRADOURO,
               estab.numero as NUMERO_DA_FAIXADA,
               estab.bairro as BAIRRO,
               estab.CIDADE, estab.uf as UF, estab.cep as CEP, 
               estab.ddd1, estab.telefone1, estab.ddd2, estab.telefone2 
        FROM (
            SELECT estab.*, m.descricao as CIDADE 
            FROM hemn.estabelecimento estab 
            LEFT JOIN hemn.municipio m ON estab.municipio = m.codigo 
            WHERE estab.uf = 'CE' AND estab.situacao_cadastral = '02'
            LIMIT 100
        ) as estab
        JOIN hemn.empresas e ON e.cnpj_basico = estab.cnpj_basico
        WHERE natureza_juridica = '2135'
        SETTINGS join_algorithm = 'auto'
    '''
    res = client.query(q)
    df = pd.DataFrame(res.result_rows, columns=res.column_names)
    
    print("\n--- 2. DATA INSPECTION (BEFORE TRANSFORM) ---")
    print(f"Rows found: {len(df)}")
    if not df.empty:
        print("Columns:", df.columns.tolist())
        print("Sample raw row:\n", df.iloc[0].to_dict())

        # Transform (select_phone)
        def select_phone(row):
            t1, t2 = row.get('telefone1', ''), row.get('telefone2', '')
            return t1 if t1 else t2
            
        df['TELEFONE SOLICITADO'] = df.apply(select_phone, axis=1)
        df['OPERADORA DO TELEFONE'] = "CLARO" # Simulated for test
        
        # Header Normalization
        print("\n--- 3. HEADER NORMALIZATION CHECK ---")
        orig_cols = df.columns.tolist()
        df.columns = [c.upper().replace('_', ' ') if ' ' not in c else c.upper() for c in df.columns]
        normalized_cols = df.columns.tolist()
        print("Original:", orig_cols)
        print("Normalized:", normalized_cols)
        
        final_mapping = {
            'SITUACAO CADASTRAL': 'SITUAÇÃO CADASTRAL',
            'NUMERO DA FAIXADA': 'NUMERO DA FAIXADA',
            'TELEFONE SOLICITADO': 'TELEFONE SOLICITADO',
            'OPERADORA DO TELEFONE': 'OPERADORA DO TELEFONE'
        }
        df = df.rename(columns=final_mapping)
        renamed_cols = df.columns.tolist()
        print("After Rename:", renamed_cols)
        
        final_columns = ['CNPJ', 'NOME DA EMPRESA', 'SITUAÇÃO CADASTRAL', 'CNAE', 'LOGRADOURO', 'NUMERO DA FAIXADA', 'BAIRRO', 'CIDADE', 'UF', 'CEP', 'TELEFONE SOLICITADO', 'OPERADORA DO TELEFONE']
        df_final = df[final_columns]
        print("Final head (records):\n", df_final.head(2).to_dict('records'))

except Exception as e:
    print(f"Erro: {e}")
"""

print('=== EXECUTANDO DIAGNÓSTICO ESTATÍSTICO NA VPS ===')
client.exec_command("cat << 'EOF' > /tmp/diag_stats.py\n" + diag_script + "\nEOF")
stdin, stdout, stderr = client.exec_command("/var/www/hemn_cloud/venv/bin/python3 /tmp/diag_stats.py")
print(stdout.read().decode('utf-8', errors='replace'))
print(stderr.read().decode('utf-8', errors='replace'))

client.close()
