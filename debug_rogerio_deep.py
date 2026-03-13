import sqlite3
conn = sqlite3.connect(r'C:\HEMN_SYSTEM_DB\cnpj.db')
cursor = conn.cursor()

cnpjs = ['57863854', '08265765', '51763851', '18528540']
mapping = {'01':'NULA','02':'ATIVA','03':'SUSPENSA','04':'INAPTA','08':'BAIXADA'}

for c in cnpjs:
    cursor.execute("SELECT e.razao_social, s.situacao_cadastral FROM empresas e JOIN estabelecimento s ON e.cnpj_basico = s.cnpj_basico WHERE e.cnpj_basico = ?", [c])
    res = cursor.fetchone()
    if res:
        status = mapping.get(str(res[1]).zfill(2), 'DESCONHECIDA')
        print(f"CNPJ: {c} | Razao: {res[0]} | Status: {status} ({res[1]})")
    else:
        print(f"CNPJ: {c} | NÃO ENCONTRADO NO ESTABELECIMENTO")

conn.close()
