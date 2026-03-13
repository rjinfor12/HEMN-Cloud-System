import sqlite3

def diag_db(path, name):
    print(f"\n--- Database: {name} ({path}) ---")
    try:
        conn = sqlite3.connect(path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [r[0] for r in cursor.fetchall()]
        print(f"Tables: {tables}")
        for t in tables:
            cursor.execute(f"PRAGMA table_info({t});")
            info = cursor.fetchall()
            cols = [i[1] for i in info]
            print(f"  Table '{t}' columns: {cols}")
        conn.close()
    except Exception as e:
        print(f"Error {name}: {e}")

diag_db(r"C:\HEMN_SYSTEM_DB\cnpj.db", "CNPJ")
diag_db(r"C:\HEMN_SYSTEM_DB\hemn_carrier.db", "Carrier")
