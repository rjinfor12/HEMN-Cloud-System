
import clickhouse_connect
import sqlite3
import os

DB_PATH = "/var/www/hemn_cloud/hemn_cloud.db"

def test_clickhouse():
    try:
        print("Connecting to ClickHouse...")
        client = clickhouse_connect.get_client(host='localhost', port=8123, username='default', password='')
        res = client.query("SELECT count() FROM hemn.estabelecimento")
        print(f"ClickHouse test SUCCESS. Count: {res.first_row}")
    except Exception as e:
        print(f"ClickHouse test FAILED: {str(e)}")

def test_sqlite():
    try:
        print(f"Connecting to SQLite at {DB_PATH}...")
        conn = sqlite3.connect(DB_PATH)
        res = conn.execute("SELECT count() FROM background_tasks").fetchone()
        print(f"SQLite test SUCCESS. Task count: {res[0]}")
        conn.close()
    except Exception as e:
        print(f"SQLite test FAILED: {str(e)}")

if __name__ == "__main__":
    test_clickhouse()
    test_sqlite()
