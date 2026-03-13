import sqlite3

db_path = r"C:\Users\Junior T.I\OneDrive\Área de Trabalho\cruzar\cnpj.db"
try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(estabelecimento)")
    columns = cursor.fetchall()
    for col in columns:
        print(col)
    conn.close()
except Exception as e:
    print(f"Erro: {e}")
