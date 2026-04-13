import paramiko

def final_report():
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        c.connect('86.48.17.194', username='root', password='^QP67kXax9AyuvF%')
        print("--- RELATÓRIO FINAL DE EXTRAÇÕES (VPS CONTABO) ---")
        
        # Check SQLite Tasks
        cmd = 'sqlite3 /var/www/hemn_cloud/hemn_cloud.db "SELECT id, status, progress, message, result_file FROM background_tasks WHERE module=\'EXTRACTION\' ORDER BY created_at DESC LIMIT 5"'
        stdin, stdout, stderr = c.exec_command(cmd)
        tasks = stdout.read().decode().strip().split('\n')
        
        print(f"{'ID':<15} | {'STATUS':<15} | {'PROG':<5} | {'ARQUIVO GERADO':<30}")
        print("-" * 80)
        for t in tasks:
            if not t: continue
            parts = t.split('|')
            short_id = parts[0][:15]
            status = parts[1]
            prog = parts[2]
            file = parts[4] if len(parts) > 4 else "N/A"
            print(f"{short_id:<15} | {status:<15} | {prog:<5}% | {file:<30}")

        print("\n--- TESTE DE CONECTIVIDADE CLICKHOUSE ---")
        stdin, stdout, stderr = c.exec_command('clickhouse-client -q "SELECT count() FROM hemn.estabelecimentos"')
        count = stdout.read().decode().strip()
        print(f"Total de registros na base: {count}")
        
        c.close()
    except Exception as e:
        print(f"Erro: {e}")

if __name__ == "__main__":
    final_report()
