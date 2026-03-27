
import sqlite3
conn = sqlite3.connect('hemn_cloud.db')
conn.execute("""
CREATE TABLE IF NOT EXISTS system_metadata (
    key TEXT PRIMARY KEY,
    value TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
""")
# Inserir valores iniciais para carrier
conn.execute("INSERT OR IGNORE INTO system_metadata (key, value) VALUES ('last_carrier_ftp_timestamp', '2026-03-01 00:00:00');")
conn.execute("INSERT OR IGNORE INTO system_metadata (key, value) VALUES ('last_carrier_check_timestamp', '2026-03-01 00:00:00');")
conn.commit()
conn.close()
print("Tabela system_metadata criada com sucesso.")
