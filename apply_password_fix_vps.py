import paramiko, os

host = '129.121.45.136'
port = 22022
user = 'root'
key_path = os.path.expanduser('~/.ssh/id_rsa')

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, port=port, username=user, key_filename=key_path)

def run(cmd):
    stdin, stdout, stderr = client.exec_command(cmd)
    stdout.channel.recv_exit_status()
    return stdout.read().decode('utf-8', errors='replace') + stderr.read().decode('utf-8', errors='replace')

# 1. Update HEMN_Cloud_Server_VPS.py
# Adding PasswordChangeRequest model and endpoint
server_file = "/var/www/hemn_cloud/HEMN_Cloud_Server.py"

# Add model
model_code = """
class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str
    confirm_password: str
"""

# Add endpoint
endpoint_code = """
@app.post("/user/change-password")
async def change_password(req: PasswordChangeRequest, user: dict = Depends(get_current_user)):
    if req.new_password != req.confirm_password:
        raise HTTPException(status_code=400, detail="A nova senha e a confirmação não coincidem.")
    
    if len(req.new_password) < 4:
        raise HTTPException(status_code=400, detail="A nova senha deve ter pelo menos 4 caracteres.")

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    # Verify current password
    db_user = conn.execute("SELECT * FROM users WHERE username = ? AND password = ?", (user["username"], req.current_password)).fetchone()
    if not db_user:
        conn.close()
        raise HTTPException(status_code=401, detail="Senha atual incorreta.")
    
    # Update password
    conn.execute("UPDATE users SET password = ? WHERE username = ?", (req.new_password, user["username"]))
    conn.commit()
    conn.close()
    return {"status": "success", "message": "Senha alterada com sucesso."}
"""

# We'll use a temporary python script on the VPS to safely inject these
update_script = f"""
import os

file_path = "{server_file}"
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Insert model after LeadSearchRequest
if 'class LeadSearchRequest' in content and 'class PasswordChangeRequest' not in content:
    content = content.replace('class LeadSearchRequest(BaseModel):', '{model_code}\\nclass LeadSearchRequest(BaseModel):')

# Insert endpoint before @app.get("/me")
if '@app.get("/me")' in content and '"/user/change-password"' not in content:
    content = content.replace('@app.get("/me")', '{endpoint_code}\\n@app.get("/me")')

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
"""

print("Injecting backend changes...")
run(f"python3 -c '{update_script}'")

# 2. Update index_vps.html
# We'll add the button in sidebar and the modal
index_file = "/var/www/hemn_cloud/index_vps.html"

# Sidebar button (before logout button)
sidebar_btn = """
                <button class="icon-btn" onclick="app.openPasswordModal()" title="Alterar Senha"
                    style="margin-left: auto; margin-right: 10px; border:none; background:transparent">
                    <i class="fas fa-lock"></i>
                </button>
"""

# Modal HTML (add before last </div> or similar)
modal_html = """
        <!-- PASSWORD MODAL -->
        <div id="password-modal" class="modal-overlay" style="display:none; position: fixed; inset: 0; background: rgba(0,0,0,0.8); z-index: 9000; align-items: center; justify-content: center; backdrop-filter: blur(10px);">
            <div class="glass-card" style="width: 400px; padding: 30px; position: relative; animation: zoomIn 0.3s ease-out; border: 1px solid var(--border-focus);">
                <div style="text-align: center; margin-bottom: 25px;">
                    <div style="width: 60px; height: 60px; background: var(--accent-gradient); border-radius: 50%; display: flex; align-items: center; justify-content: center; margin: 0 auto 15px; box-shadow: 0 10px 20px rgba(0,0,0,0.3);">
                        <i class="fas fa-key" style="font-size: 24px; color: white;"></i>
                    </div>
                    <h2 style="font-size: 20px; font-weight: 700;">Alterar Senha</h2>
                    <p style="font-size: 13px; color: var(--text-3); margin-top: 5px;">Mantenha sua conta segura</p>
                </div>

                <div class="form-group" style="margin-bottom: 15px;">
                    <label style="display: block; font-size: 11px; font-weight: 600; text-transform: uppercase; margin-bottom: 8px; color: var(--text-2); letter-spacing: 0.5px;">Senha Atual</label>
                    <input type="password" id="current-pass" class="form-control" placeholder="••••••••">
                </div>
                <div class="form-group" style="margin-bottom: 15px;">
                    <label style="display: block; font-size: 11px; font-weight: 600; text-transform: uppercase; margin-bottom: 8px; color: var(--text-2); letter-spacing: 0.5px;">Nova Senha</label>
                    <input type="password" id="new-pass" class="form-control" placeholder="Mínimo 4 caracteres">
                </div>
                <div class="form-group" style="margin-bottom: 25px;">
                    <label style="display: block; font-size: 11px; font-weight: 600; text-transform: uppercase; margin-bottom: 8px; color: var(--text-2); letter-spacing: 0.5px;">Confirmar Nova Senha</label>
                    <input type="password" id="confirm-pass" class="form-control" placeholder="Repita a nova senha">
                </div>

                <div style="display: flex; gap: 10px;">
                    <button class="btn-cancel" onclick="app.closePasswordModal()" style="flex: 1; padding: 12px; border-radius: 12px; border: 1px solid var(--border); background: transparent; color: var(--text-2); font-weight: 600; cursor: pointer;">Cancelar</button>
                    <button class="btn-primary" onclick="app.submitPasswordChange()" style="flex: 1; padding: 12px; border-radius: 12px; background: var(--accent-gradient); color: white; font-weight: 700; border: none; cursor: pointer; box-shadow: 0 4px 15px var(--accent-shadow);">Salvar</button>
                </div>
            </div>
        </div>
"""

