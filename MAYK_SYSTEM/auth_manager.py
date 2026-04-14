class AuthManager:
    def __init__(self):
        self.token = None
        self.user_data = None

    def login(self, username, password):
        """Mock login function. Accepts any admin/admin or test/test."""
        if (username == 'admin' and password == 'admin') or \
           (username == 'test@mayk.com' and password == '123456'):
            self.token = "dev_token_123"
            self.user_data = {
                "username": username,
                "full_name": "Administrador MAYK",
                "role": "ADMIN",
                "email": username
            }
            return True, "Login com sucesso"
        return False, "Usuário ou senha incorretos."

    def logout(self):
        """Clears user session"""
        self.token = None
        self.user_data = None

    def get_status_summary(self):
        """Returns mock status info for UI headers."""
        if self.token:
            return {"valid": True, "usage": "100%"}
        return {"valid": False, "usage": "0%"}

    def refresh_user_data(self):
        """Validates current token mock."""
        if self.token == "dev_token_123":
            return True, "Sessão válida"
        return False, "Sessão expirada"
