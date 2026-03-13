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

try:
    client = clickhouse_connect.get_client(host='localhost', port=8123, username='default', password='')
    
    # Simula filtros do usuário: CE, ATIVA
    where_clause = "estab.uf = 'CE' AND estab.situacao_cadastral = '02'"
    
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
        FROM hemn.empresas e
        JOIN (
            SELECT estab.*, m.descricao as CIDADE 
            FROM hemn.estabelecimento estab 
            LEFT JOIN hemn.municipio m ON estab.municipio = m.codigo 
            WHERE {where_clause} 
            LIMIT 10
        ) as estab ON e.cnpj_basico = estab.cnpj_basico
        SETTINGS join_algorithm = 'auto'
    '''
    
    print("--- EXECUTANDO QUERY DIAGNÓSTICA ---")
    res = client.query(q)
    df = pd.DataFrame(res.result_rows, columns=res.column_names)
    
    print("\nCOLUNAS DO DATAFRAME:")
    print(df.columns.tolist())
    
    print("\nPRIMEIRAS 3 LINHAS (HEAD):")
    print(df.head(3).to_string())
    
    print("\nCONTAGEM DE VALORES NULOS/VAZIOS:")
    print(df.isna().sum())
    
except Exception as e:
    print(f"Erro no diagnóstico: {e}")
"""

print('=== EXECUTANDO DIAGNÓSTICO NO VPS ===')
client.exec_command("cat << 'EOF' > /tmp/diag_blank_results.py\n" + diag_script + "\nEOF")
print(run("/var/www/hemn_cloud/venv/bin/python3 /tmp/diag_blank_results.py"))

client.close()
