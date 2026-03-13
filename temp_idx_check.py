import sqlite3
import os

db_path = "cnpj.db" if os.path.exists("cnpj.db") else r"C:\\Users\\Junior T.I\\Desktop\\storage\\cnpj.db"
if not os.path.exists(db_path): db_path = r"C:\\Users\\Junior T.I\\OneDrive\\Área de Trabalho\\storage\\cnpj.db"
print(f"Connecting: {db_path}")

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT type, name, tbl_name, sql FROM sqlite_master WHERE type='index'")
    indexes = cursor.fetchall()
    
    print("INDEXES FOUND:")
    for idx in indexes:
        print(f"Table: {idx[2]} | Index: {idx[1]} | SQL: {idx[3]}")
except Exception as e:
    print(f"Error: {e}")
