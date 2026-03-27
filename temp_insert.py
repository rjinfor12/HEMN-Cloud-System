import sqlite3
conn = sqlite3.connect('hemn_cloud.db')
cursor = conn.cursor()
cursor.execute("INSERT INTO background_tasks (id, module, status, progress, message, created_at) VALUES (?, ?, ?, ?, ?, ?)", 
               ('cancel-test', 'EXTRACTION', 'CANCELLED', 100, 'Processo cancelado pelo usuário.', '2026-03-27T13:40:00'))
conn.commit()
conn.close()
print("DUMMY TASK INSERTED")
