import paramiko
import os

host = '129.121.45.136'
port = 22022
user = 'root'
key_path = os.path.expanduser('~/.ssh/id_rsa')

def run_remote_ch(command):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(host, port=port, username=user, key_filename=key_path)
        ch_cmd = f'clickhouse-client -q "{command}"'
        stdin, stdout, stderr = client.exec_command(ch_cmd)
        out = stdout.read().decode().strip()
        err = stderr.read().decode().strip()
        client.close()
        return out, err
    except Exception as e:
        return None, str(e)

if __name__ == "__main__":
    print("--- CHECKING FARMA POPULAR (10890651) ---")
    query_p = "SELECT nome_socio, cnpj_cpf_socio FROM hemn.socios WHERE cnpj_basico = '10890651'"
    out_p, _ = run_remote_ch(query_p)
    print("\nPartners:")
    print(out_p if out_p else "None")
    
    query_e = "SELECT razao_social, natureza_juridica FROM hemn.empresas WHERE cnpj_basico = '10890651'"
    out_e, _ = run_remote_ch(query_e)
    print("\nCompany Info:")
    print(out_e if out_e else "None")
