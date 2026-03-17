import clickhouse_connect

def check_schema():
    client = clickhouse_connect.get_client(host='localhost', port=8123, username='default', password='')
    
    print("--- SCHEMA: hemn.socios ---")
    res = client.query("DESCRIBE TABLE hemn.socios")
    for row in res.result_rows:
        print(f"{row[0]}: {row[1]}")
        
    print("\n--- SCHEMA: hemn.estabelecimento ---")
    res = client.query("DESCRIBE TABLE hemn.estabelecimento")
    for row in res.result_rows:
        print(f"{row[0]}: {row[1]}")

    print("\n--- SCHEMA: hemn.empresas ---")
    res = client.query("DESCRIBE TABLE hemn.empresas")
    for row in res.result_rows:
        print(f"{row[0]}: {row[1]}")

if __name__ == "__main__":
    try:
        check_schema()
    except Exception as e:
        print(f"Error: {e}")
