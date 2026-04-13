import paramiko

def diagnose():
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        c.connect('86.48.17.194', username='root', password='^QP67kXax9AyuvF%')
        print("--- ÚLTIMAS 50 LINHAS DO LOG DO MOTOR ---")
        stdin, stdout, stderr = c.exec_command('tail -n 50 /var/www/hemn_cloud/cloud_engine_debug.log')
        print(stdout.read().decode())

        print("\n--- PROCESSOS PYTHON ATIVOS ---")
        stdin, stdout, stderr = c.exec_command('ps aux | grep python')
        print(stdout.read().decode())

        print("\n--- RECENT TASKS (TID a82cd8d6?) ---")
        stdin, stdout, stderr = c.exec_command('sqlite3 /var/www/hemn_cloud/hemn_cloud.db "SELECT id, status, message FROM background_tasks ORDER BY created_at DESC LIMIT 3"')
        print(stdout.read().decode())

        c.close()
    except Exception as e:
        print(f"Erro: {e}")

if __name__ == "__main__":
    diagnose()
