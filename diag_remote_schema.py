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
    tables = ["hemn.socios", "hemn.estabelecimento", "hemn.empresas", "hemn.municipio"]
    for table in tables:
        print(f"\n--- {table} ---")
        out, err = run_remote_ch(f"DESCRIBE TABLE {table}")
        if out: print(out)
        if err: print(f"ERROR: {err}")
