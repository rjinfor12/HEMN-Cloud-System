import paramiko, os

host = '129.121.45.136'
port = 22022
user = 'root'
key_path = os.path.expanduser('~/.ssh/id_rsa')

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, port=port, username=user, key_filename=key_path)

# Comando Robusto para adicionar ao Crontab (Toda segunda 00:00)
cron_line = "0 0 * * 1 /var/www/hemn_cloud/venv/bin/python /var/www/hemn_cloud/vps_check_receita_updates.py >> /var/www/hemn_cloud/receita_cron.log 2>&1"

setup_cmd = f"""
(crontab -l 2>/dev/null | grep -v "vps_check_receita_updates.py"; echo "{cron_line}") | crontab -
"""

print("Setting up Cron job...")
stdin, stdout, stderr = client.exec_command(setup_cmd)
print("Cron setup attempted.")

# Testar execução manual agora
print("Testing monitor script execution...")
stdin, stdout, stderr = client.exec_command('/var/www/hemn_cloud/venv/bin/python /var/www/hemn_cloud/vps_check_receita_updates.py')
print(f"OUTPUT: {stdout.read().decode()}")
print(f"ERROR: {stderr.read().decode()}")

client.close()
