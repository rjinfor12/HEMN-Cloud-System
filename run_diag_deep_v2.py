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

print('=== ÚLTIMOS LOGS DO SERVIÇO ===')
print(run("journalctl -u hemn_cloud.service -n 50"))

diag_script = r"""
import pandas as pd
import clickhouse_connect
import re

try:
    client = clickhouse_connect.get_client(host='localhost', port=8123, username='default', password='')
    
    # Simula a mesma query da tarefa 72be2375
    estab_where = "estab.uf = 'CE' AND estab.situacao_cadastral = '02'"
    empresas_where = "natureza_juridica = '2135'"
    
    q = f'''
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
            WHERE {estab_where} 
            LIMIT 10
        ) as estab
        JOIN hemn.empresas e ON e.cnpj_basico = estab.cnpj_basico
        WHERE {empresas_where}
        SETTINGS join_algorithm = 'auto'
    '''
    
    res = client.query(q)
    df = pd.DataFrame(res.result_rows, columns=res.column_names)
    
    print("DEBUG: Colunas retornadas pelo ClickHouse:", df.columns.tolist())
    print("DEBUG: Primeira linha bruta:", df.iloc[0].to_dict())

    # Passo 784-786 (Simulado)
    df['TELEFONE SOLICITADO'] = df['telefone1']
    df['OPERADORA DO TELEFONE'] = "TEST_OP"
    
    # Passo 795 (SIT_MAP)
    sit_map = {'01':'NULA','02':'ATIVA','03':'SUSPENSA','04':'INAPTA','08':'BAIXADA'}
    if 'SITUACAO_CADASTRAL' in df.columns:
        df['SITUACAO_CADASTRAL'] = df['SITUACAO_CADASTRAL'].astype(str).str.zfill(2).map(sit_map).fillna(df['SITUACAO_CADASTRAL'])

    # Passo 809 (Normalização)
    before_norm = df.columns.tolist()
    df.columns = [c.upper().replace('_', ' ') if ' ' not in c else c.upper() for c in df.columns]
    after_norm = df.columns.tolist()
    print("DEBUG: Colunas antes norm:", before_norm)
    print("DEBUG: Colunas após norm:", after_norm)

    # Passo 811-819 (Rename)
    final_mapping = {
        'SITUACAO CADASTRAL': 'SITUAÇÃO CADASTRAL',
        'NUMERO DA FAIXADA': 'NUMERO DA FAIXADA'
    }
    df = df.rename(columns=final_mapping)
    print("DEBUG: Colunas após rename:", df.columns.tolist())

    # Passo 821-825 (Selection)
    final_columns = ['CNPJ', 'NOME DA EMPRESA', 'SITUAÇÃO CADASTRAL', 'CNAE', 'LOGRADOURO', 'NUMERO DA FAIXADA', 'BAIRRO', 'CIDADE', 'UF', 'CEP', 'TELEFONE SOLICITADO', 'OPERADORA DO TELEFONE']
    
    missing = [c for c in final_columns if c not in df.columns]
    print("DEBUG: Colunas faltando:", missing)
    
    for c in final_columns:
        if c not in df.columns: df[c] = ""
    
    df_final = df[final_columns]
    print("DEBUG: Dataframe final head:\n", df_final.head(1).to_dict('records'))

except Exception as e:
    print(f"Erro: {e}")
"""

print('=== EXECUTANDO DIAGNÓSTICO PROFUNDO NA VPS ===')
client.exec_command("cat << 'EOF' > /tmp/diag_deep_v2.py\n" + diag_script + "\nEOF")
stdin, stdout, stderr = client.exec_command("/var/www/hemn_cloud/venv/bin/python3 /tmp/diag_deep_v2.py")
print(stdout.read().decode('utf-8', errors='replace'))
print(stderr.read().decode('utf-8', errors='replace'))

client.close()
