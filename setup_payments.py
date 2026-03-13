import sqlite3
import os

DB_PATH = "hemn_cloud.db"

def setup_payments_table():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Tabela para rastreio de pagamentos ASAAS
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS asaas_payments (
        id TEXT PRIMARY KEY,          -- ID da cobrança no ASAAS (pay_...)
        username TEXT NOT NULL,
        amount REAL NOT NULL,
        credits REAL NOT NULL,
        status TEXT NOT NULL,         -- 'PENDING', 'RECEIVED', 'CONFIRMED', 'OVERDUE'
        payment_link TEXT,
        pix_payload TEXT,
        pix_image_base64 TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        confirmed_at DATETIME,
        FOREIGN KEY (username) REFERENCES users (username)
    )
    """)
    
    conn.commit()
    conn.close()
    print("Tabela asaas_payments criada/verificada com sucesso.")

if __name__ == "__main__":
    setup_payments_table()
