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

def test_export(use_constant_memory):
    output_file = f'/tmp/test_export_{use_constant_memory}.xlsx'
    if os.path.exists(output_file): os.remove(output_file)

    # Simular DF com 10 linhas
    data = {
        'CNPJ': [f'100000000000{i:02d}' for i in range(10)],
        'NOME': [f'EMPRESA {i}' for i in range(10)],
        'VAL': [i * 10 for i in range(10)]
    }
    df = pd.DataFrame(data)

    print(f"\n--- TESTING use_constant_memory={use_constant_memory} ---")
    try:
        options = {'constant_memory': True} if use_constant_memory else {}
        with pd.ExcelWriter(output_file, engine='xlsxwriter', engine_kwargs={'options': options}) as writer:
            chunk_size = 5
            for i in range(0, len(df), chunk_size):
                chunk = df.iloc[i : i + chunk_size]
                chunk.to_excel(writer, sheet_name=f"Lote_{(i//chunk_size)+1}", index=False)
        
        # Lendo de volta (Lote 1)
        df_read = pd.read_excel(output_file, sheet_name='Lote_1')
        print("Lote 1 (Lido):")
        print(df_read.head(5).to_dict())
        
        if df_read['NOME'].isnull().any():
            print("!!! BUG DETECTADO: NaNs encontrados !!!")
        else:
            print("Sucesso: Dados preservados.")

    except Exception as e:
        print(f"ERRO NO TESTE: {e}")

test_export(True)
test_export(False)
"""

print('=== RODANDO TESTE COMPARATIVO CONSTANT_MEMORY NA VPS ===')
client.exec_command("cat << 'EOF' > /tmp/test_xlsx_bug_v2.py\n" + diag_script + "\nEOF")
stdin, stdout, stderr = client.exec_command("/var/www/hemn_cloud/venv/bin/python3 /tmp/test_xlsx_bug_v2.py")
print(stdout.read().decode('utf-8', errors='replace'))
print(stderr.read().decode('utf-8', errors='replace'))

client.close()
