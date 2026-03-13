import sqlite3
import pandas as pd

db_path = r"C:\Users\Junior T.I\OneDrive\Área de Trabalho\cruzar\cnpj.db"

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("Colunas da tabela estabelecimento:")
    cursor.execute("PRAGMA table_info(estabelecimento)")
    for info in cursor.fetchall(): print(f"  {info[1]} ({info[2]})")
    
    conn.close()
except Exception as e:
    print(f"Erro: {e}")
