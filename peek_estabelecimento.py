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
filename = "Estabelecimentos0.zip"
zip_path = f"/var/www/hemn_cloud/downloads/peek_{filename}"
url = f"https://arquivos.receitafederal.gov.br/public.php/dav/files/{share_token}/2026-03/{filename}"

print(f"--- PEEKING AT {filename} ---")

# 1. Download small chunk or full if small
print(f"Downloading {filename}...")
cmd = f'curl -u {share_token}: -L -o {zip_path} "{url}"'
# We don't need the whole file to peek, but curl doesn't easily download just the start of a zip for unzip.
# Let's hope it's not too slow.
stdin, stdout, stderr = client.exec_command(cmd)
stdout.read()
print("Download finished.")

# 2. Peek at first 2 lines
print("Peeking at contents (first 2 lines):")
cmd = f"unzip -p {zip_path} | head -n 2"
stdin, stdout, stderr = client.exec_command(cmd)
print(stdout.read().decode('utf-8', errors='replace'))

# 3. Count columns in first line
print("Counting columns in first line:")
cmd = f"unzip -p {zip_path} | head -n 1 | tr -cd ';' | wc -c"
stdin, stdout, stderr = client.exec_command(cmd)
# Number of semicolons + 1 = number of columns
sems = stdout.read().decode().strip()
if sems:
    print(f"Semicolons: {sems} -> Columns: {int(sems) + 1}")

client.close()
