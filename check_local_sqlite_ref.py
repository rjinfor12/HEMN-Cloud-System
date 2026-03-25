import sqlite3, os

db = r"c:\Users\Junior T.I\.gemini\antigravity\scratch\data_analysis\cnpj.db"
if os.path.exists(db):
    conn = sqlite3.connect(db)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM _referencia")
        print("=== _referencia (SQLite Local) ===")
        for row in cursor.fetchall():
            print(row)
    except Exception as e:
        print(f"Erro ao ler _referencia: {e}")
    conn.close()
else:
    print("cnpj.db local não encontrado.")
