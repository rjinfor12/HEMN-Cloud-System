import clickhouse_connect

def inspect():
    client = clickhouse_connect.get_client(host='localhost', port=8123, username='default', password='')
    
    tables = ['hemn.empresas', 'hemn.estabelecimento', 'hemn.socios', 'hemn.municipio']
    
    for t in tables:
        print(f"\n--- {t} ---")
        try:
            res = client.query(f"DESCRIBE TABLE {t}")
            for row in res.result_rows:
                print(f"{row[0]}: {row[1]}")
        except Exception as e:
            print(f"Error describing {t}: {e}")

    client.close()

if __name__ == "__main__":
    inspect()
