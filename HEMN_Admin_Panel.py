import customtkinter as ctk
import requests
import json
import os
import subprocess
import sys
import time
from tkinter import messagebox
from datetime import datetime
from tkcalendar import Calendar

# Configurações do Servidor
CLOUD_URL = "http://localhost:8000"

class AdminPanel(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("HEMN SYSTEM - ADMIN CONTROL PANEL v1.0")
        self.geometry("1000x850")
        ctk.set_appearance_mode("dark")
        
        # Cores Premium
        self.color_bg = "#0f0f12"
        self.color_card = "#1a1a20"
        self.color_accent = "#d4af37" # Gold
        self.color_danger = "#ff4a4a"
        self.color_text = "#ffffff"
        
        self.configure(fg_color=self.color_bg)
        
        # Layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        self.create_header()
        self.create_main_content()
        
        self.refresh_list()

    def create_header(self):
        header = ctk.CTkFrame(self, fg_color=self.color_card, height=80, corner_radius=0)
        header.grid(row=0, column=0, sticky="ew")
        
        lbl_title = ctk.CTkLabel(header, text="GESTÃO DE CLIENTES & COMANDO REMOTO", 
                                font=ctk.CTkFont(size=22, weight="bold"), text_color=self.color_accent)
        lbl_title.pack(side="left", padx=30, pady=20)
        
        btn_refresh = ctk.CTkButton(header, text="ATUALIZAR LISTA", fg_color="transparent", 
                                   border_width=1, border_color=self.color_accent, 
                                   command=self.refresh_list)
        btn_refresh.pack(side="right", padx=10)

        btn_restart = ctk.CTkButton(header, text="REINICIAR SERVIDOR", fg_color=self.color_danger, 
                                   text_color="white", font=ctk.CTkFont(weight="bold"),
                                   command=self.restart_server)
        btn_restart.pack(side="right", padx=20)

    def create_main_content(self):
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.grid(row=1, column=0, sticky="nsew", padx=30, pady=20)
        container.grid_columnconfigure(0, weight=3)
        container.grid_columnconfigure(1, weight=1)
        container.grid_rowconfigure(0, weight=1)
        
        # --- TABELA DE CLIENTES ---
        self.list_frame = ctk.CTkScrollableFrame(container, fg_color=self.color_card, label_text="Clientes Ativos na Nuvem")
        self.list_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 20))
        
        # --- PAINEL DE AÇÕES ---
        actions_frame = ctk.CTkFrame(container, fg_color=self.color_card)
        actions_frame.grid(row=0, column=1, sticky="nsew")
        
        lbl_act = ctk.CTkLabel(actions_frame, text="Novo Cliente / Vinculação", font=ctk.CTkFont(size=16, weight="bold"))
        lbl_act.pack(pady=20)
        
        self.ent_name = self.add_entry(actions_frame, "Nome do Cliente")
        self.ent_hwid = self.add_entry(actions_frame, "HWID (Copiado do App)")
        
        lbl_exp = ctk.CTkLabel(actions_frame, text="Data de Expiração:", font=ctk.CTkFont(size=12))
        lbl_exp.pack(pady=(10, 0))
        
        # Calendário Fixo
        self.calendar = Calendar(actions_frame, selectmode='day',
                                year=datetime.now().year, month=datetime.now().month, day=datetime.now().day,
                                background="#1a1a20", foreground="white", 
                                bordercolor="#d4af37", headersbackground="#d4af37",
                                headersforeground="black", selectbackground="#d4af37",
                                selectforeground="black", date_pattern='yyyy-mm-dd')
        self.calendar.pack(pady=10, padx=20, fill="x")
        
        self.ent_limit = self.add_entry(actions_frame, "Limite de Créditos")
        self.ent_limit.insert(0, "1000")
        
        btn_add = ctk.CTkButton(actions_frame, text="SINCRONIZAR HWID", fg_color=self.color_accent, 
                               text_color="black", font=ctk.CTkFont(weight="bold"), 
                               command=self.add_client)
        btn_add.pack(pady=20, padx=20, fill="x")
        
        ctk.CTkLabel(actions_frame, text="Status do Servidor:", font=ctk.CTkFont(size=12)).pack(pady=(20, 0))
        self.lbl_server = ctk.CTkLabel(actions_frame, text="● ONLINE", text_color="#00d26a", font=ctk.CTkFont(weight="bold"))
        self.lbl_server.pack()

    def add_entry(self, parent, placeholder):
        e = ctk.CTkEntry(parent, placeholder_text=placeholder, height=40, fg_color="#252530", border_width=0)
        e.pack(pady=10, padx=20, fill="x")
        return e

    def refresh_list(self):
        # Limpar lista
        for widget in self.list_frame.winfo_children():
            widget.destroy()
            
        try:
            response = requests.get(f"{CLOUD_URL}/admin/list", timeout=5)
            if response.status_code == 200:
                clients = response.json()
                for c in clients:
                    self.create_client_row(c)
                self.lbl_server.configure(text="● ONLINE", text_color="#00d26a")
            else:
                messagebox.showerror("Erro", "Não foi possível obter a lista do servidor.")
        except:
            self.lbl_server.configure(text="● OFFLINE", text_color=self.color_danger)
            messagebox.showwarning("Aviso", "Servidor Nuvem Offline. Inicie o HEMN_Cloud_Server.py primeiro.")

    def create_client_row(self, data):
        row = ctk.CTkFrame(self.list_frame, fg_color="#252530", height=60)
        row.pack(fill="x", pady=5, padx=5)
        
        status_color = "#00d26a" if data['status'] == "ACTIVE" else self.color_danger
        
        info = f"{data['name']} | HWID: {data['hwid']}\n" \
               f"Exp: {data['expiration']} | Créditos: {data['usage']:.2f} / {data['limit']:.2f}\n" \
               f"Visto em: {data['last_seen'][:16] if data['last_seen'] else 'Nunca'}"
        lbl = ctk.CTkLabel(row, text=info, justify="left", font=ctk.CTkFont(size=11))
        lbl.pack(side="left", padx=15, pady=10)
        
        # Botão KILL SWITCH
        btn_text = "REVOGAR" if data['status'] == "ACTIVE" else "REATIVAR"
        btn_color = self.color_danger if data['status'] == "ACTIVE" else "#00d26a"
        
        btn_kill = ctk.CTkButton(row, text=btn_text, width=80, height=30, fg_color=btn_color,
                                command=lambda h=data['hwid'], s=data['status']: self.toggle_status(h, s))
        btn_kill.pack(side="right", padx=15)

    def toggle_status(self, hwid, current_status):
        new_status = "REVOKED" if current_status == "ACTIVE" else "ACTIVE"
        confirm = messagebox.askyesno("Confirmar", f"Deseja alterar o status do HWID {hwid} para {new_status}?")
        if not confirm: return
        
        try:
            res = requests.post(f"{CLOUD_URL}/admin/command", json={"hwid": hwid, "new_status": new_status})
            if res.status_code == 200:
                messagebox.showinfo("Sucesso", f"Comando enviado! O acesso foi {new_status.lower()}.")
                self.refresh_list()
            else:
                messagebox.showerror("Erro", "Falha ao enviar comando.")
        except:
            messagebox.showerror("Erro", "Servidor inacessível.")

    def restart_server(self):
        confirm = messagebox.askyesno("Confirmar", "Deseja reiniciar o Servidor Cloud?\nIsso fechará a instância atual e abrirá uma nova.")
        if not confirm: return
        
        try:
            # 1. Tentar derrubar qualquer coisa na porta 8000 (Windows)
            # Find PID using port 8000
            cmd_find = 'netstat -ano | findstr :8000'
            output = subprocess.check_output(cmd_find, shell=True).decode()
            for line in output.strip().split('\n'):
                if 'LISTENING' in line:
                    pid = line.strip().split()[-1]
                    subprocess.run(f'taskkill /F /PID {pid}', shell=True, capture_output=True)
            
            time.sleep(1) # Esperar porta liberar
        except:
            # Se não encontrou nada na porta, segue o jogo
            pass

        try:
            # 2. Iniciar o servidor em novo console
            server_script = os.path.join(os.path.dirname(__file__), "HEMN_Cloud_Server.py")
            if not os.path.exists(server_script):
                messagebox.showerror("Erro", f"Script do servidor não encontrado:\n{server_script}")
                return
                
            subprocess.Popen([sys.executable, server_script], creationflags=subprocess.CREATE_NEW_CONSOLE)
            messagebox.showinfo("Sucesso", "Comando de reinicialização enviado!\nUma nova janela de console deve ter sido aberta.")
            
            # Pequeno delay e atualiza o status
            self.after(2000, self.refresh_list)
            
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao iniciar servidor: {e}")

    def add_client(self):
        name = self.ent_name.get()
        hwid = self.ent_hwid.get()
        # Obter data do calendário fixo
        exp = self.calendar.get_date()
        
        if not name or not hwid:
            messagebox.showwarning("Erro", "Nome e HWID são obrigatórios.")
            return
            
        try:
            limit = float(self.ent_limit.get() or 1000)
            payload = {"hwid": hwid, "status": "ACTIVE", "expiration": exp, "total_limit": limit}
            res = requests.post(f"{CLOUD_URL}/admin/register?name={name}", json=payload)
            if res.status_code == 200:
                messagebox.showinfo("Sucesso", "Cliente sincronizado com a nuvem!")
                self.refresh_list()
            else:
                messagebox.showerror("Erro", "Falha ao registrar.")
        except:
            messagebox.showerror("Erro", "Servidor inacessível.")

if __name__ == "__main__":
    app = AdminPanel()
    app.mainloop()