# JS Logic (append to app object)
js_logic = """
            openPasswordModal: function() {
                document.getElementById('password-modal').style.display = 'flex';
                document.getElementById('current-pass').value = '';
                document.getElementById('new-pass').value = '';
                document.getElementById('confirm-pass').value = '';
            },
            closePasswordModal: function() {
                document.getElementById('password-modal').style.display = 'none';
            },
            submitPasswordChange: function() {
                const current = document.getElementById('current-pass').value;
                const next = document.getElementById('new-pass').value;
                const confirm = document.getElementById('confirm-pass').value;

                if (!current || !next || !confirm) {
                    app.showNotification('Aviso', 'Preencha todos os campos.', 'warning');
                    return;
                }
                if (next !== confirm) {
                    app.showNotification('Erro', 'As novas senhas não coincidem.', 'error');
                    return;
                }
                if (next.length < 4) {
                    app.showNotification('Erro', 'A nova senha deve ter pelo menos 4 caracteres.', 'error');
                    return;
                }

                app.showLoader();
                fetch(API + '/user/change-password', {
                    method: 'POST',
                    headers: { 
                        'Content-Type': 'application/json',
                        'Authorization': 'Bearer ' + localStorage.getItem('hemn_token')
                    },
                    body: JSON.stringify({
                        current_password: current,
                        new_password: next,
                        confirm_password: confirm
                    })
                })
                .then(res => res.json())
                .then(data => {
                    app.hideLoader();
                    if (data.status === 'success') {
                        app.showNotification('Sucesso', 'Senha alterada com sucesso!', 'success');
                        app.closePasswordModal();
                    } else {
                        app.showNotification('Erro', data.detail || 'Falha ao alterar senha', 'error');
                    }
                })
                .catch(err => {
                    app.hideLoader();
                    app.showNotification('Erro', 'Falha na conexão com o servidor', 'error');
                });
            },
"""

update_index_script = f"""
import os

file_path = "{index_file}"
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Insert button
if 'onclick="app.logout()"' in content and 'app.openPasswordModal()' not in content:
    content = content.replace('<button class="icon-btn" onclick="app.logout()"', '{sidebar_btn}<button class="icon-btn" onclick="app.logout()"')

# Insert Modal (before end of page-container or main app div)
if '<!-- Page Container -->' in content and 'id="password-modal"' not in content:
    content = content.replace('<!-- Page Container -->', '{modal_html}\\n<!-- Page Container -->')

# Insert JS logic (inside app object, after refreshUser or another method)
if 'refreshUser: function' in content and 'openPasswordModal: function' not in content:
    content = content.replace('refreshUser: function', '{js_logic}\\n            refreshUser: function')

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
"""

print("Injecting UI changes...")
run(f"python3 -c '{update_index_script}'")

# 3. Restart Service
print("Restarting service...")
run("systemctl restart hemn_cloud")

print("Backend and UI updated successfully!")
client.close()
