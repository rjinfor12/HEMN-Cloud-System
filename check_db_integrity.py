
import sqlite3

db_path = r"C:\HEMN_SYSTEM_DB\cnpj.db"

def check_db():
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        print("Checking integrity...")
        cursor.execute("PRAGMA integrity_check(1)")
        res = cursor.fetchone()
        print(f"Result: {res}")
        
        print("Checking tables...")
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print(f"Tables: {[t[0] for t in tables]}")
        
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_db()
