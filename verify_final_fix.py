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
    
    # Simula a mesma query que o usuário fez
    estab_where = "estab_inner.uf = 'CE' AND estab_inner.situacao_cadastral = '02'"
    empresas_where = "natureza_juridica = '2135'"
    
    # Nova estrutura otimizada com aliases explicitos
    q = f'''
        SELECT 
            e.razao_social AS NOME_DA_EMPRESA, 
            CONCAT(estab.cnpj_basico, estab.cnpj_ordem, estab.cnpj_dv) AS CNPJ, 
            estab.situacao_cadastral AS SITUACAO_CADASTRAL,
            estab.cnae_fiscal AS CNAE, 
            estab.logradouro AS LOGRADOURO,
            estab.numero AS NUMERO_DA_FAIXADA,
            estab.bairro AS BAIRRO,
            estab.CIDADE AS CIDADE, 
            estab.uf AS UF, 
            estab.cep AS CEP
        FROM hemn.empresas e
        INNER JOIN (
            SELECT estab_inner.*, m.descricao as CIDADE 
            FROM hemn.estabelecimento estab_inner 
            LEFT JOIN hemn.municipio m ON estab_inner.municipio = m.codigo 
            WHERE {estab_where} 
            LIMIT 100
        ) AS estab ON e.cnpj_basico = estab.cnpj_basico
        WHERE {empresas_where}
        SETTINGS join_algorithm = 'auto'
    '''
    
    res = client.query(q)
    df = pd.DataFrame(res.result_rows, columns=res.column_names)
    
    print("Colunas retornadas:", df.columns.tolist())
    if not df.empty:
        print("PRIMEIRO REGISTRO:")
        print(df.iloc[0].to_dict())
        
        # Test mapping logic
        df.columns = [str(c).upper().replace('_', ' ') for c in df.columns]
        final_mapping = {
            'NOME DA EMPRESA': 'NOME DA EMPRESA',
            'SITUACAO CADASTRAL': 'SITUAÇÃO CADASTRAL',
            'NUMERO DA FAIXADA': 'NUMERO DA FAIXADA'
        }
        df = df.rename(columns=final_mapping)
        print("Colunas apos mapeamento:", df.columns.tolist())
        print("Valor NOME DA EMPRESA:", df['NOME DA EMPRESA'].iloc[0])
    else:
        print("Nenhum dado encontrado.")

except Exception as e:
    print(f"Erro: {e}")
"""

print('=== VALIDANDO FIX FINAL NA VPS ===')
client.exec_command("cat << 'EOF' > /tmp/diag_final_fix.py\n" + diag_script + "\nEOF")
stdin, stdout, stderr = client.exec_command("/var/www/hemn_cloud/venv/bin/python3 /tmp/diag_final_fix.py")
print(stdout.read().decode('utf-8', errors='replace'))
print(stderr.read().decode('utf-8', errors='replace'))

client.close()
