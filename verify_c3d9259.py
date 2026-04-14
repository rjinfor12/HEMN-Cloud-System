import paramiko

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('86.48.17.194', username='root', password='^QP67kXax9AyuvF%', timeout=20)

# Check if recoverActiveTasks was in c3d9259
stdin, stdout, stderr = client.exec_command('cd /var/www/hemn_cloud && git show c3d9259:index_vps.html | grep -n "recoverActiveTasks\\|hemn_active_tasks" | head -20')
output = stdout.read().decode(errors='ignore')
print("=== COMMIT c3d9259 - recoverActiveTasks & localStorage ===")
print(output if output else "NOT FOUND")

# Check current HEAD
stdin, stdout, stderr = client.exec_command('cd /var/www/hemn_cloud && git log --oneline -1')
current = stdout.read().decode(errors='ignore').strip()
print(f"\n=== CURRENT DEPLOYED (HEAD) ===\n{current}")

# Check if current deployment has the recovery code
stdin, stdout, stderr = client.exec_command('grep -n "recoverActiveTasks\\|hemn_active_tasks" /var/www/hemn_cloud/index_vps.html | head -20')
output2 = stdout.read().decode(errors='ignore')
print("\n=== CURRENT DEPLOYED FILE - recoverActiveTasks & localStorage ===")
print(output2 if output2 else "NOT FOUND")

client.close()
