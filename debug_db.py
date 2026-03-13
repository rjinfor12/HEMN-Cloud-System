import sqlite3
import os

db_path = r"C:\HEMN_SYSTEM_DB\cnpj.db"

if not os.path.exists(db_path):
    print(f"Error: Database {db_path} not found.")
    exit(1)

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("--- TABLES ---")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    for t in tables:
        print(f"Table: {t[0]}")
    
    print("\n--- INDEXES ON estabelecimento ---")
    cursor.execute("PRAGMA index_list('estabelecimento')")
    indexes = cursor.fetchall()
    for idx in indexes:
        print(f"Index: {idx[1]} (Unique: {idx[2]})")
        cursor.execute(f"PRAGMA index_info('{idx[1]}')")
        cols = cursor.fetchall()
        for col in cols:
            print(f"  - Column: {col[2]}")
            
    print("\n--- SCHEMA estabelecimento ---")
    cursor.execute("PRAGMA table_info('estabelecimento')")
    info = cursor.fetchall()
    for col in info:
        print(f"Col {col[0]}: {col[1]} ({col[2]})")

    conn.close()
except Exception as e:
    print(f"Error: {e}")
