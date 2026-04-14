import customtkinter as ctk
from tkinter import filedialog, messagebox
import os
import sys
import threading
from PIL import Image, ImageTk
from auth_manager import AuthManager
from database import MaykDatabase

VERSION = "1.0.0"

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.dirname(__file__)
    return os.path.join(base_path, relative_path)

class MaykApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("MAYK SYSTEM | CRM Local")
        self.geometry("1100x820")
        
        try:
            png_path = resource_path("logo.png")
            if os.path.exists(png_path):
                img_tk = ImageTk.PhotoImage(Image.open(png_path))
                self.wm_iconphoto(False, img_tk)
        except Exception:
            pass
        
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # Paleta de Cores Premium (Titanium Dark)
        self.color_bg = ("#08090c", "#08090c")
        self.color_sidebar = ("#0d0e12", "#0d0e12")
        self.color_card = ("#13141c", "#13141c")
        self.color_accent = ("#3858f9", "#3858f9")
        self.color_border = ("#1e2030", "#1e2030")
        self.color_text_main = ("#f9fafb", "#f9fafb")
        self.color_text_dim = ("#64748b", "#64748b")
        self.color_success = ("#22c55e", "#22c55e")
        
        self.configure(fg_color=self.color_bg[1])

        # Grid
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=0) # Header
        self.grid_rowconfigure(1, weight=1) # Content

        # Sidebar
        self.sidebar_frame = ctk.CTkFrame(self, width=100, corner_radius=0, 
                                        fg_color=self.color_sidebar, border_width=0)
        self.sidebar_frame.grid(row=0, column=0, rowspan=2, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(9, weight=1)

        # Header
        self.header_frame = ctk.CTkFrame(self, height=70, corner_radius=0, 
                                        fg_color=self.color_sidebar, border_width=0)
        self.header_frame.grid(row=0, column=1, sticky="ew")
        self.header_frame.grid_columnconfigure(0, weight=1)
        self.setup_header_content()

        self.setup_branding()

        # Botões do CRM
        self.nav_buttons = []
        self.add_nav_button("Dashboard", 2, lambda: self.show_frame("dashboard"))
        self.add_nav_button("Clientes",  3, lambda: self.show_frame("clientes"))
        self.add_nav_button("Leads",     4, lambda: self.show_frame("leads"))
        self.add_nav_button("Oportun.",  5, lambda: self.show_frame("oportunidades"))
        
        # Spacer
        self.add_nav_button("Ajustes",   10, lambda: self.show_frame("ajustes"))

        self.auth_manager = AuthManager()
        self.db = MaykDatabase()

        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.grid(row=1, column=1, sticky="nsew", padx=30, pady=20)
        self.main_container.grid_columnconfigure(0, weight=1)
        self.main_container.grid_rowconfigure(0, weight=1)

        self.frames = {}
        self.frames["dashboard"] = self.create_dashboard_frame()
        self.frames["clientes"] = self.create_placeholder_frame("Clientes / Contatos")
        self.frames["leads"] = self.create_placeholder_frame("Leads / Caixa de Entrada")
        self.frames["oportunidades"] = self.create_oportunidades_frame()
        self.frames["ajustes"] = self.create_ajustes_frame()
        self.show_frame("dashboard")

        self._login_overlay = None
        self.show_login_screen()

    def setup_header_content(self):
        ctk.CTkLabel(self.header_frame, text="", width=10).pack(side="left")

        actions = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        actions.pack(side="right", padx=30)
        
        self.header_metrics = ctk.CTkLabel(actions, text="Metas: 100%",
                                           font=ctk.CTkFont(size=13, weight="bold"),
                                           text_color=self.color_success)
        self.header_metrics.pack(side="left", padx=20)

        self.user_btn_frame = ctk.CTkFrame(actions, fg_color=self.color_sidebar,
                                           corner_radius=8, border_width=1,
                                           border_color=self.color_border)
        self.user_btn_frame.pack(side="left")

        self.header_user = ctk.CTkLabel(self.user_btn_frame, text="Usuário",
                                        font=ctk.CTkFont(size=13, weight="bold"),
                                        text_color=self.color_text_main)
        self.header_user.pack(padx=16, pady=8)

    def setup_branding(self):
        try:
            p_img = resource_path("logo.png")
            if os.path.exists(p_img):
                img = Image.open(p_img)
                self.logo_img = ctk.CTkImage(light_image=img, dark_image=img, size=(45, 45))
                self.logo_label = ctk.CTkLabel(self.sidebar_frame, image=self.logo_img, text="")
                self.logo_label.grid(row=0, column=0, pady=(15, 25))
        except Exception:
            pass

    def add_nav_button(self, text, row, command):
        container = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        container.grid(row=row, column=0, sticky="ew", pady=2)
        
        btn = ctk.CTkFrame(container, fg_color="transparent", width=85, height=75, corner_radius=12)
        btn.pack(padx=8, pady=5)
        btn.pack_propagate(False)
        
        icon_map = {
            "Dashboard": "📊", "Clientes": "👥", "Leads": "🎯", 
            "Oportun.": "💼", "Ajustes": "⚙️"
        }
        icon_text = icon_map.get(text, "•")
        
        btn.icon_label = ctk.CTkLabel(btn, text=icon_text, font=ctk.CTkFont(size=24))
        btn.icon_label.pack(pady=(12, 0))
        
        btn.text_label = ctk.CTkLabel(btn, text=text, font=ctk.CTkFont(size=11, weight="bold"),
                                     text_color=self.color_text_dim)
        btn.text_label.pack(pady=(0, 10))
        
        def on_enter(e):
            if btn.cget("fg_color") == "transparent":
                btn.configure(fg_color="#1a1b26")
        def on_leave(e):
            if not getattr(btn, "is_selected", False):
                btn.configure(fg_color="transparent")
        
        def on_click(e):
            command()
            self.update_nav_selection(btn)

        for widget in [btn, btn.icon_label, btn.text_label]:
            widget.bind("<Enter>", on_enter)
            widget.bind("<Leave>", on_leave)
            widget.bind("<Button-1>", on_click)
            widget.configure(cursor="hand2")

        self.nav_buttons.append(btn)
        return btn

    def update_nav_selection(self, selected_btn):
        for btn in self.nav_buttons:
            if btn == selected_btn:
                btn.configure(fg_color="#13141c")
                btn.is_selected = True
                btn.icon_label.configure(text_color=self.color_accent)
                btn.text_label.configure(text_color=self.color_accent)
            else:
                btn.configure(fg_color="transparent")
                btn.is_selected = False
                btn.icon_label.configure(text_color=self.color_text_dim)
                btn.text_label.configure(text_color=self.color_text_dim)

    def _hide_main_ui(self):
        self.sidebar_frame.grid_remove()
        self.header_frame.grid_remove()
        self.main_container.grid_remove()

    def _reveal_app(self):
        if self._login_overlay:
            self._login_overlay.destroy()
            self._login_overlay = None
        self.sidebar_frame.grid()
        self.header_frame.grid()
        self.main_container.grid()
        if self.auth_manager.user_data:
            self.header_user.configure(text=self.auth_manager.user_data['full_name'])

    def show_login_screen(self):
        self._hide_main_ui()

        overlay = ctk.CTkFrame(self, fg_color="#08090c", corner_radius=0)
        overlay.place(x=0, y=0, relwidth=1.0, relheight=1.0)
        overlay.lift()
        self._login_overlay = overlay

        left = ctk.CTkFrame(overlay, fg_color="transparent", corner_radius=0)
        left.place(relx=0, rely=0, relwidth=0.55, relheight=1.0)

        center_box = ctk.CTkFrame(left, fg_color="transparent")
        center_box.place(relx=0.5, rely=0.5, anchor="center")

        try:
            if hasattr(self, 'logo_img'):
                ctk.CTkLabel(center_box, image=self.logo_img, text="").pack(pady=(0, 20))
        except Exception:
            pass

        ctk.CTkLabel(center_box, text="MAYK SYSTEM",
                     font=ctk.CTkFont(size=36, weight="bold"),
                     text_color="#f8fafc").pack(anchor="w")
        ctk.CTkLabel(center_box, text="CRM de Alta Conversão",
                     font=ctk.CTkFont(size=16),
                     text_color="#94a3b8").pack(anchor="w", pady=(6, 30))

        bullets = [
            ("📁", "Gestão de Clientes e Contatos"),
            ("🎯", "Prospecção Inteligente"),
            ("💼", "Painel de Oportunidades"),
            ("🔒", "Dados 100% Locais"),
        ]
        for icon, text in bullets:
            row = ctk.CTkFrame(center_box, fg_color="transparent")
            row.pack(anchor="w", pady=6)
            ctk.CTkLabel(row, text=icon, font=ctk.CTkFont(size=18), text_color="#38bdf8").pack(side="left", padx=(0, 12))
            ctk.CTkLabel(row, text=text, font=ctk.CTkFont(size=14), text_color="#cbd5e1").pack(side="left")

        sep = ctk.CTkFrame(overlay, fg_color="#1e293b", corner_radius=0, width=2)
        sep.place(relx=0.55, rely=0.0, relwidth=0, relheight=1.0)

        right = ctk.CTkFrame(overlay, fg_color="#08090c", corner_radius=0)
        right.place(relx=0.55, rely=0, relwidth=0.45, relheight=1.0)

        form_box = ctk.CTkFrame(right, fg_color="#0d0e12", corner_radius=20,
                                border_width=1, border_color="#1e2030",
                                width=360, height=480)
        form_box.place(relx=0.5, rely=0.5, anchor="center")
        form_box.pack_propagate(False)

        ctk.CTkLabel(form_box, text="Acessar CRM",
                     font=ctk.CTkFont(size=24, weight="bold"),
                     text_color="#f1f5f9").pack(pady=(40, 4))
        ctk.CTkLabel(form_box, text="Entre com suas credenciais de acesso",
                     font=ctk.CTkFont(size=13),
                     text_color="#64748b").pack(pady=(0, 28))

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

        self.ent_user = make_field("Usuário", "admin")
        self.ent_pass = make_field("Senha", "••••••••", show="*")

        self.btn_login = ctk.CTkButton(
            form_box, text="Entrar", width=296, height=46, corner_radius=8,
            fg_color="#3b82f6", hover_color="#2563eb",
            text_color="#ffffff", font=ctk.CTkFont(size=15, weight="bold"),
            command=self.execute_login)
        self.btn_login.pack(pady=(6, 16))

        self.lbl_login_status = ctk.CTkLabel(
            form_box, text="Use admin/admin",
            text_color="#94a3b8", font=ctk.CTkFont(size=12))
        self.lbl_login_status.pack()

        ctk.CTkLabel(overlay, text=f"v{VERSION} · MAYK SYSTEM CRM",
                     font=ctk.CTkFont(size=10), text_color="#334155"
                     ).place(relx=0.5, rely=0.97, anchor="center")

        self.ent_user.focus_set()
        overlay.bind("<Return>", lambda e: self.execute_login())

    def execute_login(self):
        user = self.ent_user.get()
        pw = self.ent_pass.get()

        if not user or not pw:
            self.lbl_login_status.configure(text="Preencha todos os campos", text_color="#f87171")
            return

        self.btn_login.configure(state="disabled", text="Autenticando...")
        self.lbl_login_status.configure(text="")

        def run():
            success, msg = self.auth_manager.login(user, pw)
            if success:
                self.after(0, self.finish_login)
            else:
                self.after(0, lambda: [
                    self.lbl_login_status.configure(text=msg, text_color="#f87171"),
                    self.btn_login.configure(state="normal", text="Entrar")
                ])

        threading.Thread(target=run, daemon=True).start()

    def finish_login(self):
        self._reveal_app()

    def show_frame(self, frame_name):
        for f in self.frames.values():
            f.grid_remove()
        
        target = self.frames[frame_name]
        if hasattr(target, "refresh_dashboard"):
            target.refresh_dashboard()
            
        target.grid(row=0, column=0, sticky="nsew")

    def create_card(self, parent, title, description):
        card = ctk.CTkFrame(parent, fg_color=self.color_card, corner_radius=20, 
                            border_width=1, border_color=self.color_border)
        
        header = ctk.CTkFrame(card, fg_color="transparent", height=45)
        header.pack(fill="x", padx=25, pady=(20, 10))
        
        dot = ctk.CTkFrame(header, width=8, height=8, corner_radius=4, fg_color=self.color_accent)
        dot.pack(side="left", padx=(0, 12))

        ctk.CTkLabel(header, text=title.upper(), font=ctk.CTkFont(size=14, weight="bold"), 
                     text_color=self.color_text_main).pack(side="left")
        
        ctk.CTkLabel(card, text=description, font=ctk.CTkFont(size=12), 
                     text_color=self.color_text_dim, justify="left").pack(padx=45, anchor="w", pady=(0, 20))
        
        content = ctk.CTkFrame(card, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=40, pady=(0, 25))
        return content

    def create_dashboard_frame(self):
        frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_columnconfigure(1, weight=1)
        
        lbl_title = ctk.CTkLabel(frame, text="Visão Geral Analítica", 
                                 font=ctk.CTkFont(size=24, weight="bold"),
                                 text_color=self.color_text_main)
        lbl_title.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 20))

        # Containers dinâmicos que serão regerados no refresh
        cards_container = ctk.CTkFrame(frame, fg_color="transparent")
        cards_container.grid(row=1, column=0, columnspan=2, sticky="nsew")
        cards_container.grid_columnconfigure(0, weight=1)
        cards_container.grid_columnconfigure(1, weight=1)

        def refresh_dashboard():
            for w in cards_container.winfo_children(): w.destroy()
            metrics = self.db.get_dashboard_metrics()
            
            # Card Financeiro e Vendas Globais
            c1 = self.create_card(cards_container, "Volume Financeiro", "Soma das negociações declaradas no CRM.")
            c1.master.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
            
            ctk.CTkLabel(c1, text=f"Total de Oportunidades: {metrics['total_sales']}", font=ctk.CTkFont(size=18, weight="bold"), text_color=self.color_text_main).pack(anchor="w", pady=5)
            ctk.CTkLabel(c1, text=f"Volume Estimado: R$ {metrics['total_value']:.2f}", font=ctk.CTkFont(size=22, weight="bold"), text_color=self.color_success).pack(anchor="w", pady=(10, 5))

            # Card de Conversão / Status
            c2 = self.create_card(cards_container, "Funil de Vendas", "Oportunidades mapeadas por Etapa no Kanban.")
            c2.master.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)

            # Barra de Progresso Customizada (Visualização simples de densidade)
            total = metrics['total_sales'] if metrics['total_sales'] > 0 else 1
            for st_name, count in metrics['status_counts'].items():
                row = ctk.CTkFrame(c2, fg_color="transparent")
                row.pack(fill="x", pady=8)
                
                pct = (count / total) * 100
                ctk.CTkLabel(row, text=f"{st_name} ({count})", font=ctk.CTkFont(size=13), text_color=self.color_text_dim).pack(side="left")
                ctk.CTkLabel(row, text=f"{pct:.1f}%", font=ctk.CTkFont(size=13, weight="bold"), text_color=self.color_accent).pack(side="right")
                
                # Barra
                bar_bg = ctk.CTkFrame(c2, fg_color="#1a1b26", height=6, corner_radius=3)
                bar_bg.pack(fill="x", pady=(0, 4))
                
                bar_fg = ctk.CTkFrame(bar_bg, fg_color=self.color_accent, width=max(int((pct/100)*250), 5), height=6, corner_radius=3)
                bar_fg.pack(side="left")

        # Anexar a função de recarregamento ao frame para ser chamada externamente
        frame.refresh_dashboard = refresh_dashboard
        refresh_dashboard()

        frame.grid_rowconfigure(1, weight=1)
        return frame

    def create_placeholder_frame(self, title):
        frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        
        ctk.CTkLabel(frame, text=title, 
                     font=ctk.CTkFont(size=24, weight="bold"),
                     text_color=self.color_text_main).pack(anchor="w", pady=(0, 20))
        
        content = self.create_card(frame, "Módulo em Construção", "Este módulo será desenvolvido na próxima fase.")
        content.master.pack(fill="both", expand=True, padx=2, pady=10)
        
        ctk.CTkLabel(content, text="Aguardando implementação...",
                     text_color=self.color_text_dim, font=ctk.CTkFont(size=16)).pack(pady=40)
        
        return frame

    def open_sale_details(self, sale_id):
        # Janela de Detalhes da Oportunidade
        top = ctk.CTkToplevel(self)
        top.title(f"Detalhes da Oportunidade #{sale_id}")
        top.geometry("800x600")
        top.configure(fg_color="#08090c")
        top.attributes("-topmost", True)
        
        # Buscar dados base da venda
        sales = self.db.get_all_sales()
        sale = next((s for s in sales if s["id"] == sale_id), None)
        if not sale: return

        header = ctk.CTkFrame(top, fg_color="#13141c", height=80, corner_radius=0)
        header.pack(fill="x")
        ctk.CTkLabel(header, text=f"Cliente: {sale['nome_cliente']} (Doc: {sale['documento_cliente']})", font=ctk.CTkFont(size=18, weight="bold")).pack(side="left", padx=20, pady=20)
        
        # Layout Direita / Esquerda
        content = ctk.CTkFrame(top, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=20, pady=20)
        
        left = ctk.CTkFrame(content, fg_color="#0d0e12", corner_radius=12)
        left.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        right = ctk.CTkFrame(content, fg_color="#0d0e12", corner_radius=12)
        right.pack(side="right", fill="both", expand=True, padx=(10, 0))

        # Aba Esquerda: Produtos
        ctk.CTkLabel(left, text="Produtos da Venda", font=ctk.CTkFont(size=14, weight="bold"), text_color=self.color_accent).pack(pady=10)
        frm_prod_add = ctk.CTkFrame(left, fg_color="transparent")
        frm_prod_add.pack(fill="x", padx=10)
        
        ent_prod = ctk.CTkEntry(frm_prod_add, placeholder_text="Nome do Produto", width=150)
        ent_prod.pack(side="left", padx=5)
        ent_qtd = ctk.CTkEntry(frm_prod_add, placeholder_text="Qtd", width=50)
        ent_qtd.pack(side="left", padx=5)

        prod_list = ctk.CTkScrollableFrame(left, fg_color="#1a1b26", height=150)
        prod_list.pack(fill="both", expand=True, padx=10, pady=10)

        def load_prods():
            for w in prod_list.winfo_children(): w.destroy()
            for p in self.db.get_sale_products(sale_id):
                ctk.CTkLabel(prod_list, text=f"{p['qtd']}x {p['product_name']}", font=ctk.CTkFont(size=12)).pack(anchor="w", pady=2)
        
        def save_prod():
            if not ent_prod.get(): return
            self.db.save_product(sale_id, {"product_name": ent_prod.get(), "qtd": int(ent_qtd.get() or 1)})
            ent_prod.delete(0, 'end'); ent_qtd.delete(0, 'end')
            load_prods()

        ctk.CTkButton(frm_prod_add, text="+", width=30, command=save_prod).pack(side="left")
        load_prods()

        # Aba Direita: Endereços
        ctk.CTkLabel(right, text="Endereços", font=ctk.CTkFont(size=14, weight="bold"), text_color=self.color_accent).pack(pady=10)
        frm_addr_add = ctk.CTkFrame(right, fg_color="transparent")
        frm_addr_add.pack(fill="x", padx=10)
        
        ent_rua = ctk.CTkEntry(frm_addr_add, placeholder_text="Logradouro", width=150)
        ent_rua.pack(side="left", padx=5)
        ent_num = ctk.CTkEntry(frm_addr_add, placeholder_text="Nº", width=50)
        ent_num.pack(side="left", padx=5)

        addr_list = ctk.CTkScrollableFrame(right, fg_color="#1a1b26", height=150)
        addr_list.pack(fill="both", expand=True, padx=10, pady=10)

        def load_addr():
            for w in addr_list.winfo_children(): w.destroy()
            for a in self.db.get_sale_addresses(sale_id):
                ctk.CTkLabel(addr_list, text=f"[{a['type']}] {a['street']}, {a['number']} - {a['city']}", font=ctk.CTkFont(size=12)).pack(anchor="w", pady=2)

        def save_addr():
            if not ent_rua.get(): return
            self.db.save_address(sale_id, {"street": ent_rua.get(), "number": ent_num.get(), "city": "Local"})
            ent_rua.delete(0, 'end'); ent_num.delete(0, 'end')
            load_addr()

        ctk.CTkButton(frm_addr_add, text="+", width=30, command=save_addr).pack(side="left")
        load_addr()

    def create_oportunidades_frame(self):
        """ Cria a tela de Gestão de Vendas com Cadastro e Kanban """
        frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        
        lbl_title = ctk.CTkLabel(frame, text="Gestão de Oportunidades", 
                                 font=ctk.CTkFont(size=24, weight="bold"),
                                 text_color=self.color_text_main)
        lbl_title.pack(anchor="w", pady=(0, 10))

        tabview = ctk.CTkTabview(frame, fg_color=self.color_card, border_width=1, border_color=self.color_border, text_color=self.color_text_main, segmented_button_selected_color=self.color_accent, segmented_button_selected_hover_color=self.color_accent)
        tabview.pack(fill="both", expand=True)

        tab_lista = tabview.add("Cadastrar")
        tab_kanban = tabview.add("Kanban")

        # ==========================================
        # ABA: CADASTRAR E LISTAR
        # ==========================================
        form_frame = ctk.CTkFrame(tab_lista, fg_color="transparent")
        form_frame.pack(fill="x", pady=10)

        def create_entry(parent, label_text, placeholder):
            vbox = ctk.CTkFrame(parent, fg_color="transparent")
            vbox.pack(side="left", padx=10, fill="x", expand=True)
            ctk.CTkLabel(vbox, text=label_text, font=ctk.CTkFont(size=12, weight="bold"), text_color=self.color_text_dim).pack(anchor="w")
            e = ctk.CTkEntry(vbox, placeholder_text=placeholder, fg_color="#0d0e12", border_color=self.color_border)
            e.pack(fill="x", pady=(2, 10))
            return e

        row1 = ctk.CTkFrame(form_frame, fg_color="transparent")
        row1.pack(fill="x")
        ent_nome = create_entry(row1, "Nome do Cliente", "Ex: Maria Silva")
        ent_doc = create_entry(row1, "Documento (CPF/CNPJ)", "000.000.000-00")
        
        row2 = ctk.CTkFrame(form_frame, fg_color="transparent")
        row2.pack(fill="x")
        ent_tel = create_entry(row2, "Telefone Principal", "(11) 99999-9999")
        ent_valor = create_entry(row2, "Valor Manual (R$)", "0.00")

        def save_new_sale():
            data = {
                "identificador": "WEB" + str(self.db.get_connection().execute("SELECT count(*) FROM sales").fetchone()[0]) + "u",
                "tipo_cliente": "PF" if len(ent_doc.get().replace(".", "").replace("-", "")) <= 11 else "PJ",
                "nome_cliente": ent_nome.get(),
                "documento_cliente": ent_doc.get(),
                "tel_principal": ent_tel.get(),
                "valor_manual": float(ent_valor.get() if ent_valor.get() else 0.0),
                "status_atual_venda": 6
            }
            if not data["nome_cliente"]:
                messagebox.showerror("Erro", "Nome do cliente é obrigatório")
                return

            self.db.save_sale(data)
            messagebox.showinfo("Sucesso", "Oportunidade registrada com sucesso!")
            ent_nome.delete(0, 'end')
            ent_doc.delete(0, 'end')
            ent_tel.delete(0, 'end')
            ent_valor.delete(0, 'end')
            load_sales()
            load_kanban()

        btn_save = ctk.CTkButton(form_frame, text="Registrar Oportunidade", fg_color=self.color_accent, font=ctk.CTkFont(weight="bold"), command=save_new_sale)
        btn_save.pack(pady=15, anchor="e", padx=10)

        history_frame = ctk.CTkFrame(tab_lista, fg_color="transparent")
        history_frame.pack(fill="both", expand=True)
        ctk.CTkLabel(history_frame, text="Últimas Oportunidades", font=ctk.CTkFont(size=14, weight="bold"), text_color=self.color_text_main).pack(anchor="w", padx=10)
        
        listbox = ctk.CTkScrollableFrame(history_frame, fg_color="#08090c", border_width=1, border_color=self.color_border)
        listbox.pack(fill="both", expand=True, padx=10, pady=5)

        def load_sales():
            for widget in listbox.winfo_children():
                widget.destroy()
            
            sales = self.db.get_all_sales()
            statuses_map = {st['id']: st['name'] for st in self.db.get_statuses()}
            for s in sales:
                item = ctk.CTkFrame(listbox, fg_color="#13141c", corner_radius=8)
                item.pack(fill="x", pady=4, padx=4)
                s_name = statuses_map.get(s['status_atual_venda'], "Desconhecido")
                text = f"ID: {s['id']} | Cliente: {s['nome_cliente']} | Doc: {s['documento_cliente']} | Status: {s_name} | Valor: R$ {s['valor_manual']}"
                ctk.CTkLabel(item, text=text, font=ctk.CTkFont(size=12), text_color=self.color_text_main).pack(anchor="w", padx=10, pady=(8,2))
                ctk.CTkButton(item, text="Abrir", width=50, height=20, fg_color="#334155", font=ctk.CTkFont(size=10), command=lambda sid=s['id']: self.open_sale_details(sid)).pack(anchor="w", padx=10, pady=(0, 8))

        # ==========================================
        # ABA: KANBAN
        # ==========================================
        kanban_frame = ctk.CTkFrame(tab_kanban, fg_color="transparent")
        kanban_frame.pack(fill="both", expand=True)

        def move_sale(sale_id, curr_status_id, direction):
            statuses = self.db.get_statuses()
            idx = next((i for i, v in enumerate(statuses) if v["id"] == curr_status_id), -1)
            
            if direction == "right" and idx < len(statuses) - 1:
                new_status = statuses[idx+1]["id"]
            elif direction == "left" and idx > 0:
                new_status = statuses[idx-1]["id"]
            else:
                return

            self.db.update_sale_status(sale_id, new_status)
            load_kanban()
            load_sales()

        def load_kanban():
            for widget in kanban_frame.winfo_children():
                widget.destroy()

            statuses = self.db.get_statuses()
            sales = self.db.get_all_sales()
            
            for i, st in enumerate(statuses):
                col = ctk.CTkFrame(kanban_frame, fg_color="#0d0e12", corner_radius=8, border_width=1, border_color=self.color_border)
                col.pack(side="left", fill="both", expand=True, padx=5)
                
                ctk.CTkLabel(col, text=st['name'].upper(), font=ctk.CTkFont(size=13, weight="bold"), text_color=self.color_accent).pack(pady=10)
                
                scroll = ctk.CTkScrollableFrame(col, fg_color="transparent")
                scroll.pack(fill="both", expand=True, padx=5, pady=5)

                col_sales = [s for s in sales if s['status_atual_venda'] == st['id']]
                for s in col_sales:
                    card = ctk.CTkFrame(scroll, fg_color="#1a1b26", corner_radius=6, border_width=1, border_color="#1e2030")
                    card.pack(fill="x", pady=4)
                    
                    ctk.CTkLabel(card, text=s['nome_cliente'], font=ctk.CTkFont(size=12, weight="bold"), text_color=self.color_text_main).pack(anchor="w", padx=8, pady=(8,2))
                    ctk.CTkLabel(card, text=f"R$ {s['valor_manual']}", font=ctk.CTkFont(size=11), text_color=self.color_success).pack(anchor="w", padx=8)
                    
                    btn_frame = ctk.CTkFrame(card, fg_color="transparent")
                    btn_frame.pack(fill="x", side="bottom", pady=4, padx=4)
                    
                    btn_details = ctk.CTkButton(btn_frame, text="Info", width=40, height=20, fg_color="#3b82f6", font=ctk.CTkFont(size=10, weight="bold"), command=lambda sid=s['id']: self.open_sale_details(sid))
                    btn_details.pack(side="left", padx=2)

                    if i > 0:
                        btn_prev = ctk.CTkButton(btn_frame, text="◀", width=30, height=20, fg_color="#334155", font=ctk.CTkFont(size=10), command=lambda sid=s['id'], curr=st['id']: move_sale(sid, curr, "left"))
                        btn_prev.pack(side="left")
                    if i < len(statuses) - 1:
                        btn_next = ctk.CTkButton(btn_frame, text="▶", width=30, height=20, fg_color="#334155", font=ctk.CTkFont(size=10), command=lambda sid=s['id'], curr=st['id']: move_sale(sid, curr, "right"))
                        btn_next.pack(side="right")

        load_sales()
        load_kanban()

        return frame

    def create_ajustes_frame(self):
        frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_columnconfigure(1, weight=1)
        
        lbl_title = ctk.CTkLabel(frame, text="Ajustes do Sistema", 
                                 font=ctk.CTkFont(size=24, weight="bold"),
                                 text_color=self.color_text_main)
        lbl_title.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 20))

        users_card = self.create_card(frame, "Gestão de Usuários", "Controle de Vendedores e Consultores")
        users_card.master.grid(row=1, column=0, sticky="nsew", padx=10)

        frm_user_add = ctk.CTkFrame(users_card, fg_color="transparent")
        frm_user_add.pack(fill="x", pady=5)
        ent_uname = ctk.CTkEntry(frm_user_add, placeholder_text="Nome", width=120)
        ent_uname.pack(side="left", padx=2)
        ent_uemail = ctk.CTkEntry(frm_user_add, placeholder_text="Email", width=120)
        ent_uemail.pack(side="left", padx=2)
        
        user_list = ctk.CTkScrollableFrame(users_card, fg_color="#1a1b26", height=200)
        user_list.pack(fill="both", expand=True, pady=10)

        def add_user():
            if ent_uname.get() and ent_uemail.get():
                self.db.add_user(ent_uname.get(), ent_uemail.get(), "", "vendedor")
                ent_uname.delete(0, 'end'); ent_uemail.delete(0, 'end')
                refresh_ajustes()

        ctk.CTkButton(frm_user_add, text="Adicionar", width=60, command=add_user).pack(side="left", padx=5)

        status_card = self.create_card(frame, "Funil de Vendas", "Personalize as colunas do Kanban")
        status_card.master.grid(row=1, column=1, sticky="nsew", padx=10)

        frm_status_add = ctk.CTkFrame(status_card, fg_color="transparent")
        frm_status_add.pack(fill="x", pady=5)
        ent_sname = ctk.CTkEntry(frm_status_add, placeholder_text="Nome do Status", width=200)
        ent_sname.pack(side="left", padx=2)
        
        status_list = ctk.CTkScrollableFrame(status_card, fg_color="#1a1b26", height=200)
        status_list.pack(fill="both", expand=True, pady=10)

        def add_status():
            if ent_sname.get():
                self.db.add_status(ent_sname.get())
                ent_sname.delete(0, 'end')
                refresh_ajustes()
                if hasattr(self.frames["oportunidades"], "refresh"):
                    pass # O ideal é sempre dar refresh na tab kanban no show_frame

        ctk.CTkButton(frm_status_add, text="Adicionar", width=60, command=add_status).pack(side="left", padx=5)

        def del_user(uid):
            if self.db.delete_user(uid): refresh_ajustes()
            else: messagebox.showerror("Erro", "Usuário possui vendas vinculadas!")

        def del_status(sid):
            if self.db.delete_status(sid): refresh_ajustes()
            else: messagebox.showerror("Erro", "Status possui vendas vinculadas!")

        def refresh_ajustes():
            for w in user_list.winfo_children(): w.destroy()
            for u in self.db.get_users():
                r = ctk.CTkFrame(user_list, fg_color="transparent")
                r.pack(fill="x", pady=2)
                ctk.CTkLabel(r, text=u['name'], font=ctk.CTkFont(size=12)).pack(side="left")
                ctk.CTkButton(r, text="X", width=20, fg_color="#ef4444", command=lambda uid=u['id']: del_user(uid)).pack(side="right")

            for w in status_list.winfo_children(): w.destroy()
            for s in self.db.get_statuses():
                r = ctk.CTkFrame(status_list, fg_color="transparent")
                r.pack(fill="x", pady=2)
                ctk.CTkLabel(r, text=s['name'], font=ctk.CTkFont(size=12)).pack(side="left")
                ctk.CTkButton(r, text="X", width=20, fg_color="#ef4444", command=lambda sid=s['id']: del_status(sid)).pack(side="right")

        frame.refresh_ajustes = refresh_ajustes
        refresh_ajustes()

        frame.grid_rowconfigure(1, weight=1)
        return frame

if __name__ == "__main__":
    app = MaykApp()
    app.mainloop()
