import paramiko, os

host = '129.121.45.136'
port = 22022
user = 'root'
key_path = os.path.expanduser('~/.ssh/id_rsa')

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, port=port, username=user, key_filename=key_path)

# Simulando extração real com CloudEngine - Corrigida Query
diag_script = r"""
import sys
import os
import pandas as pd
sys.path.append('/var/www/hemn_cloud')
from cloud_engine import CloudEngine

engine = CloudEngine()

tid = "FINAL_VAL"
output_file = "/tmp/final_validation.xlsx"
if os.path.exists(output_file): os.remove(output_file)

print("--- INICIANDO VALIDAÇÃO FINAL (FASE 5) ---")
try:
    # Query super simples para teste
    q = "SELECT razao_social as NOME, '0000' as CNPJ FROM hemn.empresas LIMIT 5"
    df = engine.ch_client.query_df(q)
    
    # Simular o mapping do código
    df.columns = [str(c).upper().replace('_', ' ').strip() for c in df.columns]
    df = df.rename(columns={'NOME': 'NOME DA EMPRESA'})
    
    print(f"Exportando {len(df)} linhas para {output_file}...")
    # Executando o EXATO bloco de exportação do servidor (Sem constante_memory)
    import xlsxwriter
    with pd.ExcelWriter(output_file, engine='xlsxwriter') as writer:
        for i in range(0, len(df), 200000):
            chunk = df.iloc[i : i + 200000]
            chunk.to_excel(writer, sheet_name=f"Lote_{(i//200000)+1}", index=False)
            
    # Lendo de volta para provar
    df_read = pd.read_excel(output_file)
    print("DADOS LIDOS DO EXCEL FINAL:")
    print(df_read.to_dict())
    
    if df_read['NOME DA EMPRESA'].isnull().any():
        print("FALHA: Nomes continuam vindo em branco!")
    else:
        print("SUCESSO TOTAL! Dados preservados.")
        
except Exception as e:
    print(f"ERRO NA VALIDAÇÃO: {e}")
"""

print('=== EXECUTANDO VALIDAÇÃO FINAL (V2) NA VPS ===')
client.exec_command("cat << 'EOF' > /tmp/verify_final.py\n" + diag_script + "\nEOF")
stdin, stdout, stderr = client.exec_command("/var/www/hemn_cloud/venv/bin/python3 /tmp/verify_final.py")
print(stdout.read().decode('utf-8', errors='replace'))
print(stderr.read().decode('utf-8', errors='replace'))

client.close()
