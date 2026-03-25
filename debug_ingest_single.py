import paramiko
import os

host = '129.121.45.136'
port = 22022
user = 'root'
key_path = os.path.expanduser('~/.ssh/id_rsa')

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, port=port, username=user, key_filename=key_path)

share_token = "YggdBLfdninEJX9"
filename = "Empresas0.zip"
zip_path = f"/var/www/hemn_cloud/downloads/debug_{filename}"
url = f"https://arquivos.receitafederal.gov.br/public.php/dav/files/{share_token}/2026-03/{filename}"

print(f"--- DEBUGGING INGESTION OF {filename} ---")

# 1. Download
print(f"Downloading {filename}...")
cmd = f'curl -u {share_token}: -L -o {zip_path} "{url}"'
stdin, stdout, stderr = client.exec_command(cmd)
stdout.read() # wait
print("Download finished.")

# 2. Check zip
print("Checking zip content...")
cmd = f"unzip -l {zip_path}"
stdin, stdout, stderr = client.exec_command(cmd)
print(stdout.read().decode())

# 3. Try ingest
print("Trying ingestion...")
table = "hemn_update_tmp.empresas"
pipe_cmd = f'unzip -p {zip_path} | clickhouse-client --format_csv_delimiter ";" -q "INSERT INTO {table} FORMAT CSV"'
stdin, stdout, stderr = client.exec_command(pipe_cmd)
err = stderr.read().decode()
out = stdout.read().decode()
if err:
    print("INGESTION ERROR:", err)
else:
    print("Ingestion stdout:", out)

# 4. Check count
cmd = f"clickhouse-client -q 'SELECT count() FROM {table}'"
stdin, stdout, stderr = client.exec_command(cmd)
print("Row count after test:", stdout.read().decode().strip())

client.close()
