import sqlite3
import os

db_path = r'C:\HEMN_SYSTEM_DB\cnpj.db'

if not os.path.exists(db_path):
    print(f"ERRO: Arquivo {db_path} não encontrado.")
else:
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Checking _metadata table (if it exists in SQLite too)
        # Note: In SQLite it might just be a table or the script might not have added it yet.
        # But let's check.
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='_metadata'")
        if cursor.fetchone():
            cursor.execute("SELECT value FROM _metadata WHERE key='db_version'")
            row = cursor.fetchone()
            if row:
                print(f"VERSÃO NO ARQUIVO LOCAL: {row[0]}")
            else:
                print("VERSÃO NO ARQUIVO LOCAL: Não encontrada na tabela _metadata.")
        else:
            # Fallback: check date of a record or just say metadata missing
            print("TABELA _metadata não existe no SQLite local.")
            
        cursor.execute("SELECT count() FROM empresas")
        print(f"TOTAL DE EMPRESAS NO LOCAL: {cursor.fetchone()[0]}")
        
        conn.close()
    except Exception as e:
        print(f"ERRO ao ler SQLite: {e}")
