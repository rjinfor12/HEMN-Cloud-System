import sqlite3
import os

DB_PATH = r'c:\Users\Junior T.I\.gemini\antigravity\scratch\data_analysis\hemn_cloud.db'

def create_test_clinic():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("UPDATE users SET role='CLINICAS', valor_mensal=1099.0, vencimento_dia=15 WHERE username='junior'")
    conn.commit()
    print("Updated user 'junior' to CLINICAS role for testing.")
    conn.close()

if __name__ == "__main__":
    create_test_clinic()
