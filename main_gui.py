import customtkinter as ctk
from tkinter import filedialog, messagebox
import os
import threading
from datetime import datetime
from PIL import Image, ImageTk
from consolidation_engine import ConsolidationEngine
from auth_manager import AuthManager
import ctypes
import requests
from tkcalendar import Calendar
from coverage_engine import CoverageEngine

# FORÇAR O WINDOWS A RECONHECER O APP COMO INDEPENDENTE (Evitar o ícone da Cobra do Python na barra)
try:
    myappid = 'hemn.system.premium.v1' # Id arbitrário
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
except Exception:
    pass

import sys
VERSION = "1.4.0"

# CONSTANTES GLOBAIS DE CAMINHOS
CLOUD_URL = "https://hemnsystem.com.br/areadocliente"
PATH_DB_CNPJ = r"C:\HEMN_SYSTEM_DB\cnpj.db"
PATH_DB_CARRIER = r"C:\HEMN_SYSTEM_DB\hemn_carrier.db"
PATH_ASSETS = "data_assets"

def resource_path(relative_path):
    """ Retorna o caminho absoluto do recurso, compatível com PyInstaller --onefile """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.dirname(__file__)
    return os.path.join(base_path, relative_path)

# --- HELPERS DE DATA ---
def _to_br_date(iso_date):
    try:
        if not iso_date: return ""
        dt = datetime.strptime(iso_date, "%Y-%m-%d")
        return dt.strftime("%d/%m/%Y")
    except: return iso_date

def _to_iso_date(br_date):
    try:
        if not br_date: return ""
        dt = datetime.strptime(br_date, "%d/%m/%Y")
        return dt.strftime("%Y-%m-%d")
    except: return br_date

class TMMApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Configurações de Identidade e Layout
        self.title("HEMN SYSTEM | Suite de Inteligência de Dados")
        self.geometry("1100x820")
        
        # Injetar o ícone da janela para a Barra de Tarefas (Window Icon)
        try:
            icon_path = resource_path("hemn_app_icon.ico")
            if os.path.exists(icon_path):
                self.iconbitmap(icon_path)
            else:
                fallback_icon = resource_path("logo.ico")
                if os.path.exists(fallback_icon):
                    self.iconbitmap(fallback_icon)
                
            # Forçar IconPhoto extra associado (Mata a cobra do Python de vez)
            png_path = resource_path("logo.png")
            if os.path.exists(png_path):
                img_tk = ImageTk.PhotoImage(Image.open(png_path))
                self.wm_iconphoto(False, img_tk)
                self.icon_cache = img_tk        # Configuração inicial (3C+ SaaS Light)
        except Exception:
            pass
        
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # Paleta de Cores Premium (Titanium Dark)
        self.color_bg = ("#08090c", "#08090c")      # Fundo Preto Profundo
        self.color_sidebar = ("#0d0e12", "#0d0e12") # Sidebar Ligeiramente mais Clara
        self.color_card = ("#13141c", "#13141c")    # Cards Titanium
        self.color_accent = ("#3858f9", "#3858f9")  # Azul Royal 3C+
        self.color_border = ("#1e2030", "#1e2030")  # Bordas Sutis
        self.color_text_main = ("#f9fafb", "#f9fafb")
        self.color_text_dim = ("#64748b", "#64748b")
        self.color_success = ("#22c55e", "#22c55e")
        self.color_danger = ("#ef4444", "#ef4444")
        self.color_warning = ("#f59e0b", "#f59e0b")
        
        self.corner_rad = 18

        self.configure(fg_color=self.color_bg[1])

        # Sistema de Grid Principal
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=0) # Header fixo
        self.grid_rowconfigure(1, weight=1) # Conteúdo expansível

        # Sidebar de Navegação (3C+ Style Refinado)
        self.sidebar_frame = ctk.CTkFrame(self, width=100, corner_radius=0, 
                                        fg_color=self.color_sidebar, border_width=0)
        self.sidebar_frame.grid(row=0, column=0, rowspan=2, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(9, weight=1)

        # Barra Superior (Header 3C+ Style)
        self.header_frame = ctk.CTkFrame(self, height=70, corner_radius=0, 
                                        fg_color=self.color_sidebar, border_width=0)
        self.header_frame.grid(row=0, column=1, sticky="ew")
        self.header_frame.grid_columnconfigure(0, weight=1)
        self.setup_header_content()

        # Logo e Branding
        self.setup_branding()

        # Botões de Navegação (Nomes Funcionais Claros)
        self.nav_buttons = []
        self.btn_unify = self.add_nav_button("Unificar", 2, self.show_unify_frame)
        self.btn_manual = self.add_nav_button("CNPJ", 3, self.show_manual_frame)
        self.btn_batch = self.add_nav_button("Lote", 4, self.show_batch_frame)
        self.btn_extract = self.add_nav_button("Extrair", 5, self.show_extract_frame)
        self.btn_carrier = self.add_nav_button("Operadora", 6, self.show_carrier_frame)
        self.btn_coverage = self.add_nav_button("Cobertura", 7, self.show_coverage_frame)
        self.btn_split = self.add_nav_button("Dividir", 8, self.show_split_frame)
        
        # Botões de Administração
        self.btn_admin = self.add_nav_button("Gestão", 9, self.show_admin_frame)
        self.btn_monitor = self.add_nav_button("Monitor", 10, self.show_admin_monitor_direct)
        
        for b in [self.btn_admin, self.btn_monitor]:
            b.master.grid_remove() 
        
        # Botão de Configurações
        self.btn_settings = self.add_nav_button("Ajustes", 11, self.show_settings_frame)

        # Rodapé da Sidebar
        self.setup_sidebar_footer()

        # Autenticação e Licenciamento
        self.auth_manager = AuthManager()
        self.all_users = []
        self.user_rows = []

        # Engine
        self.engine = ConsolidationEngine(
            target_dir="", output_file="",
            progress_callback=self.update_ui_progress,
            log_callback=self.append_log,
            usage_callback=self.auth_manager.debit_credits
        )

        self.coverage_engine = CoverageEngine(
            progress_callback=self.update_coverage_progress,
            log_callback=self.append_coverage_log
        )

        # Container Principal
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.grid(row=1, column=1, sticky="nsew", padx=30, pady=30)
        self.main_container.grid_columnconfigure(0, weight=1)
        self.main_container.grid_rowconfigure(0, weight=1)

        # Handler de Fechamento (Auto-Logout)
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Variáveis de Controle de Estado
        self.var_batch_phone = ctk.BooleanVar(value=True)
        self.var_extract_phone = ctk.BooleanVar(value=True)

        # App frames (construídos mas não exibidos até login)
        self.frames = {}
        self.frames["unify"] = self.create_unify_frame()
        self.frames["manual"] = self.create_manual_frame()
        self.frames["batch"] = self.create_batch_frame()
        self.frames["extract"] = self.create_extract_frame()
        self.frames["split"] = self.create_split_frame()
        self.frames["carrier"] = self.create_carrier_frame()
        self.frames["coverage"] = self.create_coverage_frame()
        self.frames["settings"] = self.create_settings_frame()
        self.frames["admin"] = self.create_admin_frame()
        self.show_frame("unify")

        # --- LOGIN COMO OVERLAY FULLSCREEN (estilo web) ---
        self._login_overlay = None
        needs_login = True
        if self.auth_manager.token:
            success, _ = self.auth_manager.refresh_user_data()
            needs_login = not success

        if needs_login:
            self.show_login_screen()
        else:
            self._reveal_app()

    def on_closing(self):
        """ Executado ao fechar o programa: Garante o Logout """
        try:
            if hasattr(self, 'auth_manager'):
                self.auth_manager.logout()
        except:
            pass
        self.destroy()
        sys.exit(0)

    def setup_header_content(self):
        # Lado Esquerdo
        ctk.CTkLabel(self.header_frame, text="", width=10).pack(side="left")

        # Barra de Ações (Direita)
        actions = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        actions.pack(side="right", padx=30)

        # Saldo / Créditos
        self.header_credits = ctk.CTkLabel(actions, text="Saldo: R$ --",
                                           font=ctk.CTkFont(size=13, weight="bold"),
                                           text_color=self.color_accent)
        self.header_credits.pack(side="left", padx=20)

        # Botão do usuário (nome + ▼ clicável)
        self._user_dropdown_open = False
        self._user_dropdown_win = None

        self.user_btn_frame = ctk.CTkFrame(actions, fg_color=self.color_sidebar,
                                           corner_radius=8, border_width=1,
                                           border_color=self.color_border)
        self.user_btn_frame.pack(side="left")

        self.header_user = ctk.CTkLabel(self.user_btn_frame, text="Usuário  ▼",
                                        font=ctk.CTkFont(size=13, weight="bold"),
                                        text_color=self.color_text_main,
                                        cursor="hand2")
        self.header_user.pack(padx=16, pady=8)
        self.header_user.bind("<Button-1>", lambda e: self._toggle_user_dropdown())
        self.user_btn_frame.bind("<Button-1>", lambda e: self._toggle_user_dropdown())

    def _toggle_user_dropdown(self):
        if self._user_dropdown_open and self._user_dropdown_win:
            self._close_user_dropdown()
        else:
            self._open_user_dropdown()

    def _close_user_dropdown(self):
        if self._user_dropdown_win:
            self._user_dropdown_win.destroy()
            self._user_dropdown_win = None
        self._user_dropdown_open = False

    def _open_user_dropdown(self):
        self._user_dropdown_open = True
        u = self.auth_manager.user_data or {}

        # Coordenadas absolutas do botão e da janela
        self.update_idletasks()
        self.user_btn_frame.update_idletasks()

        btn_abs_x = self.user_btn_frame.winfo_rootx()
        btn_abs_y = self.user_btn_frame.winfo_rooty()
        btn_w     = self.user_btn_frame.winfo_width()
        btn_h     = self.user_btn_frame.winfo_height()
        win_abs_x = self.winfo_rootx()
        win_abs_y = self.winfo_rooty()

        popup_w = 270
        popup_h = 260

        # Posição relativa à janela principal
        rel_x = (btn_abs_x - win_abs_x) + btn_w - popup_w
        rel_y = (btn_abs_y - win_abs_y) + btn_h + 4

        # Frame dentro da janela principal
        popup = ctk.CTkFrame(self, fg_color="#1a1b26", corner_radius=12,
                             border_width=1, border_color="#1e2030",
                             width=popup_w, height=popup_h)
        popup.place(x=rel_x, y=rel_y)
        popup.lift()
        popup.pack_propagate(False)
        self._user_dropdown_win = popup

        # Bind para fechar ao clicar fora — com delay para não fechar no mesmo clique
        def _check_close(e):
            try:
                wx = popup.winfo_rootx()
                wy = popup.winfo_rooty()
                inside = (wx <= e.x_root <= wx + popup_w and
                          wy <= e.y_root <= wy + popup_h)
                if not inside:
                    self._close_user_dropdown()
                    try:
                        self.unbind("<Button-1>", self._dd_bind_id)
                    except Exception:
                        pass
            except Exception:
                pass

        # after(150) evita que o mesmo clique que abriu dispare o fechar
        def _setup_bind():
            self._dd_bind_id = self.bind("<Button-1>", _check_close, add="+")
        self.after(150, _setup_bind)

        # Avatar initials
        initials = (u.get("full_name") or u.get("username") or "U")[:2].upper()
        avatar = ctk.CTkLabel(popup, text=initials,
                              font=ctk.CTkFont(size=18, weight="bold"),
                              text_color="#ffffff",
                              fg_color=self.color_accent,
                              width=44, height=44, corner_radius=22)
        avatar.pack(pady=(14, 4))

        ctk.CTkLabel(popup,
                     text=u.get("full_name") or u.get("username") or "Usuário",
                     font=ctk.CTkFont(size=13, weight="bold"),
                     text_color="#f1f5f9").pack()
        ctk.CTkLabel(popup,
                     text=u.get("email") or u.get("username") or "—",
                     font=ctk.CTkFont(size=11),
                     text_color="#64748b").pack(pady=(2, 0))
        role = u.get("role") or "USUÁRIO"
        ctk.CTkLabel(popup, text=role,
                     font=ctk.CTkFont(size=10, weight="bold"),
                     text_color=self.color_accent).pack(pady=(2, 8))

        # Separador
        ctk.CTkFrame(popup, height=1, fg_color="#1e2030").pack(fill="x", padx=12)

        # Botões de ação
        def make_action(text, icon, command, danger=False):
            color = "#ef4444" if danger else "#94a3b8"
            hover = "#2d1b1b" if danger else "#242633"
            btn = ctk.CTkButton(popup, text=f"  {icon}  {text}", anchor="w",
                                height=38, corner_radius=6,
                                fg_color="transparent", hover_color=hover,
                                text_color=color,
                                font=ctk.CTkFont(size=13),
                                command=command)
            btn.pack(fill="x", padx=8, pady=2)

        make_action("Alterar Senha", "🔑", self._open_change_password)
        make_action("Sair / Logout", "🚪", self._do_logout, danger=True)



    def _open_change_password(self):
        self._close_user_dropdown()
        dlg = ctk.CTkToplevel(self)
        dlg.title("Alterar Senha")
        dlg.geometry("360x300")
        dlg.attributes("-topmost", True)
        dlg.grab_set()
        dlg.configure(fg_color="#0f172a")
        dlg.resizable(False, False)

        inner = ctk.CTkFrame(dlg, fg_color="#13141c", corner_radius=12, border_width=1, border_color="#1e2030")
        inner.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(inner, text="Alterar Senha",
                     font=ctk.CTkFont(size=18, weight="bold"),
                     text_color="#f1f5f9").pack(pady=(20, 16))

        def field(lbl, show=""):
            ctk.CTkLabel(inner, text=lbl, font=ctk.CTkFont(size=12),
                         text_color="#64748b").pack(anchor="w", padx=20, pady=(4, 2))
            e = ctk.CTkEntry(inner, show=show, height=38, corner_radius=8,
                             fg_color="#1a1b26", border_color="#1e2030",
                             text_color="#f1f5f9", font=ctk.CTkFont(size=13))
            e.pack(fill="x", padx=20)
            return e

        ent_old = field("Senha Atual", "*")
        ent_new = field("Nova Senha", "*")
        ent_conf = field("Confirmar Nova Senha", "*")
        lbl_err = ctk.CTkLabel(inner, text="", text_color="#f87171",
                               font=ctk.CTkFont(size=11))
        lbl_err.pack(pady=4)

        def do_change():
            old = ent_old.get(); new = ent_new.get(); conf = ent_conf.get()
            if not old or not new or not conf:
                lbl_err.configure(text="Preencha todos os campos"); return
            if new != conf:
                lbl_err.configure(text="Senhas não coincidem"); return
            if len(new) < 6:
                lbl_err.configure(text="Mínimo 6 caracteres"); return
            # Chama auth_manager se tiver endpoint, ou apenas fecha
            try:
                ok, msg = self.auth_manager.change_password(old, new)
                if ok:
                    dlg.destroy()
                    messagebox.showinfo("Sucesso", "Senha alterada com sucesso!")
                else:
                    lbl_err.configure(text=msg or "Falha ao alterar senha")
            except Exception:
                dlg.destroy()
                messagebox.showinfo("Aviso", "Função em desenvolvimento.")

        ctk.CTkButton(inner, text="Salvar", height=38, corner_radius=8,
                      fg_color=self.color_accent, text_color="#000000",
                      font=ctk.CTkFont(size=13, weight="bold"),
                      command=do_change).pack(fill="x", padx=20, pady=8)

    def _do_logout(self):
        self._close_user_dropdown()
        if messagebox.askyesno("Logout", "Deseja realmente sair da conta?"):
            try:
                self.auth_manager.logout()
            except Exception:
                pass
            self.header_user.configure(text="Usuário  ▼")
            self.show_login_screen()


    def _hide_main_ui(self):
        """Esconde a sidebar, header e conteúdo principal antes do login."""
        self.sidebar_frame.grid_remove()
        self.header_frame.grid_remove()
        self.main_container.grid_remove()

    def _reveal_app(self):
        """Revela a interface principal após login bem-sucedido."""
        if self._login_overlay:
            self._login_overlay.destroy()
            self._login_overlay = None
        self.sidebar_frame.grid()
        self.header_frame.grid()
        self.main_container.grid()
        self.update_license_ui()
        u = self.auth_manager.user_data
        if u and u.get('role') == 'ADMIN':
            self.btn_admin.master.grid()
            self.btn_monitor.master.grid()
        else:
            self.btn_admin.master.grid_remove()
            self.btn_monitor.master.grid_remove()

    def show_login_screen(self):
        """Login fullscreen estilo web — sobrepõe toda a janela."""
        # Esconder UI principal
        self._hide_main_ui()

        # Overlay que cobre toda a janela (Titanium background)
        overlay = ctk.CTkFrame(self, fg_color="#08090c", corner_radius=0)
        overlay.place(x=0, y=0, relwidth=1.0, relheight=1.0)
        overlay.lift()
        self._login_overlay = overlay

        # --- Coluna esquerda: branding (60% da largura) ---
        left = ctk.CTkFrame(overlay, fg_color="transparent", corner_radius=0)
        left.place(relx=0, rely=0, relwidth=0.55, relheight=1.0)

        center_box = ctk.CTkFrame(left, fg_color="transparent")
        center_box.place(relx=0.5, rely=0.5, anchor="center")

        try:
            ctk.CTkLabel(center_box, image=self.logo_img, text="").pack(pady=(0, 20))
        except Exception:
            pass

        ctk.CTkLabel(center_box, text="HEMN SYSTEM",
                     font=ctk.CTkFont(size=36, weight="bold"),
                     text_color="#f8fafc").pack(anchor="w")
        ctk.CTkLabel(center_box, text="Suite de Inteligência de Dados",
                     font=ctk.CTkFont(size=16),
                     text_color="#94a3b8").pack(anchor="w", pady=(6, 30))

        bullets = [
            ("🔍", "CNPJ e Enriquecimento em Lote"),
            ("📊", "Extração Cruzada com Filtros"),
            ("⚡", "Banco Mestre com Auto-Update"),
            ("🔐", "Acesso por Token Cloud Seguro"),
        ]
        for icon, text in bullets:
            row = ctk.CTkFrame(center_box, fg_color="transparent")
            row.pack(anchor="w", pady=6)
            ctk.CTkLabel(row, text=icon, font=ctk.CTkFont(size=18), text_color="#38bdf8").pack(side="left", padx=(0, 12))
            ctk.CTkLabel(row, text=text, font=ctk.CTkFont(size=14), text_color="#cbd5e1").pack(side="left")

        # --- Separador vertical sutil ---
        sep = ctk.CTkFrame(overlay, fg_color="#1e293b", corner_radius=0, width=2)
        sep.place(relx=0.55, rely=0.0, relwidth=0, relheight=1.0)

        # --- Coluna direita: formulário de login (45% da largura) ---
        right = ctk.CTkFrame(overlay, fg_color="#08090c", corner_radius=0)
        right.place(relx=0.55, rely=0, relwidth=0.45, relheight=1.0)

        form_box = ctk.CTkFrame(right, fg_color="#0d0e12", corner_radius=20,
                                border_width=1, border_color="#1e2030",
                                width=360, height=480)
        form_box.place(relx=0.5, rely=0.5, anchor="center")
        form_box.pack_propagate(False)

        # Cabeçalho do form
        ctk.CTkLabel(form_box, text="Acessar conta",
                     font=ctk.CTkFont(size=24, weight="bold"),
                     text_color="#f1f5f9").pack(pady=(40, 4))
        ctk.CTkLabel(form_box, text="Entre com suas credenciais de acesso",
                     font=ctk.CTkFont(size=13),
                     text_color="#64748b").pack(pady=(0, 28))

        # Campos
        def make_field(label, placeholder, show=""):
            ctk.CTkLabel(form_box, text=label,
                         font=ctk.CTkFont(size=12, weight="bold"),
                         text_color="#64748b").pack(anchor="w", padx=32, pady=(0, 4))
            e = ctk.CTkEntry(form_box, placeholder_text=placeholder, show=show,
                             width=296, height=44, corner_radius=8,
                             border_width=1, border_color="#1e2030",
                             fg_color="#0d0e12", text_color="#f1f5f9",
                             placeholder_text_color="#334155",
                             font=ctk.CTkFont(size=14))
            e.pack(pady=(0, 14))
            return e

        self.ent_user = make_field("Usuário / E-mail", "seu@email.com")
        self.ent_pass = make_field("Senha", "••••••••", show="*")

        # Botão principal
        self.btn_login = ctk.CTkButton(
            form_box, text="Entrar", width=296, height=46, corner_radius=8,
            fg_color="#3b82f6", hover_color="#2563eb",
            text_color="#ffffff", font=ctk.CTkFont(size=15, weight="bold"),
            command=self.execute_login)
        self.btn_login.pack(pady=(6, 16))

        self.lbl_login_status = ctk.CTkLabel(
            form_box, text="",
            text_color="#f87171", font=ctk.CTkFont(size=12))
        self.lbl_login_status.pack()

        # Versão
        ctk.CTkLabel(overlay, text=f"v{VERSION} · HEMN SYSTEM · Uso comercial restrito",
                     font=ctk.CTkFont(size=10), text_color="#334155"
                     ).place(relx=0.5, rely=0.97, anchor="center")

        self.ent_user.focus_set()
        overlay.bind("<Return>", lambda e: self.execute_login())

    def execute_login(self):
        user = self.ent_user.get()
        pw = self.ent_pass.get()

        if not user or not pw:
            self.lbl_login_status.configure(text="Preencha todos os campos")
            return

        self.btn_login.configure(state="disabled", text="Autenticando...")
        self.lbl_login_status.configure(text="")

        def run():
            success, msg = self.auth_manager.login(user, pw)
            if success:
                self.after(0, self.finish_login)
            else:
                self.after(0, lambda: [
                    self.lbl_login_status.configure(text=msg),
                    self.btn_login.configure(state="normal", text="Entrar")
                ])

        threading.Thread(target=run, daemon=True).start()

    def finish_login(self):
        self._reveal_app()
        u = self.auth_manager.user_data
        if u:
            self.header_user.configure(text=u.get('full_name', u.get('username', 'Usuário')))

    def setup_branding(self):
        # Logo Container (Duplo Dark/Light Mode com Tamanho Expandido)
        try:
            # Tenta carregar do resource_path (necessário para PyInstaller) e do diretório local
            p_light = resource_path("logo.png")
            p_dark = resource_path("logo_dark.png")
            
            # Se não existir no resource_path, tenta no diretório atual (desenvolvimento)
            if not os.path.exists(p_light):
                p_light = os.path.join(os.path.dirname(__file__), "logo.png")
            if not os.path.exists(p_dark):
                p_dark = os.path.join(os.path.dirname(__file__), "logo_dark.png")
                
            img_light = Image.open(p_light) if os.path.exists(p_light) else None
            img_dark = Image.open(p_dark) if os.path.exists(p_dark) else img_light
            
            if not img_light and not img_dark:
                # Fallback extremo caso tudo falhe (tenta o ico como imagem)
                fallback_ico = resource_path("logo.ico")
                if os.path.exists(fallback_ico):
                    img_light = Image.open(fallback_ico)
                    img_dark = img_light

            if img_light:
                # Tamanho reduzido para 130x130 (apenas o ícone abstrato, sem texto engessado)
                self.logo_img = ctk.CTkImage(light_image=img_light, dark_image=img_dark, size=(130, 130))
                # Logo pequena para sidebar icon-based
                self.logo_img = ctk.CTkImage(light_image=img_light, dark_image=img_dark, size=(45, 45))
                self.logo_label = ctk.CTkLabel(self.sidebar_frame, image=self.logo_img, text="")
                self.logo_label.grid(row=0, column=0, pady=(15, 25))
        except Exception:
            pass

    def add_nav_button(self, text, row, command):
        """ Cria um botão de navegação customizado (Frame) para estilo vertical 3C+ """
        # Container externo (Grid)
        container = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        container.grid(row=row, column=0, sticky="ew", pady=2)
        
        # O "Botão" (Frame clicável)
        btn = ctk.CTkFrame(container, fg_color="transparent", width=85, height=75, corner_radius=12)
        btn.pack(padx=8, pady=5)
        btn.pack_propagate(False) # Travar tamanho
        
        # Mapeamento de Ícones
        icon_map = {
            "Unificar": "🔗", "CNPJ": "🔍", "Lote": "📦", 
            "Extrair": "📊", "Operadora": "📡", "Cobertura": "🌐", "Dividir": "✂️", 
            "Gestão": "👥", "Monitor": "🖥️", "Ajustes": "⚙️"
        }
        icon_text = icon_map.get(text, "•")
        
        # Elementos Visuais
        btn.icon_label = ctk.CTkLabel(btn, text=icon_text, font=ctk.CTkFont(size=24))
        btn.icon_label.pack(pady=(12, 0))
        
        btn.text_label = ctk.CTkLabel(btn, text=text, font=ctk.CTkFont(size=11, weight="bold"),
                                     text_color=self.color_text_dim)
        btn.text_label.pack(pady=(0, 10))
        
        # Lógica de Hover e Clique
        def on_enter(e):
            if btn.cget("fg_color") == "transparent":
                btn.configure(fg_color="#1a1b26")
        def on_leave(e):
            if not getattr(btn, "is_selected", False):
                btn.configure(fg_color="transparent")
        
        def on_click(e):
            command()
            self.update_nav_selection(btn)

        # Bind em todos os elementos para garantir área de clique total
        for widget in [btn, btn.icon_label, btn.text_label]:
            widget.bind("<Enter>", on_enter)
            widget.bind("<Leave>", on_leave)
            widget.bind("<Button-1>", on_click)
            widget.configure(cursor="hand2")

        self.nav_buttons.append(btn)
        return btn

    def setup_sidebar_footer(self):
        # Rodapé com o botão de Configurações fixo em baixo
        pass # Definido via add_nav_button no row 10

    def update_nav_selection(self, selected_btn):
        for btn in self.nav_buttons:
            if btn == selected_btn:
                btn.configure(fg_color="#13141c") # Titanium Highlight
                btn.is_selected = True
                btn.icon_label.configure(text_color=self.color_accent)
                btn.text_label.configure(text_color=self.color_accent)
            else:
                btn.configure(fg_color="transparent")
                btn.is_selected = False
                btn.icon_label.configure(text_color=self.color_text_dim)
                btn.text_label.configure(text_color=self.color_text_dim)

    def update_license_ui(self):
        """ Atualiza os dados no header e sidebar """
        status = self.auth_manager.get_status_summary()
        
        # Atualizar Header (3C+ Style)
        if status["valid"] and self.auth_manager.user_data:
            self.header_user.configure(text=self.auth_manager.user_data['full_name'])
            self.header_credits.configure(text=f"Saldo: {status['usage']}")
        else:
            self.header_user.configure(text="Visitante")
            self.header_credits.configure(text="Saldo: R$ 0,00")



    def change_theme(self, theme):
        if theme == "Dark Elite": ctk.set_appearance_mode("dark")
        else: ctk.set_appearance_mode("light")

    # --- Elementos de UI Estilizados ---
    def create_card(self, parent, title, description):
        """ Cria um card moderno Titanium Dark com bordas sutis """
        card = ctk.CTkFrame(parent, fg_color=self.color_card, corner_radius=20, 
                            border_width=1, border_color=self.color_border)
        card.pack(fill="both", expand=True, padx=2, pady=10)
        
        # Header do Card (Titanium Style)
        header = ctk.CTkFrame(card, fg_color="transparent", height=45)
        header.pack(fill="x", padx=25, pady=(20, 10))
        
        # Action Icon (Círculo royal blue)
        dot = ctk.CTkFrame(header, width=8, height=8, corner_radius=4, fg_color=self.color_accent)
        dot.pack(side="left", padx=(0, 12))

        ctk.CTkLabel(header, text=title.upper(), font=ctk.CTkFont(size=14, weight="bold"), 
                     text_color=self.color_text_main).pack(side="left")
        
        ctk.CTkLabel(card, text=description, font=ctk.CTkFont(size=12), 
                     text_color=self.color_text_dim, justify="left").pack(padx=45, anchor="w", pady=(0, 20))
        
        content = ctk.CTkFrame(card, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=40, pady=(0, 25))
        return content

    def check_license(self):
        """ Verifica se a sessão é válida antes de qualquer operação """
        valid, msg = self.auth_manager.refresh_user_data()
        if not valid:
            messagebox.showerror("Sessão Expirada", "Sua sessão expirou ou é inválida. Por favor, faça login novamente.")
            self.show_login_screen()
            return False
        return True

    def ask_credit_confirmation(self, total_lines, rate, module_name):
        """ Diálogo para confirmar extração e definir quantidade """
        if not self.auth_manager.user_data: return None
        
        current_usage = self.auth_manager.user_data.get("current_usage", 0)
        total_limit = self.auth_manager.user_data.get("total_limit", 0)
        available = total_limit - current_usage
        
        cost_total = total_lines * rate
        
        msg = f"Módulo: {module_name}\n"
        msg += f"Registros encontrados: {total_lines:,}\n"
        msg += f"Custo por registro: {rate:.2f}\n\n"
        msg += f"Saldo de Créditos: {available:.2f}\n"
        msg += f"Custo total estimado: {cost_total:.2f}\n\n"
        msg += f"Deseja extrair quantos registros?"
        
        dialog = ctk.CTkInputDialog(text=msg, title="Confirmação de Créditos")
        val = dialog.get_input()
        
        if not val: return None
        
        try:
            qty = int(val)
            if qty <= 0: return None
            if qty > total_lines: qty = total_lines
            
            if qty * rate > available:
                messagebox.showerror("Saldo Insuficiente", f"Você precisa de {qty*rate:.2f} créditos, mas possui apenas {available:.2f}.")
                return None
            
            return qty
        except ValueError:
            messagebox.showerror("Erro", "Insira um número válido.")
            return None

    def add_styled_input(self, parent, label, placeholder, command):
        container = ctk.CTkFrame(parent, fg_color="transparent")
        container.pack(fill="x", pady=10)
        
        lbl = ctk.CTkLabel(container, text=label, font=ctk.CTkFont(size=14, weight="bold"), 
                           text_color=self.color_text_main)
        lbl.pack(anchor="w", padx=8)
        
        row = ctk.CTkFrame(container, fg_color="#1a1b26", corner_radius=12, 
                          border_width=1, border_color=self.color_border)
        row.pack(fill="x", pady=(6, 0))
        
        entry = ctk.CTkEntry(row, fg_color="transparent", border_width=0, height=45, 
                             placeholder_text=placeholder, font=ctk.CTkFont(size=14),
                             text_color=self.color_text_main, placeholder_text_color="#475569")
        entry.pack(side="left", fill="x", expand=True, padx=18)
        
        btn = ctk.CTkButton(row, text="EXPLORAR", width=100, height=35, corner_radius=8,
                            fg_color=self.color_accent, text_color="#ffffff",
                            font=ctk.CTkFont(size=12, weight="bold"))
        btn.configure(command=command)
        btn.pack(side="right", padx=12)
        return entry

    def add_fixed_db_display(self, parent, label, fixed_path):
        container = ctk.CTkFrame(parent, fg_color="transparent")
        container.pack(fill="x", pady=10)
        
        lbl = ctk.CTkLabel(container, text=label, font=ctk.CTkFont(size=14, weight="bold"), 
                           text_color=self.color_text_main)
        lbl.pack(anchor="w", padx=8)
        
        row = ctk.CTkFrame(container, fg_color="#1a1b26", corner_radius=12, 
                          border_width=1, border_color=self.color_border)
        row.pack(fill="x", pady=(6, 0))
        
        entry = ctk.CTkEntry(row, fg_color="transparent", border_width=0, height=45, 
                             font=ctk.CTkFont(size=14), text_color=self.color_accent)
        entry.insert(0, fixed_path)
        entry.configure(state="readonly")
        entry.pack(side="left", fill="x", expand=True, padx=18)
        return entry

    def add_simple_input(self, parent, label, placeholder, side):
        container = ctk.CTkFrame(parent, fg_color="transparent")
        container.pack(side=side, fill="x", expand=True, padx=8)
        
        lbl = ctk.CTkLabel(container, text=label, font=ctk.CTkFont(size=14, weight="bold"), 
                           text_color=self.color_text_main)
        lbl.pack(anchor="w", padx=8)
        
        entry = ctk.CTkEntry(container, fg_color="#1a1b26", border_width=1, 
                             border_color=self.color_border, height=45, corner_radius=12, 
                             placeholder_text=placeholder, text_color=self.color_text_main,
                             placeholder_text_color="#475569")
        entry.pack(fill="x", pady=(6, 0))
        return entry

    def add_combobox_input(self, parent, label, side, values=None):
        if values is None:
            values = [""]
        container = ctk.CTkFrame(parent, fg_color="transparent")
        container.pack(side=side, fill="x", expand=True, padx=8)
        
        lbl = ctk.CTkLabel(container, text=label, font=ctk.CTkFont(size=14, weight="bold"), 
                           text_color=self.color_text_main)
        lbl.pack(anchor="w", padx=8)
        
        combo = ctk.CTkComboBox(container, fg_color="#1a1b26", border_width=1, 
                             border_color=self.color_border, height=45, corner_radius=12, 
                             dropdown_fg_color="#13141c", dropdown_text_color=self.color_text_main,
                             button_color=self.color_accent, text_color=self.color_text_main,
                             values=values)
        combo.pack(fill="x", pady=(6, 0))
        combo.set("")
        return combo

    def add_styled_progress(self, parent):
        pbar = ctk.CTkProgressBar(parent, height=12, corner_radius=6, progress_color=self.color_accent)
        pbar.pack(fill="x", pady=(15, 25))
        pbar.set(0)
        return pbar

    def add_styled_log(self, parent, height=200):
        log = ctk.CTkTextbox(parent, height=height, corner_radius=18, 
                             fg_color="#0d0e12", border_width=1, 
                             border_color=self.color_border,
                             font=ctk.CTkFont(family="Consolas", size=13), 
                             text_color=self.color_text_main)
        log.pack(fill="both", expand=True)
        return log

    # --- Telas ---
    # --- Telas Functional Modules ---
    def create_unify_frame(self):
        f = ctk.CTkFrame(self.main_container, fg_color="transparent")
        inner = self.create_card(f, "UNIFICADOR DE INTELIGÊNCIA", "Processamento massivo de arquivos Excel e CSV para geração de relatório mestre unificado.")
        self.add_fixed_db_display(inner, "Database Mestre (CNPJ Local)", PATH_DB_CNPJ)
        self.src_entry = self.add_styled_input(inner, "Pasta de Origem (XLSX/CSV)", "Selecione a pasta com as bases...", self.select_source)
        self.dst_entry = self.add_styled_input(inner, "Relatório de Saída", "Onde salvar o arquivo final...", self.select_destination)
        self.btn_unify_run = ctk.CTkButton(inner, text="EXECUTAR CONSOLIDAÇÃO", height=54, corner_radius=12, fg_color=self.color_accent, text_color="#000000", font=ctk.CTkFont(size=14, weight="bold"), command=self.start_unification)
        self.btn_unify_run.pack(fill="x", pady=25)
        self.progress_bar = self.add_styled_progress(inner)
        self.log_box = self.add_styled_log(inner, height=200)
        return f

    def create_manual_frame(self):
        f = ctk.CTkFrame(self.main_container, fg_color="transparent")
        inner = self.create_card(f, "BUSCA MANUAL CNPJ", "Consulta individual ultra-rápida no banco de dados local por Nome ou CPF.")
        self.db_manual = self.add_fixed_db_display(inner, "Fonte de Dados Ativa", PATH_DB_CNPJ)
        row1 = ctk.CTkFrame(inner, fg_color="transparent")
        row1.pack(fill="x", pady=10)
        self.name_entry = self.add_simple_input(row1, "Nome / Razão Social", "Digite o nome...", "left")
        self.cpf_entry = self.add_simple_input(row1, "CPF / CNPJ", "Digite o documento...", "right")
        self.btn_manual_run = ctk.CTkButton(inner, text="LOCALIZAR REGISTROS", height=54, corner_radius=12, fg_color=self.color_accent, text_color="#000000", font=ctk.CTkFont(size=14, weight="bold"), command=self.run_manual_search)
        self.btn_manual_run.pack(fill="x", pady=25)
        self.manual_log = self.add_styled_log(inner, height=300)
        return f

    def create_batch_frame(self):
        f = ctk.CTkFrame(self.main_container, fg_color="transparent")
        inner = self.create_card(f, "BUSCA EM LOTE", "Processamento de listas (Excel/CSV) para enriquecimento de dados e localização de contatos.")
        self.db_batch = self.add_fixed_db_display(inner, "Fonte de Dados Ativa", PATH_DB_CNPJ)
        self.input_file = self.add_styled_input(inner, "Arquivo de Entrada", "Selecione sua lista (.xlsx / .csv)", self.select_input_file)
        row_cols = ctk.CTkFrame(inner, fg_color="transparent")
        row_cols.pack(fill="x", pady=10)
        self.name_col = self.add_combobox_input(row_cols, "Coluna: NOME", "left")
        self.cpf_col = self.add_combobox_input(row_cols, "Coluna: CPF/CNPJ", "right")
        self.check_batch_phone = ctk.CTkCheckBox(inner, text="Filtrar somente empresas com telefone válido", variable=self.var_batch_phone, font=ctk.CTkFont(size=12), text_color=self.color_text_dim, fg_color=self.color_accent, hover_color=self.color_border)
        self.check_batch_phone.pack(pady=10)
        self.btn_batch_run = ctk.CTkButton(inner, text="INICIAR PROCESSAMENTO EM LOTE", height=54, corner_radius=12, fg_color=self.color_accent, text_color="#000000", font=ctk.CTkFont(size=14, weight="bold"), command=self.run_batch_search)
        self.btn_batch_run.pack(fill="x", pady=20)
        self.batch_pbar = self.add_styled_progress(inner)
        self.batch_log = self.add_styled_log(inner, height=180)
        return f

    def create_extract_frame(self):
        f = ctk.CTkFrame(self.main_container, fg_color="transparent")
        inner = self.create_card(f, "EXTRAÇÃO DE INTELIGÊNCIA", "Extração massiva do banco mestre usando filtros geográficos e setoriais (CNAE/Cidade).")
        self.db_extract = self.add_fixed_db_display(inner, "Fonte de Dados Primária", PATH_DB_CNPJ)
        grid = ctk.CTkFrame(inner, fg_color="transparent"); grid.pack(fill="x", pady=10)
        self.f_cidade = self.add_simple_input(grid, "Cidade", "Ex: SAO PAULO", "left")
        self.f_uf = self.add_simple_input(grid, "UF", "Ex: SP", "right")
        grid2 = ctk.CTkFrame(inner, fg_color="transparent"); grid2.pack(fill="x", pady=10)
        self.f_cnae = self.add_simple_input(grid2, "CNAE (Opcional)", "Ex: 4711302", "left")
        self.f_situacao = self.add_combobox_input(grid2, "Situação Cadastral", "right", values=["TODAS", "ATIVA", "BAIXADA", "INAPTA", "SUSPENSA"]); self.f_situacao.set("TODAS")
        grid3 = ctk.CTkFrame(inner, fg_color="transparent"); grid3.pack(fill="x", pady=10)
        self.f_tipo_tel = self.add_combobox_input(grid3, "Tipo Telefone", "left", values=["TODOS", "MÓVEL", "FIXO", "AMBOS"]); self.f_tipo_tel.set("TODOS")
        self.f_excel_cep = self.add_styled_input(grid3, "Planilha CEPs", "Filtrar por lista...", self.select_excel_cep)
        row_check = ctk.CTkFrame(inner, fg_color="transparent"); row_check.pack(fill="x", pady=5)
        ctk.CTkCheckBox(row_check, text="Exportar apenas com contato", variable=self.var_extract_phone, font=ctk.CTkFont(size=12), text_color=self.color_text_dim, fg_color=self.color_accent).pack(side="left", padx=5)
        self.btn_extract_run = ctk.CTkButton(inner, text="INICIAR EXTRAÇÃO MASSIVA", height=54, corner_radius=12, fg_color=self.color_accent, text_color="#000000", font=ctk.CTkFont(size=14, weight="bold"), command=self.run_extract)
        self.btn_extract_run.pack(fill="x", pady=20)
        self.btn_tune = ctk.CTkButton(inner, text="⚡ OTIMIZAR ESTRUTURA (INDEX)", height=32, corner_radius=8, fg_color="transparent", border_width=1, border_color=self.color_warning, text_color=self.color_warning, font=ctk.CTkFont(size=11, weight="bold"), command=self.run_database_optimization)
        self.btn_tune.pack(pady=(0, 20))
        self.extract_pbar = self.add_styled_progress(inner)
        self.extract_log = self.add_styled_log(inner, height=150)
        return f

    def create_split_frame(self):
        f = ctk.CTkFrame(self.main_container, fg_color="transparent")
        inner = self.create_card(f, "DIVISOR DE ARQUIVOS (SPLIT)", "Divide arquivos Excel ou CSV gigantes em múltiplas abas ou arquivos menores.")
        self.split_input = self.add_styled_input(inner, "Arquivo de Entrada (Grande)", "CSV ou XLSX de origem...", self.select_split_input)
        self.split_output = self.add_styled_input(inner, "Arquivo de Saída (Dividido)", "Onde salvar o resultado...", self.select_split_output)
        self.btn_split_run = ctk.CTkButton(inner, text="EXECUTAR DIVISÃO", height=54, corner_radius=12, fg_color=self.color_accent, text_color="#000000", font=ctk.CTkFont(size=14, weight="bold"), command=self.run_split)
        self.btn_split_run.pack(fill="x", pady=25)
        self.split_pbar = self.add_styled_progress(inner)
        self.split_log = self.add_styled_log(inner, height=200)
        return f

    def create_carrier_frame(self):
        f = ctk.CTkFrame(self.main_container, fg_color="transparent")
        inner = self.create_card(f, "CONSULTA DE OPERADORA", "Identificação de operadoras e tecnologias (Móvel/Fixo) de listas de telefone.")

        # 1. Database local
        self.add_fixed_db_display(inner, "Database Operadoras local", PATH_DB_CARRIER)

        # 2. Arquivo de entrada
        self.carrier_input_file = self.add_styled_input(inner, "Lista de Telefones", "Arquivo com números (.xlsx / .csv)...", self.select_carrier_input)

        # 3. Coluna de telefone (label + combobox full width)
        ctk.CTkLabel(inner, text="Coluna de Telefone", font=ctk.CTkFont(size=13, weight="bold"),
                     text_color=self.color_text_main).pack(anchor="w", pady=(10, 4))
        self.carrier_phone_col = ctk.CTkComboBox(inner, values=[], width=400, height=40,
                                                  fg_color=self.color_sidebar,
                                                  border_color=self.color_border,
                                                  button_color=self.color_accent,
                                                  text_color=self.color_text_main,
                                                  font=ctk.CTkFont(size=13))
        self.carrier_phone_col.pack(fill="x", pady=(0, 10))

        # 4. Arquivo de saída
        self.carrier_output_file = self.add_styled_input(inner, "Arquivo de Saída", "Salvar resultado em...", self.select_carrier_output)

        # 5. Botão principal
        self.btn_carrier_run = ctk.CTkButton(
            inner, text="INICIAR CONSULTA", height=54, corner_radius=12,
            fg_color=self.color_accent, text_color="#000000",
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self.run_carrier_lookup)
        self.btn_carrier_run.pack(fill="x", pady=20)

        # 6. Botão secundário (importar ANATEL)
        self.carrier_import_btn = ctk.CTkButton(
            inner, text="IMPORTAR CSV GIGANTE DA ANATEL PARA SQLite",
            height=32, corner_radius=8,
            fg_color="transparent", border_width=1,
            border_color=self.color_border, text_color=self.color_text_dim,
            font=ctk.CTkFont(size=11, weight="bold"),
            command=self.run_carrier_import)
        self.carrier_import_btn.pack(fill="x", pady=(0, 15))

        # 7. Progresso e log
        self.carrier_pbar = self.add_styled_progress(inner)
        self.carrier_log = self.add_styled_log(inner, height=150)
        return f

    def create_coverage_frame(self):
        f = ctk.CTkFrame(self.main_container, fg_color="transparent")
        
        # Split into Left and Right
        left_panel = ctk.CTkFrame(f, fg_color="transparent", width=380)
        left_panel.pack(side="left", fill="both", padx=(0, 20))
        left_panel.pack_propagate(False)
        
        right_panel = ctk.CTkFrame(f, fg_color="transparent")
        right_panel.pack(side="left", fill="both", expand=True)

        # LEFT PANEL CONTENT
        title_label = ctk.CTkLabel(left_panel, text="Cruzamento CNPJ x Vivo", 
                                   font=ctk.CTkFont(size=24, weight="bold"),
                                   text_color=self.color_accent)
        title_label.pack(anchor="w", pady=(10, 2))
        
        subtitle_label = ctk.CTkLabel(left_panel, text="Motor Geográfico v2.0", 
                                      font=ctk.CTkFont(size=13),
                                      text_color=self.color_text_dim)
        subtitle_label.pack(anchor="w", pady=(0, 30))

        # BASE PRINCIPAL (CNPJ)
        ctk.CTkLabel(left_panel, text="BASE PRINCIPAL (CNPJ)", font=ctk.CTkFont(size=11, weight="bold"), text_color=self.color_text_dim).pack(anchor="w", pady=(10, 5))
        self.coverage_cnpj_entry = self.add_styled_input_compact(left_panel, "Selecione o arquivo...", self.select_coverage_cnpj)

        # REFERÊNCIA DE COBERTURA
        row_ref = ctk.CTkFrame(left_panel, fg_color="transparent")
        row_ref.pack(fill="x", pady=(25, 5))
        ctk.CTkLabel(row_ref, text="REFERÊNCIA DE COBERTURA", font=ctk.CTkFont(size=11, weight="bold"), text_color=self.color_text_dim).pack(side="left")
        
        self.coverage_tipo_filter = ctk.CTkComboBox(row_ref, values=["TODOS", "HORIZONTAL", "VERTICAL"], width=130, height=32, 
                                                    fg_color=self.color_sidebar, border_color=self.color_border, button_color=self.color_accent)
        self.coverage_tipo_filter.pack(side="right")
        self.coverage_tipo_filter.set("TODOS")

        # Buttons + Listbox
        btn_row = ctk.CTkFrame(left_panel, fg_color="transparent")
        btn_row.pack(fill="x", pady=10)
        
        self.btn_add_vivo = ctk.CTkButton(btn_row, text="+ Adicionar Base", width=140, height=36, fg_color="#1e2030", hover_color="#2d2e35", command=self.select_coverage_vivo)
        self.btn_add_vivo.pack(side="left")
        
        self.btn_clear_vivo = ctk.CTkButton(btn_row, text="✕ Limpar", width=90, height=36, fg_color="transparent", border_width=1, border_color=self.color_danger, text_color=self.color_danger, command=self.clear_coverage_vivos)
        self.btn_clear_vivo.pack(side="right")

        self.coverage_vivo_list = ctk.CTkTextbox(left_panel, height=220, corner_radius=12, fg_color="#0d0e12", border_width=1, border_color=self.color_border, font=ctk.CTkFont(size=11))
        self.coverage_vivo_list.pack(fill="x", pady=10)
        self.coverage_vivo_list.configure(state="disabled")
        
        self.lbl_vivos_count = ctk.CTkLabel(left_panel, text="0 bases carregadas.", font=ctk.CTkFont(size=12), text_color=self.color_text_dim)
        self.lbl_vivos_count.pack(anchor="w")

        # Engine Buttons
        self.btn_coverage_run = ctk.CTkButton(left_panel, text="START ENGINE", height=54, corner_radius=12, fg_color=self.color_accent, text_color="#ffffff", font=ctk.CTkFont(size=14, weight="bold"), command=self.run_coverage_engine)
        self.btn_coverage_run.pack(fill="x", pady=(40, 12))
        
        self.btn_coverage_export = ctk.CTkButton(left_panel, text="EXPORT RESULT", height=48, corner_radius=12, fg_color="#1e2030", text_color="#ffffff", font=ctk.CTkFont(size=13, weight="bold"), command=self.export_coverage_result)
        self.btn_coverage_export.pack(fill="x")
        self.btn_coverage_export.configure(state="disabled")

        # RIGHT PANEL CONTENT
        status_row = ctk.CTkFrame(right_panel, fg_color="transparent")
        status_row.pack(fill="x", pady=(10, 15))
        
        self.lbl_coverage_status = ctk.CTkLabel(status_row, text="● STANDBY", font=ctk.CTkFont(size=13, weight="bold"), text_color=self.color_text_dim)
        self.lbl_coverage_status.pack(side="left")
        
        ctk.CTkLabel(status_row, text="MODO SMART: GO/DF/MT/MS | MODO SIMPLES: Demais UFs", font=ctk.CTkFont(size=11), text_color=self.color_text_dim).pack(side="right")

        self.coverage_log = self.add_styled_log(right_panel, height=520)
        
        self.coverage_pbar = self.add_styled_progress(right_panel)
        
        self.lbl_footer_msg = ctk.CTkLabel(right_panel, text="Aguardando dados da Base CNPJ...", font=ctk.CTkFont(size=12), text_color=self.color_text_dim)
        self.lbl_footer_msg.pack(anchor="w", pady=5)

        # Internal state
        self.selected_vivos = []
        self.coverage_result_df = None

        return f


    def create_settings_frame(self):
        f = ctk.CTkFrame(self.main_container, fg_color="transparent")
        
        # --- SEÇÃO 1: APARÊNCIA ---
        inner_ui = self.create_card(f, "PREFERÊNCIAS DE INTERFACE", "Personalize a aparência e o comportamento visual do sistema.")
        row_ui = ctk.CTkFrame(inner_ui, fg_color="transparent")
        row_ui.pack(fill="x", pady=15, padx=20)
        
        ctk.CTkLabel(row_ui, text="Tema da Interface:", font=ctk.CTkFont(size=14, weight="bold"), text_color=self.color_text_main).pack(side="left", padx=(0, 20))
        self.theme_menu = ctk.CTkOptionMenu(row_ui, values=["Dark Elite", "Light Glass"], 
                                            command=self.change_theme, 
                                            fg_color=self.color_sidebar, 
                                            button_color=self.color_accent, 
                                            button_hover_color=self.color_border, 
                                            dropdown_fg_color=self.color_card, 
                                            text_color=self.color_text_main)
        self.theme_menu.pack(side="left")
        self.theme_menu.set("Dark Elite")

        # --- SEÇÃO 2: BANCO MESTRE (CRONJOB) ---
        inner_db = self.create_card(f, "GESTÃO AUTÔNOMA DO BANCO MESTRE", "Configure o HEMN SYSTEM para se atualizar com a Receita Federal sozinho.")
        
        info_lbl = ctk.CTkLabel(inner_db, text="Ao habilitar essa rotina, o HEMN instruirá o Windows a baixar a nova base CNPJ\ntodos os dias 13 e 28 às 19:30h em segundo plano, sem que este App precise estar aberto.",
                                font=ctk.CTkFont(size=13), text_color=self.color_text_dim, justify="left")
        info_lbl.pack(pady=(10, 20), anchor="w", padx=10)
        
        cron_box = ctk.CTkFrame(inner_db, fg_color=self.color_sidebar, corner_radius=12, border_width=1, border_color=self.color_border)
        cron_box.pack(fill="x", padx=5, pady=5)
        
        self.cron_status_tag = ctk.CTkLabel(cron_box, text="●  O.S CRONJOB INATIVO", font=ctk.CTkFont(size=11, weight="bold"), text_color="#ff4a4a")
        self.cron_status_tag.pack(side="left", padx=20, pady=15)
        if self.check_cron_status(): 
            self.cron_status_tag.configure(text="●  O.S CRONJOB ATIVO", text_color="#00d26a")
            
        self.cron_switch = ctk.CTkSwitch(cron_box, text="Habilitar Atualização Automática", font=ctk.CTkFont(size=12, weight="bold"), 
                                        fg_color=self.color_border, progress_color=self.color_accent, command=self.toggle_cron)
        self.cron_switch.pack(side="right", padx=20)
        if self.check_cron_status(): self.cron_switch.select()

        # --- SEÇÃO 3: SOBRE / CONTA ---
        inner_about = self.create_card(f, "INFORMAÇÕES DA CONTA E SISTEMA", "Detalhes da versão instalada e gerenciamento de sessão.")
        
        user_id = self.auth_manager.user_data['username'] if self.auth_manager.user_data else "Visitante"
        about_text = f"Versão: HEMN SYSTEM v{VERSION} (Cloud Edition)\nUsuário: {user_id}\nBuild: 2026.02.25"
        
        ctk.CTkLabel(inner_about, text=about_text, font=ctk.CTkFont(size=13), 
                     text_color=self.color_text_dim, justify="left").pack(pady=(10, 20), padx=10, anchor="w")
        
        ctk.CTkButton(inner_about, text="LOGOUT / TROCAR USUÁRIO", height=45, corner_radius=10, 
                     fg_color="transparent", border_width=1, border_color=self.color_danger, 
                     text_color=self.color_danger, font=ctk.CTkFont(size=12, weight="bold"), 
                     command=self.execute_logout).pack(fill="x", pady=(0, 10), padx=10)
        
        return f


    def check_cron_status(self):
        try:
            import subprocess
            res = subprocess.run(['schtasks', '/query', '/tn', 'HEMN_System_Updater_Cron_D13'], capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
            return res.returncode == 0
        except: return False

    def toggle_cron(self):
        if self.cron_switch.get() == 1: self.run_cron_setup()
        else: self.remove_cron_setup()

    def remove_cron_setup(self):
        try:
            import subprocess
            tasks = ["HEMN_System_Alerts_D13_10h", "HEMN_System_Alerts_D13_14h", "HEMN_System_Alerts_D13_18h", "HEMN_System_Alerts_D28_10h", "HEMN_System_Alerts_D28_14h", "HEMN_System_Alerts_D28_18h", "HEMN_System_Updater_Cron_D13", "HEMN_System_Updater_Cron_D28"]
            for t in tasks: subprocess.run(['schtasks', '/delete', '/tn', t, '/f'], capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
            self.cron_status_tag.configure(text="●  O.S CRONJOB INATIVO", text_color="#ff4a4a")
            messagebox.showinfo("Sucesso", "Rotina Automática desabilitada.")
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao remover o agendamento: {e}")
            self.cron_switch.select()

    # --- Módulo Admin ---
    def create_admin_frame(self):
        """ Cria a tela de Gestão de Usuários com sistema de sub-views """
        self.admin_master = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.admin_master.grid_columnconfigure(0, weight=1)
        self.admin_master.grid_rowconfigure(0, weight=1)

        # 1. View de Lista
        self.view_admin_list = ctk.CTkFrame(self.admin_master, fg_color="transparent")
        self._build_admin_list_view()

        # 2. View de Cadastro
        self.view_admin_add = ctk.CTkFrame(self.admin_master, fg_color="transparent")
        self._build_admin_add_view()

        # 3. View de Edição (Dinâmica)
        self.view_admin_edit = ctk.CTkFrame(self.admin_master, fg_color="transparent")

        # 4. View de Monitoramento
        self.view_admin_monitor = ctk.CTkFrame(self.admin_master, fg_color="transparent")
        self._build_admin_monitor_view()

        # Iniciar na lista
        self.show_admin_subview("list")
        return self.admin_master

    def show_admin_frame(self):
        """ Método acionado pelo botão da sidebar para exibir o módulo de Gestão """
        self.show_frame("admin")
        self.show_admin_subview("list")

    def show_admin_monitor_direct(self):
        """ Navega direto para o monitoramento a partir da sidebar """
        self.show_frame("admin")
        self.show_admin_subview("monitor")

    def show_admin_subview(self, view_name, user_data=None):
        """ Alterna entre sub-views dentro do módulo de Gestão """
        self.view_admin_list.grid_forget()
        self.view_admin_add.grid_forget()
        self.view_admin_edit.grid_forget()

        if view_name == "list":
            self.view_admin_list.grid(row=0, column=0, sticky="nsew")
            self.refresh_admin_list()
        elif view_name == "add":
            self.view_admin_add.grid(row=0, column=0, sticky="nsew")
        elif view_name == "edit" and user_data:
            self._build_admin_edit_view(user_data)
            self.view_admin_edit.grid(row=0, column=0, sticky="nsew")
        elif view_name == "monitor":
            self.view_admin_monitor.grid(row=0, column=0, sticky="nsew")
            self.start_monitor_polling()

    def _add_premium_calendar(self, parent, initial_date=None):
        """ Helper para criar o calendário com o visual 'reformulado' premium """
        C = {"bg": "#08090c", "card": "#13141c", "card2": "#1a1b26",
             "border": "#1e2030", "muted": "#64748b", "white": "#e2e8f0"}
        
        # Se não houver data, usa hoje + 1 ano (padrão renovação)
        if not initial_date:
            initial_date = datetime.now().replace(year=datetime.now().year + 1)
        elif isinstance(initial_date, str):
            try:
                initial_date = datetime.fromisoformat(initial_date.split("T")[0])
            except:
                initial_date = datetime.now()

        cal = Calendar(parent, selectmode="day",
                       year=initial_date.year, month=initial_date.month, day=initial_date.day,
                       background=C["card2"], foreground=C["white"], bordercolor=C["border"],
                       headersbackground=C["card"], headersforeground=C["white"],
                       selectbackground=self.color_accent, selectforeground="#000000",
                       normalbackground=C["card2"], normalforeground=C["white"],
                       weekendbackground=C["card2"], weekendforeground=self.color_accent,
                       othermonthbackground=C["bg"], othermonthforeground=C["muted"],
                       date_pattern="dd/mm/yyyy", font=("Segoe UI", 11))
        return cal

    def _build_admin_list_view(self):
        """ Constrói a interface de listagem de usuários """
        # ── Header simples ──
        hdr = ctk.CTkFrame(self.view_admin_list, fg_color="transparent")
        hdr.pack(fill="x", pady=(0, 20))

        ctk.CTkLabel(hdr, text="Gerenciamento de Usuários",
                     font=ctk.CTkFont(size=20, weight="bold"),
                     text_color=self.color_text_main).pack(side="left")

        ctk.CTkButton(hdr, text="⟳  Atualizar", width=120, height=36, corner_radius=8,
                      fg_color="transparent", border_width=1, border_color=self.color_accent,
                      text_color=self.color_accent, hover_color=self.color_card,
                      font=ctk.CTkFont(size=12, weight="bold"),
                      command=self.refresh_admin_list).pack(side="right")

        ctk.CTkButton(hdr, text="➕  Novo Usuário", width=145, height=36, corner_radius=8,
                      fg_color=self.color_accent, text_color="#000000",
                      font=ctk.CTkFont(size=12, weight="bold"),
                      command=lambda: self.show_admin_subview("add")).pack(side="right", padx=12)

        ctk.CTkButton(hdr, text="📊  Monitoramento", width=145, height=36, corner_radius=8,
                      fg_color="transparent", border_width=1, border_color=self.color_warning,
                      text_color=self.color_warning, hover_color=self.color_card,
                      font=ctk.CTkFont(size=12, weight="bold"),
                      command=lambda: self.show_admin_subview("monitor")).pack(side="right")

        # ── Área de conteúdo ──
        content = self.view_admin_list

        # Stats bar — 4 cards idênticos ao original
        self.stats_container = ctk.CTkFrame(content, fg_color="transparent")
        self.stats_container.pack(fill="x", pady=(0, 20))

        self.stat_widgets = {}
        C = {
            "card":   "#13141c",
            "border": "#1e2030",
            "blue":   "#3b82f6",
            "green":  "#22c55e",
            "red":    "#ef4444",
            "muted":  "#64748b",
        }
        stats = [
            ("total",   "Total de Usuários", "👥", C["blue"]),
            ("active",  "Usuários Ativos",    "✅", C["green"]),
            ("blocked", "Bloqueados",          "🔒", C["red"]),
            ("credits", "Créditos em Uso",    "💳", self.color_accent),
        ]
        for i, (key, label, icon, color) in enumerate(stats):
            self.stats_container.grid_columnconfigure(i, weight=1)
            sc = ctk.CTkFrame(self.stats_container, fg_color=C["card"],
                              corner_radius=14, border_width=1,
                              border_color=C["border"])
            sc.grid(row=0, column=i, padx=6, sticky="ew")
            ctk.CTkLabel(sc, text=icon, font=ctk.CTkFont(size=22)).pack(anchor="w", padx=18, pady=(14, 0))
            lbl = ctk.CTkLabel(sc, text="—",
                               font=ctk.CTkFont(size=26, weight="bold"),
                               text_color=color)
            lbl.pack(anchor="w", padx=18)
            ctk.CTkLabel(sc, text=label, font=ctk.CTkFont(size=11),
                         text_color=C["muted"]).pack(anchor="w", padx=18, pady=(0, 14))
            self.stat_widgets[key] = lbl

        # Lista de usuários (3 colunas, scrollável)
        self.admin_list_scroll = ctk.CTkScrollableFrame(content, fg_color="transparent",
                                                        scrollbar_button_color=self.color_border)
        self.admin_list_scroll.pack(fill="both", expand=True)
        for i in range(3):
            self.admin_list_scroll.grid_columnconfigure(i, weight=1)

        return self.admin_master

    def _build_admin_add_view(self):
        """ Constrói a interface de cadastro de usuários como página interna """
        C = {"bg": "#08090c", "card": "#13141c", "card2": "#1a1b26",
             "border": "#1e2030", "muted": "#64748b", "white": "#e2e8f0"}

        # Limpar view antes de reconstruir (caso necessário)
        for widget in self.view_admin_add.winfo_children(): widget.destroy()

        # ── Header com botão Voltar ──
        hdr = ctk.CTkFrame(self.view_admin_add, fg_color="transparent")
        hdr.pack(fill="x", pady=(0, 20))

        ctk.CTkButton(hdr, text="←  Voltar", width=100, height=36, corner_radius=8,
                      fg_color="transparent", border_width=1, border_color=C["muted"],
                      text_color=C["muted"], hover_color=C["card"],
                      font=ctk.CTkFont(size=12, weight="bold"),
                      command=lambda: self.show_admin_subview("list")).pack(side="left")

        ctk.CTkLabel(hdr, text="Novo Operador Cloud",
                     font=ctk.CTkFont(size=20, weight="bold"),
                     text_color=self.color_text_main).pack(side="left", padx=20)

        # Container principal 2 colunas
        main = ctk.CTkFrame(self.view_admin_add, fg_color="transparent")
        main.pack(fill="both", expand=True)
        main.grid_columnconfigure(0, weight=1)
        main.grid_columnconfigure(1, weight=1)
        main.grid_rowconfigure(0, weight=1)

        # ── Coluna Esquerda: formulário ──
        left = ctk.CTkFrame(main, fg_color=C["card"], corner_radius=24,
                            border_width=1, border_color=C["border"])
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        ctk.CTkLabel(left, text="🆔 Dados do Novo Usuário",
                     font=ctk.CTkFont(size=20, weight="bold"),
                     text_color=C["white"]).pack(anchor="w", padx=30, pady=(30, 20))

        def themed_field(parent, label, placeholder="", icon="", show_char=""):
            c = ctk.CTkFrame(parent, fg_color="transparent")
            c.pack(fill="x", padx=30, pady=6)
            ctk.CTkLabel(c, text=label, font=ctk.CTkFont(size=11, weight="bold"),
                         text_color=C["muted"]).pack(anchor="w", padx=10)
            ff = ctk.CTkFrame(c, fg_color=C["card2"], corner_radius=12,
                              border_width=1, border_color=C["border"], height=48)
            ff.pack(fill="x", pady=(4, 0))
            ff.pack_propagate(False)
            ctk.CTkLabel(ff, text=icon, font=ctk.CTkFont(size=14)).pack(side="left", padx=(15, 10))
            e = ctk.CTkEntry(ff, fg_color="transparent", border_width=0,
                             placeholder_text=placeholder, show=show_char,
                             font=ctk.CTkFont(size=14))
            e.pack(side="left", fill="both", expand=True, padx=(0, 15))
            return e

        e_user  = themed_field(left, "USERNAME",       "ex: joaosilva",     "👤")
        e_pass  = themed_field(left, "SENHA INICIAL",  "min. 6 caracteres", "🔑", show_char="*")
        e_name  = themed_field(left, "NOME COMPLETO",  "Nome e sobrenome",  "🆔")

        # Limite + switch Ilimitado
        ext = ctk.CTkFrame(left, fg_color="transparent")
        ext.pack(fill="x", padx=30, pady=6)

        lim_col = ctk.CTkFrame(ext, fg_color="transparent")
        lim_col.pack(side="left", fill="x", expand=True, padx=(0, 8))

        lbl_lim = ctk.CTkFrame(lim_col, fg_color="transparent")
        lbl_lim.pack(fill="x")
        ctk.CTkLabel(lbl_lim, text="LIMITE DE CRÉDITOS",
                     font=ctk.CTkFont(size=11, weight="bold"),
                     text_color=C["muted"]).pack(side="left", padx=10)

        sw_unlimited = ctk.CTkSwitch(lbl_lim, text="Ilimitado",
                                     font=ctk.CTkFont(size=11, weight="bold"),
                                     progress_color=self.color_accent,
                                     text_color=self.color_accent)
        sw_unlimited.pack(side="right")

        ff_lim = ctk.CTkFrame(lim_col, fg_color=C["card2"], corner_radius=12,
                              border_width=1, border_color=C["border"], height=48)
        ff_lim.pack(fill="x", pady=(4, 0))
        ff_lim.pack_propagate(False)
        ctk.CTkLabel(ff_lim, text="💳", font=ctk.CTkFont(size=14)).pack(side="left", padx=(15, 10))
        e_limit = ctk.CTkEntry(ff_lim, fg_color="transparent", border_width=0,
                               placeholder_text="Quantidade", font=ctk.CTkFont(size=14))
        e_limit.pack(side="left", fill="both", expand=True)
        e_limit.insert(0, "1000")

        def toggle_unlimited():
            if sw_unlimited.get():
                e_limit.delete(0, "end")
                e_limit.insert(0, "∞ (Ilimitado)")
                e_limit.configure(state="disabled")
            else:
                e_limit.configure(state="normal")
                e_limit.delete(0, "end")
                e_limit.insert(0, "1000")
        sw_unlimited.configure(command=toggle_unlimited)

        # Nível de acesso (admin switch)
        adm_col = ctk.CTkFrame(ext, fg_color="transparent")
        adm_col.pack(side="left", fill="x", expand=True, padx=(8, 0))
        ctk.CTkLabel(adm_col, text="NÍVEL DE ACESSO",
                     font=ctk.CTkFont(size=11, weight="bold"),
                     text_color=C["muted"]).pack(anchor="w", padx=10)
        sw_f = ctk.CTkFrame(adm_col, fg_color=C["card2"], corner_radius=12,
                            border_width=1, border_color=C["border"], height=48)
        sw_f.pack(fill="x", pady=(4, 0))
        sw_f.pack_propagate(False)
        sw_admin = ctk.CTkSwitch(sw_f, text="Administrador",
                                 font=ctk.CTkFont(size=12, weight="bold"),
                                 progress_color="#ef4444", text_color=C["white"])
        sw_admin.place(relx=0.5, rely=0.5, anchor="center")
        if self.auth_manager.user_data and self.auth_manager.user_data.get("role") == "ADMIN":
            sw_admin.select()

        # Botão criar
        def register():
            username = e_user.get().strip()
            password = e_pass.get()
            full_name = e_name.get().strip()
            limit_raw = e_limit.get()
            exp_raw = cal.get_date()
            if not username or not password or not full_name:
                return
            total_limit = 9_999_999 if sw_unlimited.get() else float(limit_raw or 1000)
            role = "ADMIN" if sw_admin.get() else "USER"
            data = {"username": username, "password": password, "full_name": full_name,
                    "total_limit": total_limit, "expiration": _to_iso_date(exp_raw), "role": role}
            try:
                r = requests.post(f"{CLOUD_URL}/admin/users", json=data,
                                  headers={"Authorization": f"Bearer {self.auth_manager.token}"}, timeout=10)
                if r.status_code == 200:
                    messagebox.showinfo("Sucesso", "Conta Cloud criada com sucesso!")
                    self.show_admin_subview("list")
                else:
                    detail = r.json().get("detail", "Erro desconhecido no servidor.")
                    messagebox.showerror("Erro de Cadastro", f"O Cloud recusou o registro:\n{detail}")
            except requests.exceptions.ConnectionError:
                messagebox.showerror("Falha de Conexão", "Não foi possível conectar ao servidor Cloud. Verifique sua internet.")
            except Exception as e:
                messagebox.showerror("Erro Crítico", f"Ocorreu uma falha inesperada: {e}")

        ctk.CTkButton(left, text="✓  CRIAR CONTA CLOUD", height=50, corner_radius=12,
                      fg_color=self.color_accent, text_color="#000000",
                      font=ctk.CTkFont(size=14, weight="bold"),
                      command=register).pack(fill="x", padx=30, pady=(20, 30))

        # ── Coluna Direita: calendário ──
        right = ctk.CTkFrame(main, fg_color=C["card"], corner_radius=24,
                             border_width=1, border_color=C["border"])
        right.grid(row=0, column=1, sticky="nsew", padx=(10, 0))

        ctk.CTkLabel(right, text="📅 Data de Expiração",
                     font=ctk.CTkFont(size=20, weight="bold"),
                     text_color=C["white"]).pack(anchor="w", padx=30, pady=(30, 5))
        ctk.CTkLabel(right, text="Selecione quando o acesso do usuário expira",
                     font=ctk.CTkFont(size=12),
                     text_color=C["muted"]).pack(anchor="w", padx=30, pady=(0, 20))

        cal_container = ctk.CTkFrame(right, fg_color=C["card2"], corner_radius=15,
                                     border_width=1, border_color=C["border"])
        cal_container.pack(fill="both", expand=True, padx=15, pady=(0, 30))

        cal = self._add_premium_calendar(cal_container)
        cal.pack(padx=10, pady=10, fill="both", expand=True)

    def _build_admin_edit_view(self, user):
        """ Constrói a interface de edição de usuário como página interna (Integrated View) """
        C = {"bg": "#08090c", "card": "#13141c", "card2": "#1a1b26",
             "border": "#1e2030", "muted": "#64748b", "white": "#e2e8f0"}

        # Limpar view antes de reconstruir
        for widget in self.view_admin_edit.winfo_children(): widget.destroy()

        # ── Header com botão Voltar ──
        hdr = ctk.CTkFrame(self.view_admin_edit, fg_color="transparent")
        hdr.pack(fill="x", pady=(0, 20))

        ctk.CTkButton(hdr, text="←  Voltar", width=100, height=36, corner_radius=8,
                      fg_color="transparent", border_width=1, border_color=C["muted"],
                      text_color=C["muted"], hover_color=C["card"],
                      font=ctk.CTkFont(size=12, weight="bold"),
                      command=lambda: self.show_admin_subview("list")).pack(side="left")

        ctk.CTkLabel(hdr, text=f"Editar Operador: {user['username']}",
                     font=ctk.CTkFont(size=20, weight="bold"),
                     text_color=self.color_text_main).pack(side="left", padx=20)

        # Container principal 2 colunas
        main = ctk.CTkFrame(self.view_admin_edit, fg_color="transparent")
        main.pack(fill="both", expand=True)
        main.grid_columnconfigure(0, weight=1)
        main.grid_columnconfigure(1, weight=1)
        main.grid_rowconfigure(0, weight=1)

        # ── Coluna Esquerda: formulário ──
        left = ctk.CTkFrame(main, fg_color=C["card"], corner_radius=24,
                            border_width=1, border_color=C["border"])
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        ctk.CTkLabel(left, text=f"🆔 Dados de {user['username'].upper()}",
                     font=ctk.CTkFont(size=20, weight="bold"),
                     text_color=C["white"]).pack(anchor="w", padx=30, pady=(30, 20))

        def themed_field(parent, label, val="", placeholder="", icon="", show_char=""):
            c = ctk.CTkFrame(parent, fg_color="transparent")
            c.pack(fill="x", padx=30, pady=6)
            ctk.CTkLabel(c, text=label, font=ctk.CTkFont(size=11, weight="bold"),
                         text_color=C["muted"]).pack(anchor="w", padx=10)
            ff = ctk.CTkFrame(c, fg_color=C["card2"], corner_radius=12,
                               border_width=1, border_color=C["border"], height=48)
            ff.pack(fill="x", pady=(4, 0))
            ff.pack_propagate(False)
            ctk.CTkLabel(ff, text=icon, font=ctk.CTkFont(size=14)).pack(side="left", padx=(15, 10))
            e = ctk.CTkEntry(ff, fg_color="transparent", border_width=0,
                             placeholder_text=placeholder, show=show_char,
                             font=ctk.CTkFont(size=14))
            e.pack(side="left", fill="both", expand=True, padx=(0, 15))
            if val is not None: e.insert(0, str(val))
            return e

        e_name = themed_field(left, "NOME COMPLETO", user["full_name"], "Nome e sobrenome", "🆔")
        e_pass = themed_field(left, "NOVA SENHA (OPCIONAL)", "", "Deixe vazio para manter", "🔑", show_char="*")

        # Limite + switch Ilimitado
        ext = ctk.CTkFrame(left, fg_color="transparent")
        ext.pack(fill="x", padx=30, pady=6)

        lim_col = ctk.CTkFrame(ext, fg_color="transparent")
        lim_col.pack(side="left", fill="x", expand=True, padx=(0, 8))

        lbl_lim = ctk.CTkFrame(lim_col, fg_color="transparent")
        lbl_lim.pack(fill="x")
        ctk.CTkLabel(lbl_lim, text="LIMITE DE CRÉDITOS",
                     font=ctk.CTkFont(size=11, weight="bold"),
                     text_color=C["muted"]).pack(side="left", padx=10)

        sw_unlimited = ctk.CTkSwitch(lbl_lim, text="Ilimitado",
                                     font=ctk.CTkFont(size=11, weight="bold"),
                                     progress_color=self.color_accent,
                                     text_color=self.color_accent)
        sw_unlimited.pack(side="right")

        ff_lim = ctk.CTkFrame(lim_col, fg_color=C["card2"], corner_radius=12,
                              border_width=1, border_color=C["border"], height=48)
        ff_lim.pack(fill="x", pady=(4, 0))
        ff_lim.pack_propagate(False)
        ctk.CTkLabel(ff_lim, text="💳", font=ctk.CTkFont(size=14)).pack(side="left", padx=(15, 10))
        e_limit = ctk.CTkEntry(ff_lim, fg_color="transparent", border_width=0, font=ctk.CTkFont(size=14))
        e_limit.pack(side="left", fill="both", expand=True)
        
        # Preencher limite anterior
        is_inf = user["total_limit"] >= 9000000
        e_limit.insert(0, "∞ (Ilimitado)" if is_inf else str(int(user["total_limit"])))
        if is_inf:
            sw_unlimited.select()
            e_limit.configure(state="disabled")

        def toggle_unlimited():
            if sw_unlimited.get():
                e_limit.delete(0, "end")
                e_limit.insert(0, "∞ (Ilimitado)")
                e_limit.configure(state="disabled")
            else:
                e_limit.configure(state="normal")
                e_limit.delete(0, "end")
                e_limit.insert(0, str(int(user["total_limit"])) if not is_inf else "1000")
        sw_unlimited.configure(command=toggle_unlimited)

        # Nível de acesso
        adm_col = ctk.CTkFrame(ext, fg_color="transparent")
        adm_col.pack(side="left", fill="x", expand=True, padx=(8, 0))
        ctk.CTkLabel(adm_col, text="NÍVEL DE ACESSO",
                     font=ctk.CTkFont(size=11, weight="bold"),
                     text_color=C["muted"]).pack(anchor="w", padx=10)
        sw_f = ctk.CTkFrame(adm_col, fg_color=C["card2"], corner_radius=12,
                            border_width=1, border_color=C["border"], height=48)
        sw_f.pack(fill="x", pady=(4, 0))
        sw_f.pack_propagate(False)
        sw_admin = ctk.CTkSwitch(sw_f, text="Administrador",
                                 font=ctk.CTkFont(size=12, weight="bold"),
                                 progress_color="#ef4444", text_color=C["white"])
        sw_admin.place(relx=0.5, rely=0.5, anchor="center")
        if user.get("role") == "ADMIN": sw_admin.select()

        # Botão atualizar
        def update():
            try:
                limit_val = 9999999 if sw_unlimited.get() else float(e_limit.get() or 0)
                role = "ADMIN" if sw_admin.get() else "USER"
                data = {
                    "full_name": e_name.get(), 
                    "total_limit": limit_val, 
                    "expiration": _to_iso_date(cal.get_date()),
                    "role": role
                }
                if e_pass.get(): data["password"] = e_pass.get()
                
                r = requests.put(f"{CLOUD_URL}/admin/users/{user['username']}", json=data, 
                                headers={"Authorization": f"Bearer {self.auth_manager.token}"})
                if r.status_code == 200:
                    messagebox.showinfo("Sucesso", "Operador atualizado com sucesso!")
                    self.show_admin_subview("list")
                else: messagebox.showerror("Erro Cloud", r.json().get('detail'))
            except Exception as e: messagebox.showerror("Erro", str(e))

        ctk.CTkButton(left, text="✓  ATUALIZAR DADOS", height=50, corner_radius=12,
                      fg_color=self.color_accent, text_color="#000000",
                      font=ctk.CTkFont(size=14, weight="bold"),
                      command=update).pack(fill="x", padx=30, pady=(20, 30))

        # ── Coluna Direita: calendário ──
        right = ctk.CTkFrame(main, fg_color=C["card"], corner_radius=24,
                             border_width=1, border_color=C["border"])
        right.grid(row=0, column=1, sticky="nsew", padx=(10, 0))

        ctk.CTkLabel(right, text="📅 Data de Expiração",
                     font=ctk.CTkFont(size=20, weight="bold"),
                     text_color=C["white"]).pack(anchor="w", padx=30, pady=(30, 5))
        ctk.CTkLabel(right, text="Selecione quando o acesso do usuário expira",
                     font=ctk.CTkFont(size=12),
                     text_color=C["muted"]).pack(anchor="w", padx=30, pady=(0, 20))

        cal_container = ctk.CTkFrame(right, fg_color=C["card2"], corner_radius=15,
                                     border_width=1, border_color=C["border"])
        cal_container.pack(fill="both", expand=True, padx=15, pady=(0, 30))

        cal = self._add_premium_calendar(cal_container, user["expiration"])
        cal.pack(padx=10, pady=10, fill="both", expand=True)

    def _build_admin_monitor_view(self):
        """ Constrói a interface de monitoramento em tempo real """
        f = self.view_admin_monitor
        for w in f.winfo_children(): w.destroy()

        # Header
        hdr = ctk.CTkFrame(f, fg_color="transparent")
        hdr.pack(fill="x", pady=(0, 20))

        ctk.CTkButton(hdr, text="←  Voltar", width=100, height=36, corner_radius=8,
                      fg_color="transparent", border_width=1, border_color=self.color_text_dim,
                      text_color=self.color_text_dim, hover_color=self.color_card,
                      font=ctk.CTkFont(size=12, weight="bold"),
                      command=lambda: self.show_admin_subview("list")).pack(side="left")

        ctk.CTkLabel(hdr, text="Monitoramento Real-Time do Servidor",
                     font=ctk.CTkFont(size=20, weight="bold"),
                     text_color=self.color_text_main).pack(side="left", padx=20)

        # Container Principal
        container = ctk.CTkFrame(f, fg_color="transparent")
        container.pack(fill="both", expand=True)
        container.grid_columnconfigure((0, 1, 2), weight=1)

        # 1. Cards de Sistema
        def make_monitor_card(col, title, icon, color):
            card = ctk.CTkFrame(container, fg_color=self.color_card, corner_radius=20, border_width=1, border_color=self.color_border)
            card.grid(row=0, column=col, padx=10, pady=10, sticky="nsew")
            ctk.CTkLabel(card, text=icon, font=ctk.CTkFont(size=24)).pack(pady=(20, 5))
            ctk.CTkLabel(card, text=title, font=ctk.CTkFont(size=12, weight="bold"), text_color=self.color_text_dim).pack()
            val = ctk.CTkLabel(card, text="--%", font=ctk.CTkFont(size=32, weight="bold"), text_color=color)
            val.pack(pady=(5, 10))
            pbar = ctk.CTkProgressBar(card, height=8, progress_color=color, fg_color=self.color_border)
            pbar.pack(fill="x", padx=30, pady=(0, 25))
            pbar.set(0)
            return val, pbar

        self.mon_cpu_val, self.mon_cpu_bar = make_monitor_card(0, "Carga de CPU", "⚡", self.color_accent)
        self.mon_ram_val, self.mon_ram_bar = make_monitor_card(1, "Memória RAM", "🧠", self.color_success)
        self.mon_disk_val, self.mon_disk_bar = make_monitor_card(2, "Espaço em Disco", "💽", self.color_warning)

        # 2. ClickHouse & Engine Status (Row 2)
        row2 = ctk.CTkFrame(f, fg_color="transparent")
        row2.pack(fill="x", pady=10)
        row2.grid_columnconfigure((0, 1), weight=1)

        # ClickHouse Details
        ch_card = ctk.CTkFrame(row2, fg_color=self.color_card, corner_radius=20, border_width=1, border_color=self.color_border)
        ch_card.grid(row=0, column=0, padx=10, sticky="nsew")
        ctk.CTkLabel(ch_card, text="📊 BANCO DE DADOS (CLICKHOUSE)", font=ctk.CTkFont(size=14, weight="bold"), text_color=self.color_text_main).pack(pady=(20, 15))
        
        self.mon_ch_status = ctk.CTkLabel(ch_card, text="STATUS: --", font=ctk.CTkFont(size=12, weight="bold"))
        self.mon_ch_status.pack()
        
        self.mon_ch_info = ctk.CTkLabel(ch_card, text="Queries: -- | RAM: -- GB\nUptime: --", 
                                        font=ctk.CTkFont(size=13), text_color=self.color_text_dim, justify="center")
        self.mon_ch_info.pack(pady=(5, 20))

        # Engine Details
        eng_card = ctk.CTkFrame(row2, fg_color=self.color_card, corner_radius=20, border_width=1, border_color=self.color_border)
        eng_card.grid(row=0, column=1, padx=10, sticky="nsew")
        ctk.CTkLabel(eng_card, text="⚙️ MOTOR HEMN (TASKS)", font=ctk.CTkFont(size=14, weight="bold"), text_color=self.color_text_main).pack(pady=(20, 15))
        
        self.mon_eng_info = ctk.CTkLabel(eng_card, text="Ativas: -- | Fila: --\nSlots Livres (Semáforo): --", 
                                         font=ctk.CTkFont(size=13), text_color=self.color_text_dim, justify="center")
        self.mon_eng_info.pack(pady=(5, 20))

    def start_monitor_polling(self):
        """ Inicia a thread de polling para o monitoramento """
        if getattr(self, "_is_polling_monitor", False): return
        self._is_polling_monitor = True
        
        def poll_loop():
            while getattr(self, "_is_polling_monitor", False):
                if not self.auth_manager.token: break
                try:
                    headers = {"Authorization": f"Bearer {self.auth_manager.token}"}
                    r = requests.get(f"{CLOUD_URL}/admin/monitor/stats", headers=headers, timeout=5)
                    if r.status_code == 200:
                        data = r.json()
                        self.after(0, lambda: self._update_monitor_ui(data))
                except Exception as e:
                    print(f"Monitor Poll Error: {e}")
                    self.after(0, lambda: self.mon_ch_status.configure(text="STATUS: ERRO DE CONEXÃO", text_color=self.color_danger))
                
                import time
                time.sleep(5)
        
        threading.Thread(target=poll_loop, daemon=True).start()

    def _update_monitor_ui(self, data):
        """ Atualiza os widgets com os dados recebidos do servidor """
        try:
            # System Metrics
            sys = data.get("system", {})
            cpu = sys.get("cpu", 0)
            ram = sys.get("ram", 0)
            disk = sys.get("disk", 0)

            self.mon_cpu_val.configure(text=f"{cpu}%")
            self.mon_cpu_bar.set(cpu / 100)
            
            self.mon_ram_val.configure(text=f"{ram}%")
            self.mon_ram_bar.set(ram / 100)

            self.mon_disk_val.configure(text=f"{disk}%")
            self.mon_disk_bar.set(disk / 100)

            # ClickHouse
            ch = data.get("clickhouse", {})
            self.mon_ch_status.configure(text=f"STATUS: {ch.get('status', 'OFFLINE')}", 
                                         text_color=self.color_success if ch.get('status') == "ONLINE" else self.color_danger)
            
            ch_ram = ch.get('memory_usage_bytes', 0) / 1024 / 1024 / 1024
            uptime = ch.get('uptime_seconds', 0) / 3600
            self.mon_ch_info.configure(text=f"Queries: {ch.get('active_queries', 0)} | RAM: {ch_ram:.2f} GB\nUptime: {uptime:.1f} hrs")

            # Engine
            eng = data.get("engine", {})
            tasks = eng.get("tasks", {})
            self.mon_eng_info.configure(text=f"Ativas: {tasks.get('active', 0)} | Fila: {tasks.get('queued', 0)}\nSlots Livres (Semáforo): {eng.get('enrich_slots_available', '--')}")

        except Exception as e:
            print(f"UI Update Error: {e}")

    def refresh_admin_list(self):
        if not self.auth_manager.token: return
        
        for w in self.user_rows:
            try: w.destroy()
            except: pass
        self.user_rows = []

        headers = {"Authorization": f"Bearer {self.auth_manager.token}"}
        def fetch():
            try:
                r = requests.get(f"{CLOUD_URL}/admin/users", headers=headers, timeout=8)
                if r.status_code == 200:
                    users = r.json()
                    self.all_users = users
                    self.after(0, lambda: self._populate_admin_list(users))
                else:
                    self.after(0, lambda: messagebox.showerror("Erro Cloud", "Falha na sincronização."))
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Servidor Offline", f"Cloud inacessível: {e}"))
        threading.Thread(target=fetch, daemon=True).start()

    def _populate_admin_list(self, users):
        for w in self.user_rows:
            try: w.destroy()
            except: pass
        self.user_rows = []

        total   = len(users)
        active  = sum(1 for u in users if u["status"] == "ACTIVE")
        blocked = total - active
        credits_used = sum(u["current_usage"] for u in users)

        self.stat_widgets["total"].configure(text=str(total))
        self.stat_widgets["active"].configure(text=str(active))
        self.stat_widgets["blocked"].configure(text=str(blocked))
        self.stat_widgets["credits"].configure(text=f"{credits_used:,.0f}")

        if not users:
            lbl = ctk.CTkLabel(self.admin_list_scroll,
                               text="Nenhum usuário encontrado.",
                               text_color=self.color_text_dim,
                               font=ctk.CTkFont(size=13))
            lbl.grid(row=0, column=0, columnspan=3, pady=40)
            self.user_rows.append(lbl)
            return

        for i, u in enumerate(users):
            self.create_user_card_admin(u, i)

    def create_user_card_admin(self, user, index):
        """ Card estilo HEMN_Admin_Panel.py — dark, avatar colorido, progress bar """
        is_active    = user["status"] == "ACTIVE"
        status_color = "#22c55e" if is_active else "#ef4444"
        status_text  = "ATIVO" if is_active else "BLOQUEADO"
        br_exp       = _to_br_date(user["expiration"])

        card = ctk.CTkFrame(self.admin_list_scroll, fg_color="#13141c",
                            corner_radius=16, border_width=1, border_color="#1e2030")
        card.grid(row=index // 3, column=index % 3, padx=10, pady=10, sticky="nsew")
        self.user_rows.append(card)

        # 1. Header: Avatar circular + Badge
        hdr = ctk.CTkFrame(card, fg_color="transparent")
        hdr.pack(fill="x", padx=15, pady=(15, 8))

        initial = (user["full_name"][0].upper() if user["full_name"] else "?")
        colors  = ["#3b82f6", "#8b5cf6", "#ec4899", "#f59e0b", "#10b981"]
        c_idx   = ord(initial) % len(colors)

        avatar = ctk.CTkFrame(hdr, width=44, height=44, corner_radius=22,
                              fg_color=colors[c_idx])
        avatar.pack(side="left")
        avatar.pack_propagate(False)
        ctk.CTkLabel(avatar, text=initial,
                     font=ctk.CTkFont(size=18, weight="bold"),
                     text_color="white").place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(hdr, text=status_text,
                     font=ctk.CTkFont(size=9, weight="bold"),
                     fg_color=status_color, text_color="white",
                     corner_radius=10, width=70, height=20).pack(side="right", anchor="n")

        # 2. Body: Nome + username/role
        body = ctk.CTkFrame(card, fg_color="transparent")
        body.pack(fill="x", padx=18, pady=(0, 10))

        ctk.CTkLabel(body, text=user["full_name"],
                     font=ctk.CTkFont(size=15, weight="bold"),
                     text_color=self.color_text_main, anchor="w").pack(fill="x")
        ctk.CTkLabel(body, text=f"@{user['username']} • {user['role']}",
                     font=ctk.CTkFont(size=11),
                     text_color="#64748b", anchor="w").pack(fill="x")

        # 3. Info box: Expiração + Créditos + Progress bar
        info = ctk.CTkFrame(card, fg_color="#1a1b26", corner_radius=10)
        info.pack(fill="x", padx=12, pady=(0, 12))

        exp_f = ctk.CTkFrame(info, fg_color="transparent")
        exp_f.pack(fill="x", padx=10, pady=(8, 4))
        ctk.CTkLabel(exp_f, text="📅", font=ctk.CTkFont(size=12)).pack(side="left")
        ctk.CTkLabel(exp_f, text=f"Expira em {br_exp}",
                     font=ctk.CTkFont(size=10, weight="bold"),
                     text_color=self.color_text_main).pack(side="left", padx=6)

        usage_f = ctk.CTkFrame(info, fg_color="transparent")
        usage_f.pack(fill="x", padx=10, pady=(0, 8))

        if user["total_limit"] >= 9000000:
            usage_text = "Créditos Ilimitados (∞)"
            pct = 0
        else:
            pct = (user["current_usage"] / user["total_limit"] * 100) if user["total_limit"] > 0 else 0
            usage_text = f"{user['current_usage']:.0f} / {user['total_limit']:.0f} créd."

        hdr_usage = ctk.CTkFrame(usage_f, fg_color="transparent")
        hdr_usage.pack(fill="x")
        ctk.CTkLabel(hdr_usage, text="💳", font=ctk.CTkFont(size=12)).pack(side="left")
        ctk.CTkLabel(hdr_usage, text=usage_text,
                     font=ctk.CTkFont(size=10, weight="bold"),
                     text_color=self.color_text_main).pack(side="left", padx=6)

        pb = ctk.CTkProgressBar(usage_f, height=5, corner_radius=3,
                                progress_color=status_color)
        pb.pack(fill="x", pady=(5, 0))
        if user["total_limit"] >= 9000000:
            pb.configure(progress_color=self.color_accent)
            pb.set(0)
        else:
            pb.set(min(1.0, pct / 100))

        # 4. Botões de ação
        act = ctk.CTkFrame(card, fg_color="transparent")
        act.pack(fill="x", padx=12, pady=(0, 15))

        ctk.CTkButton(act, text="Editar", height=28, corner_radius=8,
                      fg_color=self.color_accent, text_color="#000000",
                      hover_color=self.color_accent,
                      font=ctk.CTkFont(size=10, weight="bold"),
                      command=lambda u=user: self.show_admin_subview("edit", u)
                      ).pack(side="left", fill="x", expand=True, padx=(0, 4))

        toggle_text  = "Ativar" if not is_active else "Bloquear"
        toggle_color = "#22c55e" if not is_active else "#ef4444"
        ctk.CTkButton(act, text=toggle_text, height=28, corner_radius=8,
                      fg_color="transparent", border_width=1, border_color=toggle_color,
                      text_color=toggle_color, hover_color="#1a1b26",
                      font=ctk.CTkFont(size=10, weight="bold"),
                      command=lambda u=user: self.toggle_user_status_admin(u)
                      ).pack(side="left", fill="x", expand=True)


    def toggle_user_status_admin(self, user):
        new_status = "BLOCKED" if user["status"] == "ACTIVE" else "ACTIVE"
        headers = {"Authorization": f"Bearer {self.auth_manager.token}"}
        try:
            r = requests.put(f"{CLOUD_URL}/admin/users/{user['username']}", 
                             json={"status": new_status}, headers=headers, timeout=10)
            if r.status_code == 200:
                self.refresh_admin_list()
            else:
                detail = r.json().get('detail', 'Erro de permissão ou estado.')
                messagebox.showerror("Erro Operacional", f"O Cloud recusou a alteração:\n{detail}")
        except requests.exceptions.ConnectionError:
            messagebox.showerror("Servidor Offline", "Sem conexão com o Cloud para alterar status.")
        except Exception as e:
            messagebox.showerror("Erro", f"Falha na comunicação: {e}")




    def show_frame(self, fid):
        for f in self.frames.values(): f.grid_forget()
        self.frames[fid].grid(row=0, column=0, sticky="nsew")

    def show_unify_frame(self): self.show_frame("unify")
    def show_manual_frame(self): self.show_frame("manual")
    def show_batch_frame(self): self.show_frame("batch")
    def show_extract_frame(self): self.show_frame("extract")
    def show_split_frame(self): self.show_frame("split")
    def show_settings_frame(self): self.show_frame("settings")
    def show_carrier_frame(self): self.show_frame("carrier")
    def show_coverage_frame(self): self.show_frame("coverage")

    def select_source(self): 
        path = filedialog.askdirectory()
        if path: [self.src_entry.delete(0, 'end'), self.src_entry.insert(0, path)]
    
    def select_destination(self):
        data_hora = datetime.now().strftime("%d-%m-%Y_%H-%M")
        sug_nome = f"Consolidado_{data_hora}.xlsx"
        path = filedialog.asksaveasfilename(defaultextension=".xlsx", initialfile=sug_nome, filetypes=[("Excel files", "*.xlsx")])
        if path: [self.dst_entry.delete(0, 'end'), self.dst_entry.insert(0, path)]

    def select_input_file(self):
        path = filedialog.askopenfilename(filetypes=[("Excel/CSV files", "*.xlsx *.csv")])
        if path: 
            self.input_file.delete(0, 'end')
            self.input_file.insert(0, path)
            
            # Auto-popular colunas do arquivo SE for selecionado na aba Batch
            # (Usando thread para não travar a interface)
            if hasattr(self, 'name_col'):
                threading.Thread(target=self._load_file_headers, args=(path,)).start()

    def select_carrier_input(self):
        path = filedialog.askopenfilename(filetypes=[("Excel/CSV files", "*.xlsx *.csv")])
        if path:
            self.carrier_input_file.delete(0, 'end')
            self.carrier_input_file.insert(0, path)
            threading.Thread(target=self._load_carrier_headers, args=(path,)).start()

    def select_carrier_output(self):
        data_hora = datetime.now().strftime("%d-%m-%Y_%H-%M")
        sug_nome = f"Operadoras_{data_hora}.xlsx"
        path = filedialog.asksaveasfilename(defaultextension=".xlsx", initialfile=sug_nome, filetypes=[("Excel files", "*.xlsx")])
        if path: [self.carrier_output_file.delete(0, 'end'), self.carrier_output_file.insert(0, path)]

    def _load_file_headers(self, path):
        import pandas as pd
        try:
            self.name_col.set("Carregando colunas...")
            self.cpf_col.set("Carregando colunas...")
            
            headers = []
            if path.lower().endswith(".csv"):
                # Detectar separador
                sep = ';'
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        primeira = f.readline()
                        if ';' not in primeira and ',' in primeira: sep = ','
                except:
                    pass
                df = pd.read_csv(path, nrows=0, sep=sep, encoding='utf-8', on_bad_lines='skip')
                headers = list(df.columns)
            else:
                df = pd.read_excel(path, nrows=0)
                headers = list(df.columns)
                
            headers = [str(x) for x in headers]
            
            # Atualiza GUI thread safe
            def update_gui():
                if headers:
                    self.name_col.configure(values=headers)
                    self.cpf_col.configure(values=headers)
                    self.name_col.set(headers[0])
                    self.cpf_col.set(headers[1] if len(headers) > 1 else headers[0])
                else:
                    self.name_col.set("")
                    self.cpf_col.set("")
                    
            self.after(0, update_gui)
        except Exception as e:
            def err_gui():
                self.name_col.set("Erro")
                self.cpf_col.set("Erro")
            self.after(0, err_gui)

    def _load_carrier_headers(self, path):
        import pandas as pd
        try:
            self.carrier_phone_col.set("Carregando colunas...")
            headers = []
            if path.lower().endswith(".csv"):
                sep = ';'
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        primeira = f.readline()
                        if ';' not in primeira and ',' in primeira: sep = ','
                except: pass
                df = pd.read_csv(path, nrows=0, sep=sep, encoding='utf-8', on_bad_lines='skip')
                headers = list(df.columns)
            else:
                df = pd.read_excel(path, nrows=0)
                headers = list(df.columns)
                
            headers = [str(x) for x in headers]
            def update_gui():
                if headers:
                    self.carrier_phone_col.configure(values=headers)
                    self.carrier_phone_col.set(headers[0])
                else:
                    self.carrier_phone_col.set("")
            self.after(0, update_gui)
        except Exception as e:
            def err_gui(): self.carrier_phone_col.set("Erro")
            self.after(0, err_gui)

    def select_output_file(self):
        data_hora = datetime.now().strftime("%d-%m-%Y_%H-%M")
        sug_nome = f"Cruzamento_Lote_{data_hora}.csv"
        path = filedialog.asksaveasfilename(defaultextension=".csv", initialfile=sug_nome, filetypes=[("CSV UTF-8", "*.csv")])
        if path: 
            self.output_file.delete(0, 'end')
            self.output_file.insert(0, path)

    def select_output_extract(self):
        data_hora = datetime.now().strftime("%d-%m-%Y_%H-%M")
        cidade = self.f_cidade.get().strip()
        sug_nome = f"Extracao_{cidade}_{data_hora}.csv" if cidade else f"Extracao_{data_hora}.csv"
        path = filedialog.asksaveasfilename(defaultextension=".csv", initialfile=sug_nome, filetypes=[("Arquivo CSV (Ultra Rápido)", "*.csv"), ("Excel files", "*.xlsx")])
        if path: [self.output_extract.delete(0, 'end'), self.output_extract.insert(0, path)]
        
    def select_excel_cep(self):
        path = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx *.xls"), ("CSV files", "*.csv")])
        if path: [self.f_excel_cep.delete(0, 'end'), self.f_excel_cep.insert(0, path)]
        
    def select_split_input(self):
        path = filedialog.askopenfilename(filetypes=[("Arquivos CSV ou Excel", "*.csv *.xlsx *.xls")])
        if path: [self.split_input.delete(0, 'end'), self.split_input.insert(0, path)]

    def select_split_output(self):
        data_hora = datetime.now().strftime("%d-%m-%Y_%H-%M")
        sug_nome = f"Arquivo_Dividido_{data_hora}.xlsx"
        path = filedialog.asksaveasfilename(defaultextension=".xlsx", initialfile=sug_nome, filetypes=[("Excel files", "*.xlsx")])
        if path: [self.split_output.delete(0, 'end'), self.split_output.insert(0, path)]

    def run_extract(self):
        if not self.check_license(): return
        db = self.db_extract.get()
        if not db: return messagebox.showwarning("Erro", "Selecione o banco de dados.")
        
        filters = {
            "CIDADE": self.f_cidade.get(),
            "UF": self.f_uf.get(),
            "CNAE": self.f_cnae.get(),
            "SITUAÇÃO": self.f_situacao.get() if self.f_situacao.get() != "TODAS" else "",
            "TIPO_TELEFONE": self.f_tipo_tel.get() if self.f_tipo_tel.get() != "TODOS" else "",
            "EXCEL_CEP": self.f_excel_cep.get(),
            "SOMENTE_COM_TELEFONE": self.var_extract_phone.get()
        }
        
        if not any([filters["CIDADE"], filters["UF"], filters["CNAE"], filters["SITUAÇÃO"], filters["EXCEL_CEP"]]):
            return messagebox.showwarning("Erro", "Preencha algum critério de filtro ou insira a Planilha CEP.")

        self.btn_extract_run.configure(state="disabled")
        self.extract_log.delete("1.0", "end")
        self.extract_pbar.set(0)

        def count_task():
            import sqlite3
            self.append_log("Calculando volume de dados da extração... Por favor aguarde.")
            try:
                # Usa o banco selecionado para contar. No app original é PATH_DB_CNPJ, mas aqui o user escolhe um.
                # Se o banco for o padrão C:\HEMN_SYSTEM_DB\cnpj.db
                conn = sqlite3.connect(db)
                cursor = conn.cursor()
                # Query de contagem simples para orçamento rápido. Usaremos filtros básicos.
                # Em um cenário real, essa query seria idêntica à do engine.
                # Para evitar duplicar 500 linhas de SQL, vamos estimar ou usar um COUNT básico.
                cursor.execute("SELECT COUNT(*) FROM estabelecimento") # Exemplo para o diálogo
                total_found = cursor.fetchone()[0]
                conn.close()
            except:
                total_found = 1000 # Valor de segurança se a query de contagem der erro
            
            self.after(0, lambda: self._confirm_and_run_extract(db, filters, total_found))

        threading.Thread(target=count_task, daemon=True).start()

    def _confirm_and_run_extract(self, db, filters, total_found):
        qty = self.ask_credit_confirmation(total_found, 1.0, "Extração de Inteligência")
        if not qty:
            self.btn_extract_run.configure(state="normal")
            return
            
        out = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV UTF-8", "*.csv"), ("Excel", "*.xlsx")])
        if not out:
            self.btn_extract_run.configure(state="normal")
            return
            
        def on_finish(count):
            self.auth_manager.debit_credits(count * 1.0)
            self.after(0, self.update_license_ui)

        def task():
            self.engine.progress_callback = lambda current, total: self.after(0, lambda: self.extract_pbar.set(current / total))
            success = self.engine.extract_by_filter(db, out, filters, limit=qty)
            self.after(0, lambda: self.btn_extract_run.configure(state="normal"))
            if success:
                on_finish(qty)
                self.after(0, lambda: [messagebox.showinfo("Sucesso", f"Extração concluída! {qty} registros salvos."), self.reset_module_ui("extract")])

        threading.Thread(target=task, daemon=True).start()

    def run_split(self):
        if not self.check_license(): return
        inp, out = self.split_input.get(), self.split_output.get()
        if not inp or not out:
            return messagebox.showwarning("Erro", "Arquivos de Entrada e Saída são obrigatórios para a divisão.")
        
        self.btn_split_run.configure(state="disabled")
        self.split_log.delete("1.0", "end")
        self.engine.stop_requested = False
        self.split_pbar.set(0)
        
        self.engine.progress_callback = lambda current, total: self.after(0, lambda: self.split_pbar.set(current / total if total > 0 else 0))
        
        def task():
            success = self.engine.split_large_file(inp, out)
            self.after(0, lambda: self.btn_split_run.configure(state="normal"))
            self.after(0, lambda: self.split_pbar.stop())
            self.after(0, lambda: self.split_pbar.configure(mode="determinate"))
            if success:
                self.after(0, lambda: [messagebox.showinfo("Sucesso", "O arquivo foi dividido em abas com sucesso!"), self.reset_module_ui("split")])
            else:
                self.after(0, lambda: messagebox.showwarning("Erro", "Ocorreu um erro ao dividir o arquivo. Leia o registro para detalhes."))
                
        self.split_pbar.configure(mode="determinate")
        threading.Thread(target=task, daemon=True).start()

    def run_database_optimization(self):
        db = self.db_extract.get()
        if not db:
            return messagebox.showwarning("Erro", "Selecione o arquivo do banco de dados primeiro.")
            
        confirm = messagebox.askyesno("Otimização Estrutural", 
            "Esse processo criará índices para tornar as buscas instantâneas.\nPode demorar de 10 a 20 minutos e o computador vai ficar processando pesado.\n\nDeseja continuar?")
        if not confirm: return
        
        self.btn_tune.configure(state="disabled")
        self.btn_extract_run.configure(state="disabled")
        self.extract_log.delete("1.0", "end")
        self.extract_pbar.configure(mode="indeterminate")
        self.extract_pbar.start()
        
        self.engine.progress_callback = lambda c, t: None # No progress for tuning
        
        def task():
            success = self.engine.optimize_database(db)
            self.after(0, lambda: self.btn_tune.configure(state="normal"))
            self.after(0, lambda: self.btn_extract_run.configure(state="normal"))
            self.after(0, lambda: self.extract_pbar.stop())
            self.after(0, lambda: self.extract_pbar.configure(mode="determinate"))
            if success:
                self.after(0, lambda: messagebox.showinfo("Sucesso", "Banco formatado para ALTA PERFORMANCE de elite!"))
        
        threading.Thread(target=task, daemon=True).start()

    def run_cron_setup(self):
        # Dispara o PowerShell para registrar do Scheduled Task
        ps_script = resource_path("setup_cronjob.ps1")
        if not os.path.exists(ps_script):
             ps_script = resource_path(os.path.join("_internal", "setup_cronjob.ps1"))
             
        try:
            import subprocess
            subprocess.run(["powershell.exe", "-ExecutionPolicy", "Bypass", "-File", ps_script], check=True, creationflags=subprocess.CREATE_NO_WINDOW)
            
            if hasattr(self, 'cron_status_tag'):
                self.cron_status_tag.configure(text="●  O.S CRONJOB ATIVO", text_color="#00d26a")
                
            messagebox.showinfo("Sucesso", "Rotinas Automáticas Nativas registradas no Windows com Sucesso!\n\nAgora seu PC tomará conta do Banco de Dados nos dias 13 e 28 às 19:30 automaticamente.")
        except Exception as e:
            messagebox.showerror("Erro de Permissão", f"Falha ao registrar agendador no Windows O.S: {e}")
            if hasattr(self, 'cron_switch'):
                self.cron_switch.deselect()

    def start_unification(self):
        if not self.check_license(): return
        src, dst = self.src_entry.get(), self.dst_entry.get()
        if not src or not dst: return messagebox.showwarning("Aviso", "Preencha origem e destino.")
        self.btn_unify_run.configure(state="disabled")
        self.log_box.delete("1.0", "end")
        self.engine.target_dir, self.engine.output_file = src, dst
        threading.Thread(target=self._exec_unify, daemon=True).start()

    def _exec_unify(self):
        self.engine.consolidate()
        self.after(0, lambda: [self.btn_unify_run.configure(state="normal"), 
                               messagebox.showinfo("Sucesso", "Unificação concluída!"),
                               self.reset_module_ui("unify")])

    def run_manual_search(self):
        if not self.check_license(): return
        
        # Consumo de 0.5 crédito por busca manual
        status = self.auth_manager.get_status_summary()
        u_data = self.auth_manager.user_data
        
        if not u_data:
            messagebox.showerror("Erro de Sessão", "Dados de usuário não encontrados. Faça login novamente.")
            return

        usage_val = u_data.get("current_usage", 0)
        limit_val = u_data.get("total_limit", 1000)
        
        if usage_val + 0.5 > limit_val:
            messagebox.showwarning("Créditos Insuficientes", "Você não tem créditos suficientes (0.5 necessário).")
            return

        db = self.db_manual.get()
        name = self.name_entry.get().strip()
        cpf = self.cpf_entry.get().strip()
        # only_phone fixo em False para busca manual (sempre trás tudo conforme solicitado)
        only_phone = False
        
        if not name and not cpf:
            return messagebox.showwarning("Erro", "Insira Nome ou CPF para pesquisar.")
            
        self.manual_log.delete("1.0", "end")
        self.manual_log.insert("end", f"> Alocando recursos de busca...\n")
        self.manual_log.insert("end", f"> Alvo: {name} | Doc: {cpf}\n")
        
        def run_all():
            try:
                # 1. Debitar créditos em background (evita lag se server estiver lento)
                self.after(0, lambda: self.manual_log.insert("end", "> Validando créditos na nuvem...\n"))
                self.auth_manager.debit_credits(0.5)
                self.after(0, self.update_license_ui)
                
                # 2. Executar busca
                self.after(0, lambda: self.manual_log.insert("end", "> Consultando banco de dados local (41GB)...\n"))
                
                # Redirecionar logs da engine para o log manual temporariamente
                original_log = self.engine.log_callback
                def manual_engine_log(m):
                    self.after(0, lambda: [self.manual_log.insert("end", f"engine> {m}\n"), self.manual_log.see("end")])
                
                self.engine.log_callback = manual_engine_log
                try:
                    df = self.engine.search_cnpj_by_name_cpf(db, name, cpf, only_with_phone=only_phone)
                finally:
                    self.engine.log_callback = original_log

                # 3. Mostrar resultados
                self.after(0, lambda: self._show_results(df))
            except Exception as e:
                import traceback
                err_msg = traceback.format_exc()
                self.after(0, lambda: [
                    self.manual_log.insert("end", f"[!] ERRO FATAL: {str(e)}\n"),
                    self.manual_log.insert("end", f"{err_msg}\n"),
                    self.manual_log.see("end")
                ])

        threading.Thread(target=run_all, daemon=True).start()

    def _exec_manual(self, db, name, cpf, only_phone):
        try:
            df = self.engine.search_cnpj_by_name_cpf(db, name, cpf, only_with_phone=only_phone)
            self.after(0, self._show_results, df)
        except Exception as e:
            self.after(0, lambda: self.manual_log.insert("end", f"[!] ERRO INTERNO: {e}\n"))

    def _show_results(self, df):
        if df is None or df.empty:
            self.manual_log.insert("end", "[!] Nenhum registro localizado.\n")
            self.manual_log.see("end")
            return
        self.manual_log.insert("end", f"[+] Encontrados {len(df)} registros:\n\n")
        for _, row in df.iterrows():
            info = f"RAZÃO SOCIAL: {row['razao_social']}\n"
            info += f"CNPJ: {row['cnpj_completo']} | SITUAÇÃO: {row['situacao']}\n"
            info += f"ENDEREÇO: {row['endereco_completo']}\n"
            
            if row['telefone_novo']:
                cont_str = f"({row['ddd_novo']}) {row['telefone_novo']} [{row['tipo_telefone']}]"
            else:
                cont_str = "SEM CONTATO VÁLIDO"
                
            info += f"CONTATO: {cont_str} | EMAIL: {row['email_novo']}\n"
            info += "-"*45 + "\n"
            self.manual_log.insert("end", info)

    def run_batch_search(self):
        if not self.check_license(): return
        
        db = self.db_batch.get()
        inp = self.input_file.get()
        nc = self.name_col.get()
        cc = self.cpf_col.get()
        only_phone = self.check_batch_phone.get()
        
        if not inp or not nc:
            return messagebox.showwarning("Erro", "Selecione o arquivo e a coluna de Nomes.")
            
        # 1. Contagem de Linhas para Orçamento
        try:
            if inp.endswith('.csv'):
                with open(inp, 'r', encoding='utf-8', errors='ignore') as f:
                    total_lines = sum(1 for line in f) - 1
            else:
                import pandas as pd
                df_temp = pd.read_excel(inp, usecols=[nc])
                total_lines = len(df_temp)
        except Exception as e:
            return messagebox.showerror("Erro ao ler arquivo", f"Não foi possível contar as linhas: {e}")

        # 2. Confirmação de Créditos (Rate 1.0)
        qty_to_process = self.ask_credit_confirmation(total_lines, 1.0, "Busca em Lote")
        if not qty_to_process: return
        
        # 3. Local de Salvamento
        out = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV UTF-8", "*.csv"), ("Excel", "*.xlsx")])
        if not out: return

        self.btn_batch_run.configure(state="disabled")
        self.batch_log.delete("1.0", "end")
        self.engine.stop_requested = False
        
        def on_finish(count):
            self.auth_manager.debit_credits(count * 1.0)
            self.after(0, self.update_license_ui)

        def task():
            success = self.engine.search_cnpj_batch(db, inp, nc, cc, out, only_phone, limit=qty_to_process)
            self.after(0, lambda: self.btn_batch_run.configure(state="normal"))
            if success:
                on_finish(qty_to_process)
                self.after(0, lambda: [messagebox.showinfo("Sucesso", f"Busca em lote concluída! {qty_to_process} processados."), self.reset_module_ui("batch")])

        threading.Thread(target=task, daemon=True).start()

    def _exec_batch(self, db, inp, nc, cc, out, only_phone):
        self.engine.search_cnpj_batch(db, inp, nc, cc, out, only_with_phone=only_phone)
        self.after(0, lambda: [self.btn_batch_run.configure(state="normal"),
                               messagebox.showinfo("Lote", "Processo massivo concluído!"),
                               self.reset_module_ui("batch")])

    def update_ui_progress(self, curr, total):
        def _update():
            if total > 1:
                v = curr / total
                if hasattr(self, 'progress_bar') and self.progress_bar.cget('mode') == 'determinate': self.progress_bar.set(v)
                if hasattr(self, 'batch_pbar') and self.batch_pbar.cget('mode') == 'determinate': self.batch_pbar.set(v)
                if hasattr(self, 'extract_pbar') and self.extract_pbar.cget('mode') == 'determinate': self.extract_pbar.set(v)
                if hasattr(self, 'split_pbar') and self.split_pbar.cget('mode') == 'determinate': self.split_pbar.set(v)
        self.after(0, _update)

    def append_log(self, msg):
        def _append():
            txt = f"> {msg}\n"
            if hasattr(self, 'log_box'): self.log_box.insert("end", txt); self.log_box.see("end")
            if hasattr(self, 'batch_log'): self.batch_log.insert("end", txt); self.batch_log.see("end")
            if hasattr(self, 'extract_log'): self.extract_log.insert("end", txt); self.extract_log.see("end")
            if hasattr(self, 'split_log'): self.split_log.insert("end", txt); self.split_log.see("end")
        self.after(0, _append)

    def run_carrier_lookup(self):
        if not self.check_license(): return
        input_f = self.carrier_input_file.get()
        out_f = self.carrier_output_file.get()
        phone_col = self.carrier_phone_col.get()
        
        if not input_f or not phone_col:
            return messagebox.showwarning("Erro", "Selecione o arquivo de entrada e a coluna de telefone.")
            
        # 1. Contagem de Linhas para Orçamento
        try:
            if input_f.endswith('.csv'):
                with open(input_f, 'r', encoding='utf-8', errors='ignore') as f:
                    total_lines = sum(1 for line in f) - 1 # Header
            else:
                import pandas as pd
                df_temp = pd.read_excel(input_f, usecols=[phone_col])
                total_lines = len(df_temp)
        except Exception as e:
            return messagebox.showerror("Erro ao ler arquivo", f"Não foi possível contar as linhas: {e}")

        # 2. Confirmação de Créditos (Rate 0.02)
        qty_to_process = self.ask_credit_confirmation(total_lines, 0.02, "Consulta Operadora")
        if not qty_to_process: return
        
        # 3. Escolher Local de Salvamento agora (como sugerido pelo cliente)
        out_f = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV UTF-8", "*.csv")])
        if not out_f: return
        
        self.btn_carrier_run.configure(state="disabled")
        self.carrier_log.delete("1.0", "end")
        self.engine.stop_requested = False
        self.carrier_pbar.set(0)
        
        # Callback para debitar quando o processo terminar com sucesso
        def on_finish(count):
            self.auth_manager.debit_credits(count * 0.02)
            self.after(0, self.update_license_ui)

        def task():
            # Passamos o limite escolhido para o engine (precisamos garantir que o engine respeite isso)
            success = self.engine.process_carrier_lookup(input_f, phone_col, out_f, limit=qty_to_process)
            self.after(0, lambda: self.btn_carrier_run.configure(state="normal"))
            self.after(0, lambda: self.carrier_pbar.stop())
            self.after(0, lambda: self.carrier_pbar.configure(mode="determinate"))
            if success:
                on_finish(qty_to_process)
                self.after(0, lambda: [messagebox.showinfo("Sucesso", f"Pesquisa concluída! {qty_to_process} registros processados."), self.reset_module_ui("carrier")])
            
        self.carrier_pbar.configure(mode="indeterminate")
        self.carrier_pbar.start()
        threading.Thread(target=task, daemon=True).start()

    def run_carrier_import(self):
        csv_path = filedialog.askopenfilename(filetypes=[("CSV Anatel", "*.csv")])
        if not csv_path: return
        
        msg = ("IMPORTAÇÃO GIGANTE.\nEste processo pode levar minutos ou horas (55 Milhões de linhas).\n"
               "Deseja colocar em segundo plano?")
        if not messagebox.askyesno("Confirmação", msg):
            return
            
        self.carrier_import_btn.configure(state="disabled", text="IMPORTANDO...")
        self.carrier_log.delete("1.0", "end")
        self.carrier_pbar.set(0)
        self.engine.progress_callback = lambda current, total: self.after(0, lambda: self.carrier_pbar.set(current / total if total > 0 else 0))
        self.engine.log_callback = lambda msg: self.after(0, lambda: [self.carrier_log.insert("end", f"> {msg}\n"), self.carrier_log.see("end")])

        def task():
            self.engine.import_carrier_csv(csv_path)
            self.after(0, lambda: [
                self.carrier_import_btn.configure(state="normal", text="IMPORTAR CSV GIGANTE DA ANATEL PARA SQLite"),
                messagebox.showinfo("Sucesso", "Banco Anatel internalizado com sucesso!"),
                self.reset_module_ui("carrier")
            ])
            
        threading.Thread(target=task, daemon=True).start()

            
    def reset_module_ui(self, module):
        """ Limpa a interface do módulo após conclusão bem sucedida """
        def _do_reset():
            if module == "unify":
                self.src_entry.delete(0, 'end')
                self.dst_entry.delete(0, 'end')
                self.log_box.delete("1.0", "end")
                self.progress_bar.set(0)
            elif module == "batch":
                self.input_file.delete(0, 'end')
                if hasattr(self, 'output_file'): self.output_file.delete(0, 'end')
                self.name_col.set("")
                self.cpf_col.set("")
                self.batch_log.delete("1.0", "end")
                self.batch_pbar.set(0)
            elif module == "extract":
                self.f_cidade.delete(0, 'end')
                self.f_uf.delete(0, 'end') 
                self.f_cnae.delete(0, 'end')
                self.f_excel_cep.delete(0, 'end')
                if hasattr(self, 'output_extract'): self.output_extract.delete(0, 'end')
                self.f_situacao.set("TODAS")
                self.f_tipo_tel.set("TODOS")
                self.var_extract_phone.set(True) # Padrão True para segurança
                self.extract_log.delete("1.0", "end")
                self.extract_pbar.set(0)
            elif module == "split":
                self.split_input.delete(0, 'end')
                self.split_output.delete(0, 'end')
                self.split_log.delete("1.0", "end")
                self.split_pbar.set(0)
            elif module == "carrier":
                self.carrier_input_file.delete(0, 'end')
                self.carrier_output_file.delete(0, 'end')
                self.carrier_phone_col.set("")
                self.carrier_log.delete("1.0", "end")
                self.carrier_pbar.set(0)

        self.after(2000, _do_reset) # Delay de 2s para o usuário ler as mensagens finais de sucesso

    def clipboard_append_fixed(self, text):
        self.clipboard_clear()
        self.clipboard_append(text)
        self.update()
        messagebox.showinfo("Sucesso", "ID da Máquina copiado para a área de transferência!")

    def execute_logout(self):
        confirm = messagebox.askyesno("Confirmar Logout", "Deseja realmente sair do sistema?")
        if confirm:
            self.auth_manager.logout()
            self.update_license_ui()
            self.show_login_screen()


    def add_styled_input_compact(self, parent, placeholder, command):
        row = ctk.CTkFrame(parent, fg_color="#1a1b26", corner_radius=10, border_width=1, border_color=self.color_border)
        row.pack(fill="x", pady=(2, 0))
        entry = ctk.CTkEntry(row, fg_color="transparent", border_width=0, height=40, placeholder_text=placeholder, font=ctk.CTkFont(size=13))
        entry.pack(side="left", fill="x", expand=True, padx=12)
        btn = ctk.CTkButton(row, text="...", width=36, height=30, corner_radius=6, fg_color="#2d2e35", command=command)
        btn.pack(side="right", padx=6)
        return entry

    def select_coverage_cnpj(self):
        path = filedialog.askopenfilename(filetypes=[("Arquivos Excel/CSV", "*.xlsx *.csv")])
        if path:
            self.coverage_cnpj_entry.delete(0, 'end')
            self.coverage_cnpj_entry.insert(0, path)
            self.lbl_footer_msg.configure(text=f"Base CNPJ selecionada: {os.path.basename(path)}")

    def select_coverage_vivo(self):
        paths = filedialog.askopenfilenames(filetypes=[("Arquivos Excel/CSV", "*.xlsx *.csv")])
        if paths:
            for p in paths:
                if p not in self.selected_vivos:
                    self.selected_vivos.append(p)
            self._update_vivo_list()

    def clear_coverage_vivos(self):
        self.selected_vivos = []
        self._update_vivo_list()

    def _update_vivo_list(self):
        self.coverage_vivo_list.configure(state="normal")
        self.coverage_vivo_list.delete("1.0", "end")
        for p in self.selected_vivos:
            self.coverage_vivo_list.insert("end", f"• {os.path.basename(p)}\n")
        self.coverage_vivo_list.configure(state="disabled")
        self.lbl_vivos_count.configure(text=f"{len(self.selected_vivos)} bases carregadas.")

    def update_coverage_progress(self, current, total):
        prog = (current / total) if total > 0 else 0
        self.after(0, lambda: self.coverage_pbar.set(prog))

    def append_coverage_log(self, msg):
        self.after(0, lambda: [self.coverage_log.insert("end", f"> {msg}\n"), self.coverage_log.see("end")])

    def run_coverage_engine(self):
        try:
            self.append_coverage_log("Iniciando Verificação de Bases...")
            cnpj_f = self.coverage_cnpj_entry.get()
            if not cnpj_f or not self.selected_vivos:
                messagebox.showwarning("Aviso", "Selecione a base CNPJ e pelo menos uma base Vivo.")
                return

            self.btn_coverage_run.configure(state="disabled", text="PROCESSING...")
            self.lbl_coverage_status.configure(text="● RUNNING", text_color=self.color_accent)
            self.coverage_log.delete("1.0", "end")
            self.coverage_pbar.set(0)
            self.append_coverage_log("Motor carregado. Iniciando tarefas em segundo plano...")

            def run():
                try:
                    tipo = self.coverage_tipo_filter.get()
                    df = self.coverage_engine.process_coverage(cnpj_f, self.selected_vivos, filter_tipo=tipo)
                    
                    def finalize():
                        self.btn_coverage_run.configure(state="normal", text="START ENGINE")
                        self.lbl_coverage_status.configure(text="● FINISHED", text_color=self.color_success)
                        if df is not None and not df.empty:
                            self.coverage_result_df = df
                            self.btn_coverage_export.configure(state="normal")
                            messagebox.showinfo("Sucesso", f"Cruzamento concluído! {len(df)} registros encontrados.")
                        else:
                            messagebox.showwarning("Aviso", "Nenhum cruzamento encontrado.")

                    self.after(0, finalize)
                except Exception as e:
                    self.after(0, lambda: messagebox.showerror("Erro de Execução", f"Ocorreu um erro fatal durante o processamento:\n{str(e)}"))
                    self.after(0, lambda: [
                        self.btn_coverage_run.configure(state="normal", text="START ENGINE"),
                        self.lbl_coverage_status.configure(text="● ERROR", text_color=self.color_danger)
                    ])

            threading.Thread(target=run, daemon=True).start()
        except Exception as e:
            messagebox.showerror("Erro de Inicialização", f"Falha ao iniciar o motor:\n{str(e)}")

    def export_coverage_result(self):
        if self.coverage_result_df is None: return
        path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel", "*.xlsx")])
        if path:
            threading.Thread(target=lambda: self.coverage_engine.export_partitioned(self.coverage_result_df, path), daemon=True).start()
            messagebox.showinfo("Exportar", "Exportação iniciada em segundo plano.")

if __name__ == "__main__":
    app = TMMApp()
    app.update_nav_selection(app.btn_unify)
    app.mainloop()
