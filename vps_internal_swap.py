import clickhouse_connect
import os

def do_swap():
    try:
        client = clickhouse_connect.get_client(host='localhost', port=8123, username='default', password='')
        
        # Tabelas que confirmamos que têm dados
        tables = ["empresas", "estabelecimento", "socios", "municipio"]
        
        # Outras que o script de ingestão criou (pode falhar se não existirem)
        extra_tables = ["paises", "natureza_juridica", "qualificacao_socio", "cnae", "motivo", "simples"]
        
        # Filtrar apenas as tabelas que REALMENTE existem em hemn_update_tmp
        res = client.query("SHOW TABLES FROM hemn_update_tmp")
        existing_in_tmp = [row[0] for row in res.result_rows]
        print(f"EXISTING IN TMP: {existing_in_tmp}")
        
        target_tables = [t for t in tables + extra_tables if t in existing_in_tmp]
        
        if not target_tables:
            print("ERROR: No tables found to swap!")
            return

        rename_parts = []
        import uuid
        suffix = uuid.uuid4().hex[:4]
        
        for t in target_tables:
            # 1. Mover atual para backup
            rename_parts.append(f"hemn.{t} TO hemn_backup_old.{t}_{suffix}")
            # 2. Mover nova para produção
            rename_parts.append(f"hemn_update_tmp.{t} TO hemn.{t}")
            
        rename_sql = f"RENAME TABLE {', '.join(rename_parts)}"
        print(f"EXECUTING SQL: {rename_sql}")
        client.command(rename_sql)
        
        # Atualizar Meta
        client.command("INSERT INTO hemn._metadata (key, value) VALUES ('db_version', 'Março/2026 (Titanium)') ON DUPLICATE KEY UPDATE value = 'Março/2026 (Titanium)'")
        
        print("SUCCESS: Atomic Swap Completed via Python Connect.")
        
    except Exception as e:
        print(f"SWAP FAILED: {e}")

if __name__ == "__main__":
    do_swap()
