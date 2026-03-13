import clickhouse_connect

try:
    client = clickhouse_connect.get_client(host='localhost', port=8123, username='default', password='')
    
    print("--- TOP NATUREZA JURIDICA ---")
    res = client.query("SELECT natureza_juridica, count(*) as cnt FROM hemn.empresas GROUP BY natureza_juridica ORDER BY cnt DESC LIMIT 10").result_rows
    for r in res:
        print(f"ID {r[0]}: {r[1]:,} registros")

    print("\n--- TOP PORTE EMPRESA ---")
    res = client.query("SELECT porte_empresa, count(*) as cnt FROM hemn.empresas GROUP BY porte_empresa ORDER BY cnt DESC").result_rows
    # 01 – NÃO INFORMADO / 03 – ME / 05 – DEMAIS / 01 - EPP? (Depende da versão da RFB)
    for r in res:
        print(f"ID {r[0]}: {r[1]:,} registros")
            
except Exception as e:
    print(f"Error: {e}")
