import paramiko
import os

def check_schema():
    host = '86.48.17.194'
    user = 'root'
    pw = '^QP67kXax9AyuvF%'

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(host, username=user, password=pw)
        stdin, stdout, stderr = client.exec_command('clickhouse-client --query "SELECT count() FROM hemn.estabelecimento"')
        print(stdout.read().decode())
        client.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_schema()
