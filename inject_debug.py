import paramiko

hostname = "86.48.17.194"
username = "root"
password = "^QP67kXax9AyuvF%"

def inject_debug():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname, username=username, password=password, timeout=10)
    
    script = r'''
file_path = "/var/www/hemn_cloud/index_vps.html"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

old = "if (card) { // offsetParent removed - always update"
new = """if (card) { // offsetParent removed - always update
                                    console.log(`[POLL DEBUG] task-${t.id} FOUND! Updating prog-${t.id} to ${t.progress}%`);
                                    const progEl = document.getElementById(`prog-${t.id}`);
                                    if (!progEl) console.error(`[POLL DEBUG] Element prog-${t.id} is null! innerHTML = `, card.innerHTML.substring(0, 100));"""

if old in content:
    content = content.replace(old, new)
    print("Debug logger injected.")
else:
    print("Debug target not found.")

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
'''
    
    sftp = client.open_sftp()
    with sftp.open('/tmp/inject_debug.py', 'w') as f:
        f.write(script)
    sftp.close()
    
    stdin, stdout, stderr = client.exec_command("python3 /tmp/inject_debug.py && systemctl restart hemn_cloud")
    print(stdout.read().decode().strip())
    client.close()

if __name__ == "__main__":
    inject_debug()
