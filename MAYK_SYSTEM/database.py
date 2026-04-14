import sqlite3
import os

class MaykDatabase:
    def __init__(self, db_path="mayk_crm.db"):
        self.db_path = db_path
        self._create_tables()

    def get_connection(self):
        return sqlite3.connect(self.db_path)

    def _create_tables(self):
        """ Inicializa e sincroniza as tabelas """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    email TEXT UNIQUE,
                    document TEXT,
                    group_id INTEGER,
                    role TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sales (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    identificador TEXT UNIQUE,
                    consultor INTEGER,
                    tipo_cliente TEXT,
                    nome_cliente TEXT,
                    documento_cliente TEXT,
                    email TEXT,
                    tel_principal TEXT,
                    tel_celular TEXT,
                    status_atual_venda INTEGER DEFAULT 6,
                    valor_manual REAL,
                    tipo_pagamento TEXT,
                    portabilidade TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(consultor) REFERENCES users(id)
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sale_addresses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sale_id INTEGER,
                    type TEXT,
                    street TEXT,
                    number TEXT,
                    district TEXT,
                    city TEXT,
                    uf TEXT,
                    cep TEXT,
                    FOREIGN KEY(sale_id) REFERENCES sales(id)
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sale_products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sale_id INTEGER,
                    product_name TEXT,
                    qtd INTEGER DEFAULT 1,
                    FOREIGN KEY(sale_id) REFERENCES sales(id)
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS status (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT
                )
            ''')
            
            # Se a tabela status estiver vazia, popular com básicos
            if cursor.execute("SELECT COUNT(*) FROM status").fetchone()[0] == 0:
                cursor.executemany("INSERT INTO status (id, name) VALUES (?, ?)", [
                    (6, "Triagem Inicial"),
                    (1, "Aprovada"),
                    (2, "Instalada"),
                    (3, "Cancelada / Recusada")
                ])
                
            conn.commit()

    def save_sale(self, data):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            query = '''
                INSERT INTO sales (
                    identificador, consultor, tipo_cliente, nome_cliente,
                    documento_cliente, email, tel_principal, status_atual_venda,
                    valor_manual, tipo_pagamento, portabilidade
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            '''
            cursor.execute(query, (
                data.get("identificador"),
                data.get("consultor", 1),
                data.get("tipo_cliente", "PF"),
                data.get("nome_cliente", ""),
                data.get("documento_cliente", ""),
                data.get("email", ""),
                data.get("tel_principal", ""),
                data.get("status_atual_venda", 6),
                data.get("valor_manual", 0.0),
                data.get("tipo_pagamento", ""),
                data.get("portabilidade", "")
            ))
            conn.commit()
            return cursor.lastrowid

    def get_all_sales(self):
        with self.get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM sales ORDER BY id DESC")
            return [dict(row) for row in cursor.fetchall()]

    def get_statuses(self):
        with self.get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM status")
            return [dict(row) for row in cursor.fetchall()]

    def add_status(self, name):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO status (name) VALUES (?)", (name,))
            conn.commit()

    def delete_status(self, status_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            # Impede excluir status que já tenham vendas
            if cursor.execute("SELECT COUNT(*) FROM sales WHERE status_atual_venda=?", (status_id,)).fetchone()[0] == 0:
                cursor.execute("DELETE FROM status WHERE id=?", (status_id,))
                conn.commit()
                return True
            return False

    def get_users(self):
        with self.get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users")
            return [dict(row) for row in cursor.fetchall()]
            
    def add_user(self, name, email, document, role):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("INSERT INTO users (name, email, document, role) VALUES (?, ?, ?, ?)", (name, email, document, role))
                conn.commit()
                return True
            except sqlite3.IntegrityError:
                return False

    def delete_user(self, user_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            # Impede excluir se já fez vendas
            if cursor.execute("SELECT COUNT(*) FROM sales WHERE consultor=?", (user_id,)).fetchone()[0] == 0:
                cursor.execute("DELETE FROM users WHERE id=?", (user_id,))
                conn.commit()
                return True
            return False

    def update_sale_status(self, sale_id, new_status_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE sales SET status_atual_venda=?, updated_at=CURRENT_TIMESTAMP WHERE id=?", (new_status_id, sale_id))
            conn.commit()

    def save_address(self, sale_id, address_data):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO sale_addresses (sale_id, type, street, number, district, city, uf, cep)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                sale_id,
                address_data.get("type", "Instalação"),
                address_data.get("street", ""),
                address_data.get("number", ""),
                address_data.get("district", ""),
                address_data.get("city", ""),
                address_data.get("uf", ""),
                address_data.get("cep", "")
            ))
            conn.commit()

    def save_product(self, sale_id, product_data):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO sale_products (sale_id, product_name, qtd)
                VALUES (?, ?, ?)
            ''', (
                sale_id,
                product_data.get("product_name", ""),
                product_data.get("qtd", 1)
            ))
            conn.commit()

    def get_sale_addresses(self, sale_id):
        with self.get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM sale_addresses WHERE sale_id=?", (sale_id,))
            return [dict(row) for row in cursor.fetchall()]

    def get_sale_products(self, sale_id):
        with self.get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM sale_products WHERE sale_id=?", (sale_id,))
            return [dict(row) for row in cursor.fetchall()]

    def get_dashboard_metrics(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Total de Vendas
            total_sales = cursor.execute("SELECT COUNT(*) FROM sales").fetchone()[0]
            
            # Soma do Valor Manual
            total_value = cursor.execute("SELECT SUM(valor_manual) FROM sales").fetchone()[0]
            total_value = total_value if total_value else 0.0
            
            # Contagem agrupada por status
            cursor.execute('''
                SELECT st.name, COUNT(s.id) 
                FROM status st
                LEFT JOIN sales s ON s.status_atual_venda = st.id
                GROUP BY st.name
            ''')
            status_counts = {row[0]: row[1] for row in cursor.fetchall()}
            
            return {
                "total_sales": total_sales,
                "total_value": total_value,
                "status_counts": status_counts
            }
