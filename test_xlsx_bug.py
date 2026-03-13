import paramiko, os

host = '129.121.45.136'
port = 22022
user = 'root'
key_path = os.path.expanduser('~/.ssh/id_rsa')

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, port=port, username=user, key_filename=key_path)

diag_script = r"""
import pandas as pd
import os
import xlsxwriter

output_file = '/tmp/test_bug.xlsx'
if os.path.exists(output_file): os.remove(output_file)

# Simular DF com dados
data = {
    'CNPJ': ['12345678000199', '98765432000111'],
    'NOME DA EMPRESA': ['EMPRESA TESTE A', 'EMPRESA TESTE B'],
    'SITUACAO CADASTRAL': ['ATIVA', 'ATIVA']
}
df = pd.DataFrame(data)

print("--- TESTING XLSXWRITER EXPORT LÓGICA ---")
try:
    # Usando EXATAMENTE a mesma lógica do servidor
    with pd.ExcelWriter(output_file, engine='xlsxwriter', engine_kwargs={'options': {'constant_memory': True}}) as writer:
        chunk_size = 200000
        for i in range(0, len(df), chunk_size):
            chunk = df.iloc[i : i + chunk_size]
            chunk.to_excel(writer, sheet_name=f"Lote_{(i//chunk_size)+1}", index=False)
    
    print(f"XLSX gerado em: {output_file}")
    
    # Lendo de volta
    df_read = pd.read_excel(output_file)
    print("DADOS LIDOS DO XLSX:")
    print(df_read.to_dict())
    
    if df_read['NOME DA EMPRESA'].isnull().any():
        print("!!! BUG REPRODUZIDO: Nomes vieram como NaN !!!")
    else:
        print("Sucesso: Nomes vieram OK.")

except Exception as e:
    print(f"ERRO NO TESTE: {e}")
"""

print('=== RODANDO TESTE DE REPRODUÇÃO DO BUG XLSX NA VPS ===')
client.exec_command("cat << 'EOF' > /tmp/test_xlsx_bug.py\n" + diag_script + "\nEOF")
stdin, stdout, stderr = client.exec_command("/var/www/hemn_cloud/venv/bin/python3 /tmp/test_xlsx_bug.py")
print(stdout.read().decode('utf-8', errors='replace'))
print(stderr.read().decode('utf-8', errors='replace'))

client.close()
