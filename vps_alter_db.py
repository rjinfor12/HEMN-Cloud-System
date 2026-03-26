import paramiko, os

host = '129.121.45.136'
port = 22022
user = 'root'
key_path = os.path.expanduser('~/.ssh/id_rsa')

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, port=port, username=user, key_filename=key_path)

# Comando para Adicionar Coluna
alter_cmd = 'sqlite3 /var/www/hemn_cloud/hemn_cloud.db "ALTER TABLE background_tasks ADD COLUMN hidden INTEGER DEFAULT 0"'

print("Altering table...")
stdin, stdout, stderr = client.exec_command(alter_cmd)
err = stderr.read().decode()
if "duplicate column name" in err:
    print("Column already exists.")
elif err:
    print(f"Error: {err}")
else:
    print("Column added successfully.")

client.close()
