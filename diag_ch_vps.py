import clickhouse_connect
import time

def check_perf():
    try:
        client = clickhouse_connect.get_client(host='localhost', port=8123, username='default', password='')
        
        print("--- Table Structures ---")
        for table in ['estabelecimento', 'empresas']:
            create_stmt = client.command(f"SHOW CREATE TABLE hemn.{table}")
            print(f"\nTable: {table}\n{create_stmt}")
        
        print("\n--- Table Sizes ---")
        sizes = client.query("SELECT table, formatReadableSize(sum(data_compressed_bytes)) AS comp, formatReadableSize(sum(data_uncompressed_bytes)) AS uncomp, sum(rows) FROM system.parts WHERE database = 'hemn' GROUP BY table")
        for row in sizes.result_rows:
            print(row)

        print("\n--- Recent Long Queries ---")
        queries = client.query("""
            SELECT 
                query, 
                query_duration_ms / 1000 as duration_s, 
                formatReadableSize(memory_usage) as mem,
                read_rows,
                formatReadableSize(read_bytes) as read_bytes
            FROM system.query_log 
            WHERE type = 'QueryFinish' 
              AND query LIKE '%FROM hemn.estabelecimento%'
            ORDER BY event_time DESC 
            LIMIT 3
        """)
        for row in queries.result_rows:
            print(row)
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_perf()
