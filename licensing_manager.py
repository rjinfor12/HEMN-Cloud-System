import json
import os
from datetime import datetime
import requests
from security_utils import get_hwid, encrypt_data, decrypt_data

CLOUD_URL = "http://localhost:8000" # Mude para sua URL de produção (Ex: https://hemn.up.railway.app)


LICENSE_FILE = r"C:\HEMN_SYSTEM_DB\hemn.lic"

class LicenseManager:
    def __init__(self):
        self.hwid = get_hwid()
        self.data = self._load_license()

    def _load_license(self):
        """ Carrega e descriptografa a licença local """
        if not os.path.exists(LICENSE_FILE):
            return self._create_empty_license()
        
        try:
            with open(LICENSE_FILE, 'r') as f:
                encrypted = f.read()
            
            decrypted = decrypt_data(encrypted)
            if not decrypted:
                return self._create_empty_license()
            
            data = json.loads(decrypted)
            
            # Validar se a licença pertence a esta máquina
            if data.get("hwid") != self.hwid:
                return self._create_empty_license()
            
            return data
        except:
            return self._create_empty_license()

    def _create_empty_license(self):
        return {
            "hwid": self.hwid,
            "status": "TRIAL",
            "expiration": "2000-01-01",
            "total_limit": 1000.0, # Trial de 1000 créditos
            "current_usage": 0.0,
            "modules": ["all"]
        }

    def save_license(self, license_data=None):
        """ Salva a licença atual ou uma nova fornecida """
        if license_data:
            self.data = license_data
        
        os.makedirs(os.path.dirname(LICENSE_FILE), exist_ok=True)
        json_str = json.dumps(self.data)
        encrypted = encrypt_data(json_str)
        
        with open(LICENSE_FILE, 'w') as f:
            f.write(encrypted)

    def is_valid(self):
        """ Verifica se a licença está dentro da validade e limite (Local + Nuvem) """
        try:
            # 1. VERIFICAÇÃO EM NUVEM (KILL SWITCH)
            try:
                response = requests.get(f"{CLOUD_URL}/check/{self.hwid}", timeout=5)
                if response.status_code == 200:
                    cloud_data = response.json()
                    if not cloud_data.get("authorized", True):
                        return False, cloud_data.get("msg", "Acesso bloqueado remotamente.")
                    
            # --- SINCRONIZAÇÃO AUTOMÁTICA ---
                    # Se a nuvem tem uma expiração maior que a local, atualiza
                    cloud_exp = cloud_data.get("expiration")
                    if cloud_exp:
                        local_exp = self.data.get("expiration", "2000-01-01")
                        if cloud_exp > local_exp:
                            self.data["expiration"] = cloud_exp
                            self.data["status"] = "ACTIVE"
                            print(f"Licença sincronizada com a nuvem: {cloud_exp}")
                    
                    # Sincroniza Limites e Uso da Nuvem (prioridade)
                    self.data["total_limit"] = float(cloud_data.get("total_limit", self.data["total_limit"]))
                    self.data["current_usage"] = float(cloud_data.get("current_usage", self.data["current_usage"]))
                    self.save_license()
            except Exception as e:
                # Se o servidor estiver indisponível, o sistema segue a licença local
                # Nota: Em sistemas ultra-seguros, você bloquearia se não conseguisse falar com a nuvem.
                print(f"Erro ao sincronizar com nuvem: {e}")

            # 2. Verificar Data Local

            exp_date = datetime.strptime(self.data["expiration"], "%Y-%m-%d")
            if datetime.now() > exp_date:
                return False, "Licença expirada. Entre em contato com o suporte."
            
            # 2. Verificar Limite de Consumo
            if self.data["current_usage"] >= self.data["total_limit"]:
                return False, "Limite de consumo atingido. Renove sua licença."
            
            return True, "Licença Ativa"
        except:
            return False, "Licença Inválida"

    def debit_credits(self, amount):
        """ Debita créditos localmente e sincroniza com a nuvem """
        self.data["current_usage"] += float(amount)
        self.save_license()
        
        try:
            # Envia o débito para a nuvem de forma assíncrona (simulado com timeout curto)
            requests.post(f"{CLOUD_URL}/update_usage/{self.hwid}?consumed={amount}", timeout=3)
        except:
            pass # O próximo ‘is_valid’ vai puxar o valor consolidado da nuvem se este falhar

    def get_status_summary(self):
        """ Retorna resumo para exibição na UI """
        valid, msg = self.is_valid()
        usage = f"{self.data['current_usage']:.2f} / {self.data['total_limit']:.2f}"
        return {
            "valid": valid,
            "msg": msg,
            "expiration": self.data["expiration"],
            "usage": usage,
            "hwid": self.hwid
        }


