import paramiko, os

host = '129.121.45.136'
port = 22022
user = 'root'
key_path = os.path.expanduser('~/.ssh/id_rsa')

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, port=port, username=user, key_filename=key_path)

# SQL puro para swap atômico das 3 principais que movem o sistema
sql = """
RENAME TABLE 
  hemn.empresas TO hemn_backup_old.empresas_old, 
  hemn_update_tmp.empresas TO hemn.empresas,
  hemn.estabelecimento TO hemn_backup_old.estabelecimento_old,
  hemn_update_tmp.estabelecimento TO hemn.estabelecimento,
  hemn.socios TO hemn_backup_old.socios_old,
  hemn_update_tmp.socios TO hemn.socios;
"""

print("Creating swap_action.sql on VPS...")
sftp = client.open_sftp()
with sftp.open('/var/www/hemn_cloud/swap_action.sql', 'w') as f:
    f.write(sql)
sftp.close()

print("Executing swap_action.sql via clickhouse-client...")
cmd = 'clickhouse-client < /var/www/hemn_cloud/swap_action.sql'
stdin, stdout, stderr = client.exec_command(cmd)

out = stdout.read().decode().strip()
err = stderr.read().decode().strip()

if err:
    print(f"ERROR: {err}")
else:
    print("SUCCESS: Atomic Swap Completed!")
    # Update Metadata
    client.exec_command('clickhouse-client -q "INSERT INTO hemn._metadata (key, value) VALUES (\'db_version\', \'Março/2026 (Titanium)\') ON DUPLICATE KEY UPDATE value = \'Março/2026 (Titanium)\'"')


client.close()
