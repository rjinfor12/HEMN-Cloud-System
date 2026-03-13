import json
import os
from datetime import datetime
import requests

CLOUD_URL = "http://localhost:8000" # Mude para sua URL de produção (Ex: https://hemn.up.railway.app)
AUTH_FILE = r"C:\HEMN_SYSTEM_DB\auth.session"

class AuthManager:
    def __init__(self):
        self.token = self._load_session()
        self.user_data = None
        if self.token:
            self.refresh_user_data()

    def _load_session(self):
        """ Desativado: Forçar login em cada inicialização """
        return None

    def save_session(self, token):
        """ Apenas mantém na memória para esta execução """
        self.token = token

    def logout(self):
        """ Limpa dados e remove qualquer rastro de sessão anterior """
        self.token = None
        self.user_data = None
        if os.path.exists(AUTH_FILE):
            try: os.remove(AUTH_FILE)
            except: pass

    def login(self, username, password):
        """ Realiza login e retorna True se bem-sucedido """
        try:
            response = requests.post(f"{CLOUD_URL}/login", 
                                     data={"username": username, "password": password},
                                     timeout=10)
            if response.status_code == 200:
                token_data = response.json()
                self.save_session(token_data["access_token"])
                return self.refresh_user_data()
            else:
                return False, response.json().get("detail", "Erro desconhecido")
        except requests.exceptions.ConnectionError:
            return False, "Erro de conexão: O servidor não está respondendo. Verifique se o Servidor Cloud está ativo."
        except Exception as e:
            return False, f"Erro inesperado: {str(e)}"

    def refresh_user_data(self):
        """ Busca dados atualizados do usuário na nuvem usando o token """
        if not self.token:
            return False, "Nenhuma sessão ativa"
        
        headers = {"Authorization": f"Bearer {self.token}"}
        try:
            response = requests.get(f"{CLOUD_URL}/me", headers=headers, timeout=5)
            if response.status_code == 200:
                self.user_data = response.json()
                return True, "Sessão Ativa"
            else:
                self.logout()
                return False, "Sessão Expirada ou Inválida"
        except:
            return False, "Servidor Indisponível"

    def debit_credits(self, amount):
        """ Notifica a nuvem sobre o consumo de créditos """
        if not self.token: return
        
        headers = {"Authorization": f"Bearer {self.token}"}
        try:
            requests.post(f"{CLOUD_URL}/update_usage?consumed={amount}", headers=headers, timeout=5)
            # Atualiza dados locais após o débito
            self.refresh_user_data()
        except:
            # Em caso de falha de conexão, o crédito será sincronizado no próximo login/refresh
            pass

    def get_status_summary(self):
        """ Resumo para a UI """
        if not self.user_data:
            return {"valid": False, "msg": "Necessário Login"}
        
        if self.user_data['total_limit'] >= 9000000:
            usage = f"{self.user_data['current_usage']:.2f} / Ilimitado (∞)"
        else:
            usage = f"{self.user_data['current_usage']:.2f} / {self.user_data['total_limit']:.2f}"
        return {
            "valid": True,
            "msg": f"Bem-vindo, {self.user_data['full_name']}",
            "expiration": self.user_data["expiration"],
            "usage": usage,
            "username": self.user_data["username"]
        }
