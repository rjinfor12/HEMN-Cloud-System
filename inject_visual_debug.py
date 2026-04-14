import paramiko

hostname = "86.48.17.194"
username = "root"
password = "^QP67kXax9AyuvF%"

def inject_visual_debug():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname, username=username, password=password, timeout=10)
    
    script = r'''
file_path = "/var/www/hemn_cloud/index_vps.html"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Inject a visual debug panel at the bottom of the body
debug_panel = """
<div id="visual-debug" style="position:fixed; bottom:0; padding:10px; right:0; width:500px; height:200px; background:rgba(0,0,0,0.8); color:#0f0; z-index:999999; overflow-y:auto; font-family:monospace; font-size:11px;">
DEBUG INICIADO<br>
</div>
<script>
window.logDebug = function(msg) {
    const el = document.getElementById('visual-debug');
    if (el) {
        el.innerHTML += msg + '<br>';
        el.scrollTop = el.scrollHeight;
    }
}
</script>
</body>
"""

if '<div id="visual-debug"' not in content:
    content = content.replace("</body>", debug_panel)

# Now, we modify pollTasks to use logDebug
old_poll = """const card = document.getElementById(`task-${t.id}`);
                                if (!card) {"""
                                
new_poll = """const card = document.getElementById(`task-${t.id}`);
                                window.logDebug(`Polling [${t.id}] - Status API: ${data.status} | Prog: ${data.progress}% | hasCard: ${!!card}`);
                                if (card) {
                                  const pEl = document.getElementById(`prog-${t.id}`);
                                  window.logDebug(`  => Element prog-${t.id}: ${!!pEl}`);
                                }
                                if (!card) {"""

if 'window.logDebug(`Polling' not in content:
    content = content.replace(old_poll, new_poll)
    
with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
'''
    sftp = client.open_sftp()
    with sftp.open('/tmp/visual_debug.py', 'w') as f:
        f.write(script)
    sftp.close()
    
    stdin, stdout, stderr = client.exec_command("python3 /tmp/visual_debug.py")
    print(stdout.read().decode())
    client.close()

if __name__ == "__main__":
    inject_visual_debug()
