import paramiko, os

host = '129.121.45.136'
port = 22022
user = 'root'
key_path = os.path.expanduser('~/.ssh/id_rsa')

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, port=port, username=user, key_filename=key_path)

sftp = client.open_sftp()
# Enviar o arquivo corrigido de volta para o VPS
sftp.put('c:\\Users\\Junior T.I\\.gemini\\antigravity\\scratch\\data_analysis\\cloud_engine_vps.py', '/var/www/hemn_cloud/cloud_engine.py')
sftp.close()

def run(cmd):
    stdin, stdout, stderr = client.exec_command(cmd)
    stdout.channel.recv_exit_status()
    out = stdout.read().decode('utf-8', errors='replace')
    err = stderr.read().decode('utf-8', errors='replace')
    return out + err

print('=== REINICIANDO SERVICO NO VPS ===')
print(run("systemctl restart hemn_cloud.service"))

client.close()
print('Upload e reinicialização concluídos com sucesso.')
