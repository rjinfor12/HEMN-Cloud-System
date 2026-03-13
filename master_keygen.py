import json
import os
import hashlib
from datetime import datetime
from security_utils import encrypt_data

# Este script deve ser mantido APENAS com o administrador (VOCÊ).
# Ele gera as chaves que os clientes inserem no sistema.

LICENSE_DIR = r"C:\HEMN_SYSTEM_DB"

def generate_key_string(type="ANUAL", value="2027"):
    """ Gera a string que o cliente digita no app """
    key = f"HEMN-{type}-{value}"
    print(f"\nCHAVE GERADA: {key}")
    print(f"Instrução: Passe essa chave para o cliente inserir no botão 'ATIVAR CHAVE'.")
    return key

def generate_direct_license(hwid, expiration_year, limit=10000000):
    """ 
    Gera o arquivo .lic diretamente para uma máquina específica.
    Útil se o cliente tiver problemas com a ativação manual.
    """
    license_data = {
        "hwid": hwid,
        "status": "ACTIVE",
        "expiration": f"{expiration_year}-12-31",
        "total_limit": limit,
        "current_usage": 0,
        "modules": ["all"]
    }
    
    json_str = json.dumps(license_data)
    encrypted = encrypt_data(json_str)
    
    filename = f"hemn_{hwid}.lic"
    with open(filename, 'w') as f:
        f.write(encrypted)
    
    print(f"\nLICENÇA DIRETA GERADA: {filename}")
    print(f"Instrução: Envie este arquivo para o cliente e peça para ele renomear para 'hemn.lic' ")
    print(f"e colocar na pasta C:\\HEMN_SYSTEM_DB\\")

if __name__ == "__main__":
    print("-" * 30)
    print(" HEMN SYSTEM - MASTER KEYGEN ")
    print("-" * 30)
    print("1. Gerar Chave de Ativação (Manual)")
    print("2. Gerar Arquivo de Licença Direto (HWID Lock)")
    
    choice = input("\nEscolha uma opção: ")
    
    if choice == "1":
        year = input("Ano de expiração (Ex: 2026, 2027): ")
        generate_key_string("ANUAL", year)
    elif choice == "2":
        hwid = input("HWID do cliente (Copiado das Configurações): ")
        year = input("Ano de expiração: ")
        limit = input("Limite de registros (Padrão 10.000.000): ")
        if not limit: limit = 10000000
        generate_direct_license(hwid, year, int(limit))
    else:
        print("Opção inválida.")
