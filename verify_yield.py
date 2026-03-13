import sqlite3
import pandas as pd
import clickhouse_connect
import json
import re

def test_ceara_claro():
    print("Connecting to ClickHouse...")
    client = clickhouse_connect.get_client(host='129.121.45.136', port=8123, username='default', password='')
    
    print("Fetching 100,000 mobile numbers from Ceara...")
    q = """
    SELECT ddd1, telefone1, ddd2, telefone2
    FROM hemn.estabelecimento 
    WHERE situacao_cadastral = '02' AND uf = 'CE' 
      AND (
          (length(telefone1) >= 8 AND substring(telefone1, 1, 1) IN ('6','7','8','9'))
          OR
          (length(telefone2) >= 8 AND substring(telefone2, 1, 1) IN ('6','7','8','9'))
      )
    LIMIT 100000
    """
    res = client.query(q)
    rows = res.result_rows
    print(f"Fetched {len(rows)} matching rows.")
    
    # Process phones
    mobiles = []
    for row in rows:
        d1, t1, d2, t2 = row
        t1 = str(t1).replace('.0','').replace('nan','')
        t2 = str(t2).replace('.0','').replace('nan','')
        if len(t1) >= 8 and t1[0] in '6789':
            full = d1 + t1
            if len(full) == 10 and full[2] in '6789':
                full = full[:2] + '9' + full[2:]
            mobiles.append(full)
        elif len(t2) >= 8 and t2[0] in '6789':
            full = d2 + t2
            if len(full) == 10 and full[2] in '6789':
                full = full[:2] + '9' + full[2:]
            mobiles.append(full)
            
    print(f"Parsed {len(mobiles)} mobile numbers. Example: {mobiles[:5]}")
    
    # Run operator mapper local replica
    print("Connecting to Carrier DB...")
    # NOTE: ssh might not be able to read local DB, wait, this script runs on Local Desktop? No, the VPS is remote.
    # The local Desktop does not have hemn_carrier.db!
    # I should write a script and throw it to the VPS and run it there!

