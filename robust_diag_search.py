import paramiko
import os

HOST = '129.121.45.136'
PORT = 22022
USER = 'root'
KEY_PATH = os.path.expanduser('~/.ssh/id_rsa')

def run_diagnostics():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(HOST, port=PORT, username=USER, key_filename=KEY_PATH)
        
        script_content = """
import subprocess

def run_q(q):
    cmd = ['clickhouse-client', '--query', q]
    res = subprocess.run(cmd, capture_output=True, text=True)
    return res.stdout

queries = [
    "SELECT nome_socio, cnpj_cpf_socio, cnpj_basico FROM hemn.socios WHERE upper(nome_socio) LIKE '%ROGERIO%ELIAS%' LIMIT 50",
    "SELECT razao_social, cnpj_basico FROM hemn.empresas WHERE upper(razao_social) LIKE '%ROGERIO%ELIAS%' LIMIT 50",
    "SELECT nome_socio, cnpj_cpf_socio, cnpj_basico FROM hemn.socios WHERE cnpj_cpf_socio LIKE '%522794%' LIMIT 50"
]

with open('/tmp/diag_result_v2.txt', 'w') as f:
    for q in queries:
        f.write(f'--- QUERY: {q} ---\\n')
        f.write(run_q(q))
        f.write('\\n\\n')
"""
        # Upload script
        sftp = client.open_sftp()
        with sftp.open('/tmp/remote_diag.py', 'w') as f:
            f.write(script_content)
        
        # Run script
        stdin, stdout, stderr = client.exec_command('python3 /tmp/remote_diag.py')
        stdout.read()
        
        # Download result
        sftp.get('/tmp/diag_result_v2.txt', 'diag_result_v2.txt')
        sftp.close()
        print("Downloaded results to diag_result_v2.txt")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    run_diagnostics()
