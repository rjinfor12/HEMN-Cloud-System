import sqlite3
db_path = r"C:\Users\Junior T.I\scratch\data_analysis\cnpj.db"
conn = sqlite3.connect(db_path)
cur = conn.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
print("Tables:", cur.fetchall())
conn.close()
