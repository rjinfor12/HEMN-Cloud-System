import sqlite3
import requests
import time
from datetime import datetime

DB_PATH = "hemn_cloud.db"

def setup_test():
    print("Conectando ao banco...")
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    
    # Pega um úsuario qualquer
    user = conn.execute("SELECT username, total_limit FROM users LIMIT 1").fetchone()
    if not user:
        print("Nenhum usuario no banco")
        return
    
    username = user[0]
    initial_limit = user[1]
    pay_id = f"pay_test_{int(time.time())}"
    
    print(f"Usuario escolhido: {username}")
    print(f"Limite atual: {initial_limit}")
    
    # Insere pagamento pendente do Plano Essential (500000 creditos)
    conn.execute("""
        INSERT INTO asaas_payments (id, username, amount, credits, status)
        VALUES (?, ?, ?, ?, ?)
    """, (pay_id, username, 899.00, 500000, "PENDING"))
    conn.commit()
    conn.close()
    
    print(f"Pagamento {pay_id} injetado como PENDING.")
    
    # Chama o webhook localmente
    print("Disparando webhook...")
    try:
        from fastapi.testclient import TestClient
        from HEMN_Cloud_Server import app
        client = TestClient(app)
        
        payload = {
            "event": "PAYMENT_RECEIVED",
            "payment": {
                "id": pay_id,
                "billingType": "PIX"
            }
        }
        res = client.post("/areadocliente/webhook/asaas", json=payload)
        print(f"Webhook status: {res.status_code}")
        
    except Exception as e:
        print(f"Erro ao chamar webhook via test client: {e}")
        
    # Verifica o banco de dados
    print("Verificando resultados...")
    conn = sqlite3.connect(DB_PATH)
    user_after = conn.execute("SELECT username, total_limit, expiration FROM users WHERE username = ?", (username,)).fetchone()
    pay_after = conn.execute("SELECT status FROM asaas_payments WHERE id = ?", (pay_id,)).fetchone()
    conn.close()
    
    print(f"Limite apos webhook: {user_after[1]} (Esperado: {initial_limit + 500000})")
    print(f"Expiracao definida para: {user_after[2]}")
    print(f"Status do pagamento: {pay_after[0]}")
    
    if user_after[1] == initial_limit + 500000 and user_after[2] and pay_after[0] == "RECEIVED":
        print("SUCESSO: Webhook confirmou o pagamento, injetou os creditos e adicionou a validade!")
    else:
        print("FALHA na verificacao.")

if __name__ == "__main__":
    setup_test()
