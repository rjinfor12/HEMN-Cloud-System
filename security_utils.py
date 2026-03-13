import hashlib
import os
import wmi
from cryptography.fernet import Fernet

def get_hwid():
    """ Gera um ID único baseado no hardware da máquina (Processador + Placa Mãe) """
    try:
        c = wmi.WMI()
        # Serial do Processador
        processor_id = c.Win32_Processor()[0].ProcessorId.strip()
        # Serial da Placa Mãe
        baseboard_id = c.Win32_BaseBoard()[0].SerialNumber.strip()
        
        raw_id = f"HEMN-{processor_id}-{baseboard_id}"
        return hashlib.sha256(raw_id.encode()).hexdigest().upper()[:16]
    except Exception as e:
        # Fallback para nome do computador se falhar o WMI
        import socket
        return hashlib.sha256(socket.gethostname().encode()).hexdigest().upper()[:16]

def generate_key():
    """ Gera uma chave de criptografia base (Deve ser fixa no sistema para ler as licenças) """
    # Chave mestre gerada determinística para o HEMN SYSTEM
    # Nota: Em um sistema real, essa chave viria de um servidor, mas aqui usaremos uma fixa 
    # baseada em uma seed interna para permitir portabilidade do app sem servidor.
    seed = b"HEMN_SYSTEM_SECRET_v1.1.8_SECURITY_KEY"
    return hashlib.sha256(seed).digest()

import base64
def get_fernet_key():
    """ Retorna a chave formatada para o Fernet """
    raw_key = generate_key()
    return base64.urlsafe_b64encode(raw_key)

def encrypt_data(data_str):
    """ Criptografa uma string usando a chave mestre """
    f = Fernet(get_fernet_key())
    return f.encrypt(data_str.encode()).decode()

def decrypt_data(encrypted_str):
    """ Descriptografa uma string usando a chave mestre """
    try:
        f = Fernet(get_fernet_key())
        return f.decrypt(encrypted_str.encode()).decode()
    except:
        return None
