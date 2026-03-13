import clickhouse_connect

client = clickhouse_connect.get_client(host='129.121.45.136', username='default', password='', port=8123)

# 1. Check if the MEI basico is in full_view
print("Checking 18528540 in full_view...")
res1 = client.query("SELECT cnpj_basico, cnpj_completo, razao_social FROM hemn.full_view WHERE cnpj_basico = '18528540'")
print(f"Results: {res1.result_rows}")

# 2. Check if the other company is in full_view
print("\nChecking 38262186 in full_view...")
res2 = client.query("SELECT cnpj_basico, cnpj_completo, razao_social FROM hemn.full_view WHERE cnpj_basico = '38262186'")
print(f"Results: {res2.result_rows}")

# 3. Check socios for both
print("\nChecking socios for these Companies...")
res3 = client.query("SELECT * FROM hemn.socios WHERE cnpj_basico IN ('18528540', '38262186')")
print(f"Socios: {res3.result_rows}")

# 4. Check if Rogerio exists anywhere in socios
print("\nChecking Rogerio in entire socios table...")
res4 = client.query("SELECT cnpj_basico, nome_socio FROM hemn.socios WHERE nome_socio LIKE '%ROGERIO ELIAS DO NASCIMENTO JUNIOR%'")
print(f"Rogerio in Socios: {res4.result_rows}")
