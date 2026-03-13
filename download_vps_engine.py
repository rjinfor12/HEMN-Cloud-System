import paramiko, os

host = '129.121.45.136'
port = 22022
user = 'root'
key_path = os.path.expanduser('~/.ssh/id_rsa')

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, port=port, username=user, key_filename=key_path)

sftp = client.open_sftp()
# Baixar o arquivo atual do VPS para a pasta de análise
sftp.get('/var/www/hemn_cloud/cloud_engine.py', 'c:\\Users\\Junior T.I\\.gemini\\antigravity\\scratch\\data_analysis\\cloud_engine_vps.py')
sftp.close()
client.close()

print('Arquivo cloud_engine_vps.py baixado com sucesso.')
