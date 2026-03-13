import sqlite3
import os

def merge_databases():
    old_db = r"C:\Users\Junior T.I\Documents\HEMN_SYSTEM_Suite\server\hemn_cloud_v2.db"
    # If the path above is wrong based on search, I'll use the one I found:
    alt_old_db = r"C:\Users\Junior T.I\.gemini\antigravity\scratch\HEMN_SYSTEM_Suite\server\hemn_cloud_v2.db"
    new_db = r"C:\Users\Junior T.I\.gemini\antigravity\scratch\data_analysis\hemn_cloud.db"

    source_db = alt_old_db if os.path.exists(alt_old_db) else old_db
    
    if not os.path.exists(source_db):
        print(f"ERRO: Banco de origem não encontrado em {source_db}")
        return

    print(f"Lendo dados de: {source_db}")
    print(f"Destino: {new_db}")

    conn_new = sqlite3.connect(new_db)
    conn_old = sqlite3.connect(source_db)
    conn_old.row_factory = sqlite3.Row

    cursor_old = conn_old.execute("SELECT * FROM users")
    users = cursor_old.fetchall()

    for user in users:
        u_dict = dict(user)
        username = u_dict['username']
        
        # Check if user exists in NEW
        exists = conn_new.execute("SELECT 1 FROM users WHERE username = ?", (username,)).fetchone()
        
        if exists:
            print(f"PULANDO: Usuário '{username}' já existe no novo banco.")
            continue
        
        # Map fields
        new_user = {
            'username': u_dict['username'],
            'password': u_dict.get('password_hash') or u_dict.get('password'),
            'full_name': u_dict.get('full_name'),
            'role': u_dict.get('role', 'USER'),
            'status': u_dict.get('status', 'ACTIVE'),
            'expiration': u_dict.get('expiration'),
            'total_limit': u_dict.get('total_limit', 1000.0),
            'current_usage': u_dict.get('current_usage', 0.0)
        }
        
        cols = new_user.keys()
        placeholders = ", ".join(["?"] * len(cols))
        col_names = ", ".join(cols)
        vals = [new_user[c] for c in cols]
        
        try:
            conn_new.execute(f"INSERT INTO users ({col_names}) VALUES ({placeholders})", vals)
            print(f"ADICIONADO: Usuário '{username}' recuperado com sucesso.")
        except Exception as e:
            print(f"ERRO ao inserir '{username}': {e}")

    conn_new.commit()
    conn_new.close()
    conn_old.close()
    print("\nProcesso de mesclagem concluído.")

if __name__ == "__main__":
    merge_databases()
