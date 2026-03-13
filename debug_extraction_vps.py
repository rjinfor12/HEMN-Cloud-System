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

print('=== SIMULANDO EXTRACAO NO VPS PARA DEBUGAR DATAFRAME ===')
script = """
import clickhouse_connect
import pandas as pd
import os

client = clickhouse_connect.get_client(host='localhost', port=8123, username='default', password='')
# Usando o CNPJ do print como exemplo
where_clause = "estab.cnpj_basico = '54560969'"
q = f\"\"\"
    SELECT e.razao_social as NOME_DA_EMPRESA, 
           concat(estab.cnpj_basico, estab.cnpj_ordem, estab.cnpj_dv) as CNPJ, 
           estab.situacao_cadastral as SITUACAO_CADASTRAL,
           estab.cnae_fiscal as CNAE, 
           estab.logradouro as LOGRADOURO,
           estab.numero as NUMERO_DA_FAIXADA,
           estab.bairro as BAIRRO,
           estab.uf as UF, estab.cep as CEP, 
           estab.ddd1, estab.telefone1, estab.ddd2, estab.telefone2 
    FROM (
        SELECT estab.*
        FROM hemn.estabelecimento estab 
        WHERE {where_clause} 
        LIMIT 10
    ) as estab 
    JOIN hemn.empresas e ON estab.cnpj_basico = e.cnpj_basico 
\"\"\"

res = client.query(q)
df = pd.DataFrame(res.result_rows, columns=res.column_names)
print('--- DF APOS CLICKHOUSE ---')
print('Colunas:', df.columns.tolist())
print(df.head(1).to_string())

# Simulando o resto da logica de renames e colunas finais
df = df.rename(columns={
    'NOME_DA_EMPRESA': 'NOME DA EMPRESA',
    'SITUACAO_CADASTRAL': 'SITUAÇÃO CADASTRAL',
    'NUMERO_DA_FAIXADA': 'NUMERO DA FAIXADA'
})

final_columns = [
    'CNPJ', 'NOME DA EMPRESA', 'SITUAÇÃO CADASTRAL', 'CNAE', 
    'LOGRADOURO', 'NUMERO DA FAIXADA', 'BAIRRO', 'CEP', 'UF'
]

for c in final_columns:
    if c not in df.columns: 
        print(f'ALERTA: Coluna {c} nao encontrada, preenchendo com vazio')
        df[c] = ""

df = df[final_columns]
print('\\n--- DF FINAL ANTES DE SALVAR ---')
print(df.head(1).to_string())
"""

# Usando heredoc
client.exec_command("cat << 'EOF' > /tmp/debug_extraction.py\n" + script + "\nEOF")
print(run("/var/www/hemn_cloud/venv/bin/python3 /tmp/debug_extraction.py"))

client.close()
