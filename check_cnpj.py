import clickhouse_connect
import sys

def check():
    try:
        c = clickhouse_connect.get_client(host='localhost', username='default')
        q = """
            SELECT s.socio_chave, count(distinct e.uf) as ufs_count, groupArray(distinct e.uf) as ufs
            FROM hemn.socios s
            JOIN hemn.estabelecimento e ON s.cnpj_basico = e.cnpj_basico
            WHERE s.socio_chave IN (
                SELECT socio_chave FROM hemn.socios WHERE socio_chave != '' LIMIT 1000
            )
            GROUP BY s.socio_chave
            HAVING ufs_count > 1
            LIMIT 10
        """
        res = c.query(q)
        print(f"Sócios com empresas em múltiplos estados (Amostra):")
        for row in res.result_rows:
            print(f"- {row[0]} | UFs: {row[2]}")
    except Exception as e:
        print(f"Erro: {e}")

if __name__ == '__main__':
    check()
