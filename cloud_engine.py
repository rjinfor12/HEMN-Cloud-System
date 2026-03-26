import os
import sqlite3
import pandas as pd
import threading
import time
from datetime import datetime
import uuid
import shutil
import re
import unicodedata
import ftplib
import tarfile
import bz2
from concurrent.futures import ThreadPoolExecutor
try:
    import clickhouse_connect
except ImportError:
    pass

def remove_accents(input_str):
    if not input_str: return ""
    nfkd_form = unicodedata.normalize('NFKD', input_str)
    return "".join([c for c in nfkd_form if not unicodedata.combining(c)])

def normalize_name(name):
    """Remove common suffixes to improve matching (JUNIOR, FILHO, etc.)"""
    if not name: return ""
    name = remove_accents(str(name).upper().strip())
    suffixes = [' JUNIOR', ' FILHO', ' NETO', ' SOBRINHO', ' JR', ' SEGUNDO', ' TERCEIRO']
    for sfx in suffixes:
        if name.endswith(sfx):
            name = name[:-len(sfx)].strip()
            break
    return name

class CloudEngine:
    def __init__(self, **kwargs):
        import platform
        self.is_linux = (platform.system() == 'Linux')
        if self.is_linux:
            self.db_carrier = "/var/www/hemn_cloud/hemn_carrier.db"
            self.db_path = "/var/www/hemn_cloud/hemn_cloud.db"
        else:
            self.db_carrier = kwargs.get('db_carrier_path')
            self.db_path = kwargs.get('db_path') or "hemn_cloud.db"
        
        self._init_db()
        self._load_carrier_assets()

    def _get_ch_client(self):
        """Retorna uma nova instância de cliente ClickHouse (Thread-Safe)"""
        if not self.is_linux: return None
        try:
            return clickhouse_connect.get_client(host='localhost', port=8123, username='default', password='')
        except Exception as e:
            print(f"[ERROR] Falha ao conectar no ClickHouse: {e}")
            return None

    def search_leads(self, search_type, search_term, scope, uf=None, regiao=None):
        search_type = str(search_type).lower().strip()
        client = self._get_ch_client()
        if not client:
            return {"error": "Conexão com ClickHouse indisponível (Ambiente Windows)"}
        
        where_clauses = []
        params = {}

        # Tipo de Busca
        if search_type == 'cpf':
            cpf_clean = ''.join(filter(str.isdigit, search_term))
            where_clauses.append("cpf = {cpf:String}")
            params['cpf'] = cpf_clean
        elif search_type == 'nome':
            where_clauses.append("nome LIKE {nome:String}")
            params['nome'] = f"%{remove_accents(search_term).upper().strip()}%"
        elif search_type == 'telefone':
            tel_clean = ''.join(filter(str.isdigit, search_term))
            where_clauses.append("(tel_fixo1 = {tel:String} OR celular1 = {tel:String})")
            params['tel'] = tel_clean
        
        # Filtros de Escopo
        if scope == 'ESTADO' and uf:
            where_clauses.append("uf = {uf:String}")
            params['uf'] = uf.upper()
        elif scope == 'REGIAO' and regiao:
            where_clauses.append("regiao = {regiao:String}")
            params['regiao'] = regiao.upper()
        
        if not where_clauses:
            return {"leads": [], "count": 0}

        where_str = " AND ".join(where_clauses)
        query = f"SELECT DISTINCT cpf, nome, dt_nascimento, uf, regiao FROM hemn.leads WHERE {where_str} LIMIT 100"
        
        try:
            result = client.query(query, parameters=params)
            columns = ['cpf', 'nome', 'dt_nascimento', 'uf', 'regiao']
            leads = []
            today = datetime.now()
            for row in result.result_rows:
                lead = dict(zip(columns, row))
                # Calcular idade
                idade = "N/A"
                dt_nasc = lead.get('dt_nascimento', '')
                if dt_nasc and '/' in dt_nasc:
                    try:
                        parts = dt_nasc.split('/')
                        if len(parts) == 3:
                            day, month, year = int(parts[0]), int(parts[1]), int(parts[2])
                            birth_date = datetime(year, month, day)
                            age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
                            idade = str(age)
                    except Exception:
                        pass
                lead['idade'] = idade
                leads.append(lead)
            
            return {"leads": leads, "count": len(leads)}
        except Exception as e:
            print(f"[ERROR] ClickHouse query failed: {e}")
            return {"error": str(e)}
        finally:
            client.close()

    def get_db_version(self):
        """Busca a versão atual do banco de dados na tabela hemn._metadata"""
        if not self.is_linux: return "Ambiente Windows (Local)"
        client = self._get_ch_client()
        if not client: return "Erro de Conexão (ClickHouse)"
        try:
            res = client.query("SELECT value FROM hemn._metadata WHERE key = 'db_version' LIMIT 1")
            if res.result_rows:
                return str(res.result_rows[0][0])
            return "Versão Desconhecida"
        except:
            return "Tabela _metadata não encontrada"
        finally:
            client.close()

    def _load_carrier_assets(self):
        """Loads prefix tree and operator dictionary from data_assets folder"""
        self.prefix_tree = {} # {prefix: operator_code}
        # Initial hardcoded fallback for most common
        self.anatel_dict = {
            "55320": "VIVO", "55321": "CLARO", "55341": "TIM", "55331": "OI",
            "55312": "ALGAR", "55343": "SERCOMTEL", "55306": "SURF", "55301": "ARQIA",
            "55315": "TELECALL", "55322": "BRISANET"
        }
        
        if self.is_linux:
            base_dir = "/var/www/hemn_cloud/data_assets"
        else:
            base_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_assets")
            
        prefix_path = os.path.join(base_dir, "prefix_anatel.csv")
        dict_path = os.path.join(base_dir, "cod_operadora.csv")
        
        # Load Operadora Dictionary from CSV if available
        if os.path.exists(dict_path):
            try:
                import csv
                with open(dict_path, mode='r', encoding='latin1') as f:
                    reader = csv.reader(f)
                    for row in reader:
                        if len(row) >= 2: self.anatel_dict[row[0].strip()] = row[1].strip()
            except: pass
            
        # Load Prefix Tree (Standard ANATEL Base)
        if os.path.exists(prefix_path):
            try:
                df = pd.read_csv(prefix_path, sep=';', dtype=str)
                if 'number' in df.columns and 'company' in df.columns:
                    for _, row in df.iterrows():
                        self.prefix_tree[row['number'].strip()] = row['company'].strip()
            except: pass

    def get_op_name(self, code):
        """Helper to get operator name from RN1/Anatel code"""
        code = str(code).strip()
        name = self.anatel_dict.get(code, f"OUTRA ({code})" if code else "OUTRA")
        # NORMALIZAÇÃO HEMN (Híbrida para clareza e filtros)
        nu = name.upper().strip()
        if "TELEFONICA" in nu or "VIVO" in nu: return "VIVO / TELEFONICA"
        if "CLARO" in nu: return "CLARO"
        if "TIM" in nu: return "TIM"
        if nu == "OI" or nu.startswith("OI ") or "OI S.A" in nu or "OI MOVEL" in nu or "TELEMAR" in nu: 
            return "OI"
        if "ALGAR" in nu: return "ALGAR"
        if "BRISANET" in nu: return "BRISANET"
        if "TELECALL" in nu: return "TELECALL"
        if "SERCOMTEL" in nu: return "SERCOMTEL"
        return name

    def _init_db(self):
        conn = sqlite3.connect(self.db_path, timeout=30)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS background_tasks (
                id TEXT PRIMARY KEY,
                username TEXT,
                module TEXT,
                status TEXT,
                progress REAL,
                message TEXT,
                result_file TEXT,
                record_count INTEGER,
                filters TEXT,
                created_at TEXT
            )
        """)
        
        # Migração: Adiciona coluna 'filters' se não existir (para bancos legados)
        try:
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(background_tasks)")
            columns = [info[1] for info in cursor.fetchall()]
            if 'filters' not in columns:
                print("[MIGRATION] Adicionando coluna 'filters' em background_tasks")
                conn.execute("ALTER TABLE background_tasks ADD COLUMN filters TEXT")
        except Exception as e:
            print(f"[MIGRATION ERROR] Erro ao migrar background_tasks: {e}")

        conn.execute("""
            CREATE TABLE IF NOT EXISTS asaas_payments (
                id TEXT PRIMARY KEY,
                username TEXT,
                amount REAL,
                credits REAL,
                status TEXT,
                pix_payload TEXT,
                pix_image_base64 TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                confirmed_at TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS credit_transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT,
                type TEXT,
                amount REAL,
                module TEXT,
                description TEXT,
                timestamp TEXT
            )
        """)
        conn.commit()
        conn.close()

    def _create_task(self, module="ENRICH", username=None, filters=None):
        tid = str(uuid.uuid4())
        created_at = datetime.now().isoformat()
        conn = sqlite3.connect(self.db_path, timeout=30)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute(
            "INSERT INTO background_tasks (id, username, module, status, progress, message, filters, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (tid, username, module, "QUEUED", 0, "Aguardando início...", filters, created_at)
        )
        conn.commit()
        conn.close()
        return tid

    def cancel_task(self, tid):
        conn = sqlite3.connect(self.db_path, timeout=30)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("UPDATE background_tasks SET status = 'CANCELLED', message = 'Processo cancelado pelo usuário.' WHERE id = ?", (tid,))
        conn.commit()
        conn.close()
        return True

    def hide_task(self, tid):
        conn = sqlite3.connect(self.db_path, timeout=30)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("UPDATE background_tasks SET hidden = 1 WHERE id = ?", (tid,))
        conn.commit()
        conn.close()
        return True

    def get_user_tasks(self, username):
        conn = sqlite3.connect(self.db_path, timeout=30)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.row_factory = sqlite3.Row
        # Include COMPLETED and FAILED tasks from the last 24 hours for UI persistence
        # Only show tasks that are NOT hidden
        rows = conn.execute(
            "SELECT * FROM background_tasks WHERE username = ? COLLATE NOCASE AND hidden = 0 AND (status IN ('QUEUED', 'PROCESSING') OR (status = 'COMPLETED' AND created_at > datetime('now','-24 hours')) OR (status = 'FAILED' AND created_at > datetime('now','-24 hours'))) ORDER BY created_at DESC", 
            (username,)
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def _update_task(self, tid, **kwargs):
        if not kwargs: return
        cols = ", ".join([f"{k} = ?" for k in kwargs.keys()])
        conn = sqlite3.connect(self.db_path, timeout=30)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute(f"UPDATE background_tasks SET {cols} WHERE id = ?", list(kwargs.values()) + [tid])
        conn.commit()
        conn.close()

    def get_task_status(self, tid):
        conn = sqlite3.connect(self.db_path, timeout=30)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT * FROM background_tasks WHERE id = ?", (tid,)).fetchone()
        conn.close()
        if not row: return {"status": "NOT_FOUND"}
        return dict(row)

    def get_internal_stats(self):
        try:
            conn = sqlite3.connect(self.db_path, timeout=30)
            conn.execute("PRAGMA journal_mode=WAL")
            # Return data in the format expected by the frontend (index_vps.html)
            stats = {
                "tasks": {
                    "active": conn.execute("SELECT COUNT(*) FROM background_tasks WHERE status = 'PROCESSING'").fetchone()[0],
                    "queued": conn.execute("SELECT COUNT(*) FROM background_tasks WHERE status = 'QUEUED'").fetchone()[0],
                    "completed": conn.execute("SELECT COUNT(*) FROM background_tasks WHERE status = 'COMPLETED' AND (date(created_at) = date('now') OR created_at > datetime('now','-24 hours'))").fetchone()[0],
                },
                "enrich_slots_available": 2, # Fallback value
                "recent_activities": []
            }
            
            # Fetch recent activities
            conn.row_factory = sqlite3.Row
            recent = conn.execute("SELECT module, status, progress, message, created_at FROM background_tasks ORDER BY created_at DESC LIMIT 10").fetchall()
            stats["recent_activities"] = [dict(r) for r in recent]
            conn.close()

            # Add potential external ingestion progress (DB Update)
            ingest_task = self._get_ingestion_progress()
            if ingest_task:
                stats["recent_activities"].insert(0, ingest_task)

            return stats
        except Exception as e:
            return {
                "tasks": {"active": 0, "queued": 0, "completed": 0},
                "enrich_slots_available": 2,
                "recent_activities": [],
                "error": str(e)
            }

    def _get_ingestion_progress(self):
        """Checks for external ingestion logs and returns a virtual task if active."""
        log_path = "/var/www/hemn_cloud/ingest_march_2026.log"
        if not os.path.exists(log_path): return None
        
        try:
            # Check if log was updated recently (last 30 minutes)
            mtime = os.path.getmtime(log_path)
            if time.time() - mtime > 1800: return None
            
            with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
                if not lines: return None
                
                # Simple progress heuristic: find "Starting <file>..." and "Finished <file>..."
                current_file = "Processando..."
                completed_count = 0
                for line in reversed(lines):
                    if "Starting" in line and "..." in line:
                        current_file = line.split("Starting")[-1].strip().replace("...", "")
                        break
                    if "Finished" in line:
                        completed_count += 1 # This is not precise but gives a hint

                # Calculate progress based on total FILES (40 files in the script)
                total_files = 40
                # Scan full log once to count "Finished" (expensive but 1170 lines is small)
                all_finished = [l for l in lines if "Finished" in l]
                prog = min(99, int((len(all_finished) / total_files) * 100))
                
                return {
                    "module": "DATABASE_UPDATE",
                    "status": "PROCESSING",
                    "progress": prog,
                    "message": f"Atualizando Base Mar/2026: {current_file}",
                    "created_at": datetime.fromtimestamp(mtime).isoformat()
                }
        except:
            return None

    def get_ch_metrics(self):
        client = self._get_ch_client()
        if not client:
            return {"status": "DISCONNECTED", "uptime": "0", "active_queries": 0}
        try:
            res = client.query("SELECT uptime() as up, count(*) as q FROM system.processes")
            row = res.result_rows[0]
            return {
                "status": "ONLINE",
                "uptime": str(row[0]),
                "active_queries": row[1]
            }
        except:
            return {"status": "OFFLINE", "uptime": "0", "active_queries": 0}

    def count_active_tasks(self, username):
        """Retorna o número de tarefas QUEUED ou PROCESSING de um usuário."""
        if not username: return 0
        try:
            conn = sqlite3.connect(self.db_path, timeout=30)
            conn.execute("PRAGMA journal_mode=WAL")
            count = conn.execute(
                "SELECT COUNT(*) FROM background_tasks WHERE username = ? COLLATE NOCASE AND status IN ('QUEUED', 'PROCESSING')",
                (username,)
            ).fetchone()[0]
            conn.close()
            return count
        except:
            return 0

    def _batch_query(self, sql_template, key_param, values, batch_size=3000, tid=None, base_prog=0, max_prog=0, msg_prefix="", extra_params=None):
        """Execute a query with a large IN() list in safe-sized batches with progress tracking."""
        ch_local = self._get_ch_client()
        if not ch_local: return [], []
        
        all_rows = []
        col_names = []
        total = len(values)
        if total == 0: return [], []
        
        for i in range(0, total, batch_size):
            # Check for cancellation
            if tid:
                status = self.get_task_status(tid)
                if status.get("status") == "CANCELLED": return [], []

            chunk = values[i:i + batch_size]
            params = {key_param: chunk}
            if extra_params: params.update(extra_params)
            # Otimização v1.8.12: Limitar threads para permitir concorrência de usuários
            res = ch_local.query(sql_template + " SETTINGS max_threads = 1", params)
            all_rows.extend(res.result_rows)
            # Log names once
            if not col_names:
                print(f"[DEBUG] _batch_query: col_names from res: {getattr(res, 'column_names', 'ATTR_NOT_FOUND')}")
            
            if not col_names and getattr(res, 'column_names', None):
                col_names = list(res.column_names)
            
            if tid and max_prog > base_prog:
                prog = base_prog + int((i / total) * (max_prog - base_prog))
                self._update_task(tid, progress=prog, message=f"{msg_prefix} ({i:,}/{total:,})...")
                # Yield to OS for concurrency in multi-user environments (High Priority v1.8.12)
                time.sleep(0.1) 

        return all_rows, col_names

    def _parse_address_columns(self, row):
        # Simplificado para o exemplo, manter original se possível
        tipo = row.get('tipo_logradouro', '')
        logra = row.get('logradouro', '')
        num = row.get('numero', '')
        comp = row.get('complemento', '')
        bairro = row.get('bairro', '')
        muni = row.get('municipio_nome', '')
        uf = row.get('uf', '')
        cep = row.get('cep', '')
        full_logra = f"{tipo} {logra}".strip()
        return [full_logra, num, comp, bairro, muni, uf, cep]

    def _parse_contact_columns(self, row):
        ddd1 = str(row.get('ddd1', '')).strip()
        tel1 = str(row.get('telefone1', '')).strip()
        ddd2 = str(row.get('ddd2', '')).strip()
        tel2 = str(row.get('telefone2', '')).strip()
        email = str(row.get('correio_eletronico', '')).strip()
        
        def format_tel(d, t):
            t = ''.join(filter(str.isdigit, t))
            d = ''.join(filter(str.isdigit, d))
            if not t: return ""
            # Adicionar 9º dígito se for celular (8 dígitos começando com 6-9)
            if len(t) == 8 and t[0] in '6789':
                t = '9' + t
            return f"{d}{t}"
        
        f1 = format_tel(ddd1, tel1)
        if f1: return [f1, "FIXO/CEL", email]
        f2 = format_tel(ddd2, tel2)
        if f2: return [f2, "FIXO/CEL", email]
        return ["", "", email]

    def start_enrich(self, input_file, output_dir, name_col, cpf_col, username=None, perfil="TODOS"):
        print(f"[DEBUG] start_enrich called: input={input_file}, name_col={name_col}, cpf_col={cpf_col}, user={username}, perfil={perfil}")
        fname = os.path.basename(input_file)
        f_summary = f"[v1.9.1] Enriquecer: {fname} (Perfil: {perfil})"
        tid = self._create_task(module="ENRICH", username=username, filters=f_summary)
        threading.Thread(target=self._run_enrich, args=(tid, input_file, output_dir, name_col, cpf_col, perfil), daemon=True).start()
        return tid

    def start_carrier_update(self, username="admin"):
        """Inicia atualização da base de operadoras via FTP"""
        tid = self._create_task(module="CARRIER_UPDATE", username=username, filters="[ADMIN] Atualizar Base Operadoras")
        threading.Thread(target=self._run_carrier_update, args=(tid,), daemon=True).start()
        return tid

    def _run_carrier_update(self, tid):
        """Thread que executa o download e ingestão do FTP"""
        host = "ftp.portabilidadecelular.com"
        port = 2157
        user = "MAYK"
        passwd = "Mayk@2025"
        filename = "portabilidade.tar.bz2"
        local_zip = os.path.join(os.getcwd(), "portabilidade.tar.bz2")
        
        try:
            self._update_task(tid, progress=5, message="Conectando ao FTP...")
            ftp = ftplib.FTP()
            ftp.connect(host, port, timeout=60)
            ftp.login(user, passwd)
            
            # Obter tamanho para progresso
            size = ftp.size(filename)
            downloaded = 0
            
            def ftp_callback(data):
                nonlocal downloaded
                downloaded += len(data)
                if size > 0:
                    pct = int((downloaded / size) * 40) + 5 # 5% a 45% é download
                    self._update_task(tid, progress=pct, message=f"Baixando base... {downloaded/1024/1024:.1f}MB")

            with open(local_zip, 'wb') as f:
                ftp.retrbinary(f"RETR {filename}", ftp_callback)
            ftp.quit()
            
            self._update_task(tid, progress=50, message="Extraindo arquivos...")
            # Extração tar.bz2
            extracted_file = None
            with tarfile.open(local_zip, "r:bz2") as tar:
                tar.extractall(path=os.getcwd())
                # Procurar o arquivo extraído (geralmente portabilidade.csv ou similar)
                for member in tar.getmembers():
                    if member.isfile():
                        extracted_file = os.path.join(os.getcwd(), member.name)
                        break
            
            if not extracted_file or not os.path.exists(extracted_file):
                raise Exception("Arquivo extraído não encontrado.")

            self._update_task(tid, progress=60, message="Iniciando ingestão SQLite...")
            
            # Ingestão no SQLite hemn_carrier.db
            conn = sqlite3.connect(self.db_carrier)
            conn.execute("PRAGMA journal_mode=OFF") # Performance
            conn.execute("DROP TABLE IF EXISTS portabilidade_new")
            conn.execute("CREATE TABLE portabilidade_new (telefone TEXT, operadora_id INTEGER)")
            
            batch = []
            count = 0
            with open(extracted_file, 'r') as f:
                for line in f:
                    parts = line.strip().split(',') # Formato esperado: telefone,operadora_id
                    if len(parts) >= 2:
                        batch.append((parts[0], parts[1]))
                        count += 1
                    
                    if len(batch) >= 50000:
                        conn.executemany("INSERT INTO portabilidade_new VALUES (?,?)", batch)
                        batch = []
                        # 60% a 95% é ingestão
                        self._update_task(tid, progress=60 + int((count / 1000000) * 35) % 35, message=f"Importando: {count:,} registros")

            if batch:
                conn.executemany("INSERT INTO portabilidade_new VALUES (?,?)", batch)
            
            self._update_task(tid, progress=95, message="Finalizando transação...")
            conn.execute("DROP TABLE IF EXISTS portabilidade")
            conn.execute("ALTER TABLE portabilidade_new RENAME TO portabilidade")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_tel ON portabilidade (telefone)")
            conn.commit()
            conn.close()
            
            # Limpeza
            if os.path.exists(local_zip): os.remove(local_zip)
            if extracted_file and os.path.exists(extracted_file): os.remove(extracted_file)
            
            self._update_task(tid, progress=100, message="Base atualizada com sucesso!", status="COMPLETED")
            
        except Exception as e:
            print(f"Error in carrier update: {e}")
            self._update_task(tid, status="FAILED", message=f"Erro: {str(e)}")
    def deep_search(self, name=None, cpf=None, cnpj=None, phone=None):
        """Busca rápida unitária no ClickHouse"""
        ch_local = self._get_ch_client()
        if not ch_local:
            return pd.DataFrame()
            
        basics = []
        
        if cpf:
            # Robust cleaning
            cpf_clean = ''.join(filter(str.isdigit, str(cpf)))
            if len(cpf_clean) >= 11:
                cpf_mask = f"***{cpf_clean[3:9]}**"
                res = ch_local.query("SELECT cnpj_basico FROM hemn.socios WHERE cnpj_cpf_socio IN (%(c1)s, %(c2)s) LIMIT 50", 
                                          {'c1': cpf_clean, 'c2': cpf_mask})
                basics.extend([r[0] for r in res.result_rows])
                # Add check for MEIs where Razão Social contains the CPF
                res = ch_local.query("SELECT cnpj_basico FROM hemn.empresas WHERE razao_social LIKE %(c)s LIMIT 50",
                                          {'c': f"%{cpf_clean}%"})
                basics.extend([r[0] for r in res.result_rows])
        
        if cnpj:
            cnpj_clean = ''.join(filter(str.isdigit, str(cnpj)))
            if len(cnpj_clean) >= 8:
                basics.append(cnpj_clean[:8])

        if phone:
            tel_clean = ''.join(filter(str.isdigit, str(phone)))
            if len(tel_clean) >= 10:
                ddd = tel_clean[:2]
                num_8 = tel_clean[-8:]
                nums = [num_8]
                if len(tel_clean) == 11:
                    # Inclui o número completo de 9 dígitos se fornecido
                    nums.append(tel_clean[2:])
                
                res1 = ch_local.query("SELECT cnpj_basico FROM hemn.estabelecimento WHERE ddd1 = %(ddd)s AND telefone1 IN %(nums)s LIMIT 50", 
                                           {'ddd': ddd, 'nums': nums})
                basics.extend([r[0] for r in res1.result_rows])
                
                res2 = ch_local.query("SELECT cnpj_basico FROM hemn.estabelecimento WHERE ddd2 = %(ddd)s AND telefone2 IN %(nums)s LIMIT 50", 
                                           {'ddd': ddd, 'nums': nums})
                basics.extend([r[0] for r in res2.result_rows])

        if name:
            name_clean = remove_accents(str(name).strip().upper())
            # Try both prefix for speed and contains for flexibility
            res = ch_local.query("SELECT cnpj_basico FROM hemn.socios WHERE nome_socio LIKE %(n)s OR nome_socio LIKE %(nc)s LIMIT 50", 
                                      {'n': f'{name_clean}%', 'nc': f'%{name_clean}%'})
            basics.extend([r[0] for r in res.result_rows])
            res = ch_local.query("SELECT cnpj_basico FROM hemn.empresas WHERE razao_social LIKE %(n)s OR razao_social LIKE %(nc)s LIMIT 50", 
                                      {'n': f'{name_clean}%', 'nc': f'%{name_clean}%'})
            basics.extend([r[0] for r in res.result_rows])
            
        if not basics:
            return pd.DataFrame()
            
        basics = list(set(basics))
        # Filtro de impressão digital (Fingerprint): Nome + CPF se fornecidos
        socio_filters = []
        empresa_filters = []
        
        params_socio = []
        params_empresa = []
        
        if cpf:
            cpf_clean = ''.join(filter(str.isdigit, str(cpf)))
            if len(cpf_clean) >= 11:
                cpf_mask = f"***{cpf_clean[3:9]}**"
                socio_filters.append("s.cnpj_cpf_socio IN (%s, %s)")
                params_socio.extend([cpf_clean, cpf_mask])
                
                # Permite que MEIs anonimizados pela RFB (que começam com o próprio CNPJ no nome) passem pelo filtro de CPF restrito, 
                # desde que eles passem pelo filtro do NOME EXATO que adicionamos abaixo.
                empresa_filters.append("(e.razao_social LIKE %s OR (e.natureza_juridica = '2135' AND startsWith(e.razao_social, concat(substring(e.cnpj_basico, 1, 2), '.', substring(e.cnpj_basico, 3, 3), '.', substring(e.cnpj_basico, 6, 3)))))")
                params_empresa.append(f"%{cpf_clean}%")
        
        if name:
            name_norm = normalize_name(name)
            socio_filters.append("(s.nome_socio LIKE %s OR s.nome_socio LIKE %s)")
            params_socio.extend([f"{name_norm}%", f"%{name_norm}%"])
            
            empresa_filters.append("(e.razao_social LIKE %s OR e.razao_social LIKE %s)")
            params_empresa.extend([f"{name_norm}%", f"%{name_norm}%"])
            
        socio_match_sql = " AND ".join(socio_filters) if socio_filters else "1=1"
        company_name_match = " AND ".join(empresa_filters) if empresa_filters else "1=0"
        
        # Combine the params strictly in the order they appear in the query string:
        # WHERE ... IN (basics) AND ( socio_match_sql OR company_name_match )
        params = basics[:] + params_socio + params_empresa

        query = f"""
            SELECT e.razao_social, 
                   concat(est.cnpj_basico, est.cnpj_ordem, est.cnpj_dv) AS cnpj_completo,
                   multiIf(est.situacao_cadastral = '02', 'ATIVA', 'BAIXADA/INATIVA') AS situacao,
                   est.cnae_fiscal AS cnae_principal,
                   multiIf(e.natureza_juridica = '2135', 'SIM', 'NÃO') AS cnpj_cpf_socio,
                   est.correio_eletronico AS email_novo,
                   concat(est.logradouro, ', ', est.numero, ' - ', est.bairro, ' - ', coalesce(m.descricao, 'N/A'), '/', est.uf) AS endereco_completo,
                   multiIf(length(est.telefone1) = 8 AND substring(est.telefone1, 1, 1) IN ('6','7','8','9'), concat('9', est.telefone1), est.telefone1) AS telefone_novo,
                   est.ddd1 AS ddd_novo,
                   multiIf(length(est.telefone1) = 8 AND substring(est.telefone1, 1, 1) IN ('6','7','8','9'), 'CELULAR', 
                           length(est.telefone1) = 9, 'CELULAR', 'FIXO') AS tipo_telefone,
                   coalesce(est.nome_fantasia, e.razao_social) AS nome_fantasia,
                   multiIf(est.data_inicio_atividades != '', 
                           concat(substring(est.data_inicio_atividades, 7, 2), '/', 
                                  substring(est.data_inicio_atividades, 5, 2), '/', 
                                  substring(est.data_inicio_atividades, 1, 4)), 
                           'NÃO INFORMADA') AS data_abertura,
                   coalesce(e.capital_social, 0.0) AS capital_social,
                   multiIf(e.natureza_juridica = '2135', 'EMPRESÁRIO INDIVIDUAL (MEI)', 
                           e.natureza_juridica = '2062', 'SOCIEDADE EMPRESÁRIA LIMITADA',
                           e.natureza_juridica = '2305', 'ENTIDADE SINDICAL',
                           e.natureza_juridica = '3999', 'ASSOCIAÇÃO PRIVADA',
                           concat('CÓDIGO ', e.natureza_juridica)) AS natureza_juridica,
                   multiIf(e.porte_empresa = '01', 'MICRO EMPRESA',
                           e.porte_empresa = '03', 'PEQUENO PORTE',
                           e.porte_empresa = '05', 'DEMAIS (MÉDIA/GRANDE)',
                           'NÃO INFORMADO') AS porte,
                   est.cnae_fiscal_secundaria AS cnae_secundario,
                   arrayStringConcat(groupUniqArray(coalesce(s.nome_socio, 'NÃO ENCONTRADO')), ' / ') AS socio_nome
            FROM hemn.empresas e
            JOIN hemn.estabelecimento est ON e.cnpj_basico = est.cnpj_basico
            LEFT JOIN hemn.socios s ON e.cnpj_basico = s.cnpj_basico
            LEFT JOIN hemn.municipio m ON est.municipio = m.codigo
            WHERE e.cnpj_basico IN ({','.join(['%s' for _ in basics])})
              AND ({socio_match_sql} OR {company_name_match})
            GROUP BY 
                e.razao_social, 
                cnpj_completo,
                situacao,
                cnae_principal,
                cnpj_cpf_socio,
                email_novo,
                endereco_completo,
                telefone_novo,
                ddd_novo,
                tipo_telefone,
                nome_fantasia,
                data_abertura,
                capital_social,
                natureza_juridica,
                porte,
                cnae_secundario
            ORDER BY multiIf(situacao = 'ATIVA', 1, 2)
            LIMIT 50
        """
        res = ch_local.query(query, params)
        return pd.DataFrame(res.result_rows, columns=res.column_names)


    def _run_enrich(self, tid, input_file, output_dir, name_col, cpf_col, perfil="TODOS"):
        try:
            self._update_task(tid, status="PROCESSING", message="[v1.9.1] Iniciando Escaneamento Titanium-MT (Motor Paralelo)...")
            status = self.get_task_status(tid)
            if status.get("status") == "CANCELLED": return
            start_time = time.time()
            output_file = os.path.join(output_dir, f"Enriquecido_{tid[:8]}.xlsx")
            
            # Memory Optimized: Determine row count without loading full file
            if input_file.endswith('.csv'):
                total_rows = sum(1 for _ in open(input_file, 'r', encoding='utf-8', errors='ignore')) - 1
            else:
                # Use openpyxl to get dimensions without loading data
                import openpyxl
                wb = openpyxl.load_workbook(input_file, read_only=True)
                total_rows = wb.active.max_row - 1
                wb.close()
            
            self._update_task(tid, progress=2, message=f"Lendo base ({total_rows:,} registros)...")

            # Memory Optimized: Multi-stage processing
            all_cpfs = []
            all_names = []
            
            if input_file.endswith('.csv'):
                # Chunked reading to save RAM
                for chunk in pd.read_csv(input_file, sep=None, engine='python', chunksize=10000):
                    status = self.get_task_status(tid)
                    if status.get("status") == "CANCELLED": return
                    
                    # Process chunk...
                    # (For simplicity in this diff, I'll load the keys only)
                    if cpf_col in chunk.columns:
                        all_cpfs.extend(chunk[cpf_col].fillna('').astype(str).str.replace(r'\D', '', regex=True).str.zfill(11).tolist())
                    else:
                        # Fallback if cpf_col not found, use first column
                        all_cpfs.extend(chunk.iloc[:, 0].fillna('').astype(str).str.replace(r'\D', '', regex=True).str.zfill(11).tolist())

                    if name_col in chunk.columns:
                        all_names.extend(chunk[name_col].fillna('').astype(str).str.upper().str.strip().apply(remove_accents).tolist())
                    elif len(chunk.columns) > 1:
                        # Fallback if name_col not found, use second column
                        all_names.extend(chunk.iloc[:, 1].fillna('').astype(str).str.upper().str.strip().apply(remove_accents).tolist())
                    else:
                        # If only one column, use it for both if name_col not found
                        all_names.extend(chunk.iloc[:, 0].fillna('').astype(str).str.upper().str.strip().apply(remove_accents).tolist())
                    
                    del chunk
                
                # Reconstruct df_in from collected data
                df_in = pd.DataFrame({'original_cpf': all_cpfs, 'original_name': all_names})
                # Assuming original input file columns are needed for final output,
                # a full load might be necessary or a more complex merge strategy.
                # For now, let's assume we need to load the full df_in for the final merge.
                # This part needs careful consideration based on actual memory constraints and requirements.
                # For this diff, I'll re-load df_in fully for the merge phase,
                # but the initial CPF/Name extraction is chunked.
                if input_file.endswith('.csv'):
                    with open(input_file, 'r', encoding='utf-8', errors='ignore') as f:
                        primeira = f.readline()
                    sep = ';' if ';' in primeira else (',' if ',' in primeira else '\t')
                    df_in = pd.read_csv(input_file, sep=sep, engine='python', dtype=str)
                else:
                    df_in = pd.read_excel(input_file, dtype=str)

            else: # Excel file
                df_in = pd.read_excel(input_file, dtype=str)
                # Fallback indices if columns are None or not found
                c_idx = cpf_col if (cpf_col and cpf_col in df_in.columns) else df_in.columns[0]
                n_idx = name_col if (name_col and name_col in df_in.columns) else (df_in.columns[1] if len(df_in.columns) > 1 else df_in.columns[0])
                
                all_cpfs = df_in[c_idx].fillna('').astype(str).str.replace(r'\D', '', regex=True).str.zfill(11).tolist()
                all_names = df_in[n_idx].fillna('').astype(str).str.upper().str.strip().apply(remove_accents).tolist()

            total = len(df_in) # Recalculate total based on actual df_in if it was reloaded
            
            # --- PHASE 0: NORMALIZAÇÃO ---
            # These columns are now created based on the full df_in after loading
            if name_col in df_in.columns: n_col = name_col
            else: n_col = df_in.columns[1] if len(df_in.columns) > 1 else df_in.columns[0]
            if cpf_col in df_in.columns: c_col = cpf_col
            else: c_col = df_in.columns[0]
            
            df_in['titanium_nome'] = df_in[n_col].fillna('').astype(str).str.upper().str.strip().apply(remove_accents)
            df_in['titanium_cpf'] = df_in[c_col].fillna('').astype(str).str.replace(r'\D', '', regex=True).str.zfill(11)

            # --- EXTRAÇÃO DE UF (DETERMINAÇÃO DA COLUNA) ---
            # Prioridade: Coluna nomeada 'UF' ou 'Estado' -> Coluna C (Index 2)
            uf_col = next((c for c in df_in.columns if str(c).upper() in ['UF', 'ESTADO', 'UF_CLIENTE']), None)
            if not uf_col and len(df_in.columns) > 2:
                uf_col = df_in.columns[2]
            
            if uf_col:
                df_in['titanium_uf'] = df_in[uf_col].fillna('').astype(str).str.upper().str.strip().str[:2]
            else:
                df_in['titanium_uf'] = ''
            
            # Mapa de UF para conferência rápida
            client_uf_map = {}
            for _, row in df_in.iterrows():
                u = str(row.get('titanium_uf', '')).strip()
                c = str(row.get('titanium_cpf', '')).strip()
                n = str(row.get('titanium_nome', '')).strip()
                sc = f"{n} ***{c[3:9]}**" if len(c) >= 11 else ""
                if c: client_uf_map[c] = u
                if n: client_uf_map[n] = u
                if sc: client_uf_map[sc] = u

            # --- PHASE 1: BATCH PROCESSING (EXTREME SPEED) ---
            # Generar chaves combinadas (socio_chave) para busca ultra precisa
            # Otimização v1.8.11: Vetorização de Chaves (Elimina iterrows/CPU spike)
            mask_chave = (df_in['titanium_nome'] != '') & (df_in['titanium_cpf'].str.len() >= 11)
            if mask_chave.any():
                df_masked = df_in[mask_chave]
                search_chaves = (df_masked['titanium_nome'] + " ***" + df_masked['titanium_cpf'].str[3:9] + "**").unique().tolist()
            else:
                search_chaves = []

            # Mantemos CPF e Nome isolados apenas para fallbacks (se faltar um deles)
            valid_cpfs = [cpf for cpf in all_cpfs if len(cpf) >= 11]
            search_cpfs = list(set(valid_cpfs))
            
            valid_names = [normalize_name(n) for n in all_names if len(str(n)) > 3]
            search_names = list(set(valid_names))
            
            # Prepare Global Results
            all_results = []
            found_count = 0
            
            # --- PHASE 1: TITANIUM-TURBO DATA GATHERING ---
            # 1. Perfil Configuration
            p_val = str(perfil).upper().strip()
            if p_val == "MEI":
                perfil_cond_sql = "e.natureza_juridica = '2135'"
                is_expansion_required = False
            elif p_val == "NAO MEI":
                perfil_cond_sql = "e.natureza_juridica != '2135'"
                is_expansion_required = True
            else:
                perfil_cond_sql = "1=1"
                is_expansion_required = True

            # 2. Buscar dados em SÓCIOS
            if search_chaves or search_cpfs or search_names:
                self._update_task(tid, progress=10, message="Buscando Sócios...")
                
                # Queries para Sócios
                q_socios_base = f"""
                    SELECT cnpj_basico, nome_socio, socio_chave, {{lookup_col}} AS lookup_key 
                    FROM hemn.socios 
                    WHERE {{lookup_col}} IN %(keys)s
                    {"LIMIT 1 BY socio_chave" if not is_expansion_required else ""}
                """
                
                results_s = []
                cols_s = []
                # Prioridade 1: Chave Combinada (Socio Chave) - Muito mais precisa
                if search_chaves:
                    r, c = self._batch_query(q_socios_base.format(lookup_col="socio_chave"), "keys", search_chaves, tid=tid, base_prog=10, max_prog=20)
                    results_s += r
                    if c: cols_s = c
                
                # Prioridade 2: CPF (Apenas CPFs reais, sem máscaras isoladas para evitar poluição)
                if search_cpfs:
                    r, c = self._batch_query(q_socios_base.format(lookup_col="cnpj_cpf_socio"), "keys", search_cpfs, tid=tid, base_prog=20, max_prog=30)
                    results_s += r
                    if c: cols_s = c
                
                # Prioridade 3: Nome (Se ainda não encontrou nada)
                if search_names:
                    r, c = self._batch_query(q_socios_base.format(lookup_col="nome_socio"), "keys", search_names, tid=tid, base_prog=30, max_prog=40)
                    results_s += r
                    if c: cols_s = c
                
                if results_s:
                    df_socios = pd.DataFrame(results_s, columns=cols_s)
                    
                    # 3. Buscar dados de EMPRESAS e ESTABELECIMENTOS para os CNPJs encontrados
                    unique_cnpjs = df_socios['cnpj_basico'].unique().tolist()
                    self._update_task(tid, progress=45, message=f"Buscando Dados de {len(unique_cnpjs):,} Empresas...")
                    
                    # Otimização v1.9.2: Filtro Geográfico na Query (Somente UFs presentes na planilha)
                    unique_ufs = [u for u in df_in['titanium_uf'].unique().tolist() if u and len(u) == 2]
                    uf_filter_sql = " AND estab.uf IN %(ufs)s" if unique_ufs else ""
                    
                    q_info = f"""
                        SELECT 
                            e.cnpj_basico AS cnpj_basico, e.razao_social AS razao_social,
                            estab.cnpj_ordem, estab.cnpj_dv, estab.situacao_cadastral, estab.uf,
                            estab.ddd1, estab.telefone1, estab.ddd2, estab.telefone2, estab.correio_eletronico,
                            estab.tipo_logradouro, estab.logradouro, estab.numero, estab.complemento,
                            estab.bairro, estab.cep, estab.cnae_fiscal, estab.municipio,
                            mun.descricao AS municipio_nome
                        FROM hemn.empresas AS e
                        INNER JOIN hemn.estabelecimento AS estab ON e.cnpj_basico = estab.cnpj_basico
                        LEFT JOIN hemn.municipio AS mun ON estab.municipio = mun.codigo
                        WHERE e.cnpj_basico IN %(keys)s AND {perfil_cond_sql} AND estab.situacao_cadastral = '02' {uf_filter_sql}
                        ORDER BY (estab.cnpj_ordem = '0001') DESC
                        LIMIT 1 BY e.cnpj_basico
                    """
                    
                    params_info = {}
                    if unique_ufs: params_info["ufs"] = unique_ufs
                    results_info, cols_info = self._batch_query(q_info, "keys", unique_cnpjs, tid=tid, base_prog=45, max_prog=75, extra_params=params_info)
                    
                    if results_info:
                        df_info = pd.DataFrame(results_info, columns=cols_info)
                        
                        # 4. Join Final (Socio + Info)
                        df_final_lookup = pd.merge(df_socios, df_info, on='cnpj_basico', how='inner')
                        
                        # Pack into all_results
                        # Pack into all_results (Otimização v1.8.12: to_dict em vez de iterrows)
                        for d in df_final_lookup.to_dict('records'):
                            addr = self._parse_address_columns(d)
                            cont = self._parse_contact_columns(d)
                            mapping = {'01': 'NULA', '02': 'ATIVA', '03': 'SUSPENSA', '04': 'INAPTA', '08': 'BAIXADA'}
                            # Verificação Geográfica de Segurança (Garante que a UF bate com a solicitada para esse registro)
                            l_key = str(d['lookup_key'])
                            target_uf = client_uf_map.get(l_key, '')
                            if target_uf and target_uf != str(d['uf']):
                                continue

                            mapping = {'01': 'NULA', '02': 'ATIVA', '03': 'SUSPENSA', '04': 'INAPTA', '08': 'BAIXADA'}
                            all_results.append({
                                'lookup_key': l_key,
                                'CNPJ': f"{str(int(d['cnpj_basico'])).zfill(8)}{str(int(d['cnpj_ordem'])).zfill(4)}{str(int(d['cnpj_dv'])).zfill(2)}",
                                'RAZAO_SOCIAL': d['razao_social'], 
                                'SITUACAO': mapping.get(str(d['situacao_cadastral']).zfill(2), 'ATIVA'),
                                'CNAE': d['cnae_fiscal'], 'LOGRADOURO': str(addr[0]).upper(), 'NÚMERO': addr[1], 'COMPLEMENTO': addr[2],
                                'BAIRRO': addr[3], 'CIDADE': str(addr[4]).upper(), 'UF_END': addr[5], 'CEP': addr[6],
                                'TELEFONE': cont[0], 'TIPO': cont[1], 'EMAIL': cont[2],
                                'CHAVE_SOCIO': d.get('socio_chave', '')
                            })

                    # Motor One-Shot v5.1.4: Busca Híbrida Inteligente (CPF Flash-IN + Nome Aho-Scan)
                    def run_mei_scan(search_cpfs, search_names, tid, base_p, max_p, ufs=None):
                        results = []
                        ch_local = self._get_ch_client()
                        if not ch_local: return []

                        uf_filter = " AND uf IN %(ufs)s" if ufs else ""
                        params = {}
                        if ufs: params['ufs'] = ufs

                        # 1. BUSCA POR CPF (Modo Flash: IN Operator) - Resolve 99% dos casos em 1 seg
                        if search_cpfs:
                            cpfs = list(set([str(c).strip() for c in search_cpfs if len(str(c)) >= 11]))
                            if cpfs:
                                cpf_batch = 10000
                                for idx in range(0, len(cpfs), cpf_batch):
                                    block = cpfs[idx:idx + cpf_batch]
                                    self._update_task(tid, progress=base_p + 1, message=f"MEI CPF Flash: {idx:,}/{len(cpfs):,}...")
                                    # Otimização Crítica: substring(-11) extrai o CPF do final da Razão Social do MEI
                                    # Fix v1.9.2: Join com estabelecimento para filtrar UF (já que UF não existe em empresas)
                                    if ufs:
                                        sql_cpf = f"""
                                            SELECT e.cnpj_basico, e.razao_social 
                                            FROM hemn.empresas AS e
                                            INNER JOIN hemn.estabelecimento AS estab ON e.cnpj_basico = estab.cnpj_basico
                                            PREWHERE e.natureza_juridica = '2135'
                                            WHERE substring(e.razao_social, -11) IN %(cpfs)s AND estab.uf IN %(ufs)s
                                        """
                                    else:
                                        sql_cpf = "SELECT cnpj_basico, razao_social FROM hemn.empresas PREWHERE natureza_juridica = '2135' WHERE substring(razao_social, -11) IN %(cpfs)s"
                                    
                                    p = params.copy()
                                    p['cpfs'] = block
                                    print(f"[DEBUG] [MEI-CPF] Query: {sql_cpf}")
                                    print(f"[DEBUG] [MEI-CPF] Params Keys: {list(p.keys())}")
                                    try:
                                        res_cpf = ch_local.query(sql_cpf, p)
                                        results.extend(res_cpf.result_rows)
                                    except Exception as e:
                                        print(f"[ERROR] [MEI-CPF] ClickHouse Error: {e}")
                                        raise

                        # 2. BUSCA POR NOME (Rede de Segurança Total) - Varre tudo que não tiver CPF ou se falhou
                        if search_names:
                            names = list(set([str(n).upper().strip() for n in search_names if len(str(n)) > 5]))
                            total_names = len(names)
                            # Para evitar travamento, lotes cirúrgicos de 250 nomes.
                            batch_size = 500
                            for i in range(0, total_names, batch_size):
                                block = names[i:min(i + batch_size, total_names)]
                                self._update_task(tid, progress=base_p + 5 + int((i/total_names)*5), message=f"MEI Name Scan: {i:,}/{total_names:,}...")
                                # Fix v1.9.2: Join com estabelecimento para filtrar UF
                                if ufs:
                                    sql_name = f"""
                                        SELECT e.cnpj_basico, e.razao_social 
                                        FROM hemn.empresas AS e
                                        INNER JOIN hemn.estabelecimento AS estab ON e.cnpj_basico = estab.cnpj_basico
                                        PREWHERE e.natureza_juridica = '2135'
                                        WHERE multiSearchAny(e.razao_social, %(n)s) AND estab.uf IN %(ufs)s
                                    """
                                else:
                                    sql_name = f"SELECT cnpj_basico, razao_social FROM hemn.empresas PREWHERE natureza_juridica = '2135' WHERE multiSearchAny(razao_social, %(n)s)"
                                
                                p = params.copy()
                                p['n'] = block
                                print(f"[DEBUG] [MEI-NAME] Query: {sql_name}")
                                print(f"[DEBUG] [MEI-NAME] Params Keys: {list(p.keys())}")
                                try:
                                    res_name = ch_local.query(sql_name, p)
                                    results.extend(res_name.result_rows)
                                except Exception as e:
                                    print(f"[ERROR] [MEI-NAME] ClickHouse Error: {e}")
                                    raise
                        
                        return results

                    # Otimização v1.8.9: Recalcula listas para Phase 2 MEI
                    # Se tem CPF, ignoramos o NOME (Pois o CPF já existe na razão social do MEI e é 100x mais rápido)
                    # Otimização v1.8.11: Vetorização de Listas MEI
                    has_cpf = df_in['titanium_cpf'].str.len() >= 11
                    search_cpfs_mei = set(df_in.loc[has_cpf, 'titanium_cpf'].tolist())
                    
                    # Nomes apenas para quem não tem CPF válido
                    search_names_mei = set(df_in.loc[~has_cpf & (df_in['titanium_nome'].str.len() > 5), 'titanium_nome'].tolist())

                    # Sincronização v1.8.10: Só executa MEI Scan se perfil for TODOS ou MEI
                    if p_val in ["TODOS", "MEI"] and (search_cpfs_mei or search_names_mei):
                        found_meis = run_mei_scan(list(search_cpfs_mei), list(search_names_mei), tid, 40, 55, ufs=unique_ufs)
                    else:
                        found_meis = []

                    # 2. Busca de Detalhes (Apenas para os encontrados)
                    if found_meis:
                        found_cnpjs = list(set([str(r[0]) for r in found_meis]))
                        self._update_task(tid, progress=55, message=f"Buscando detalhes de {len(found_cnpjs)} MEIs...")
                        
                        ch_local = self._get_ch_client()
                        all_mei_results = []
                        cols_mei = []
                        
                        # Otimização v5.1.2: Lotes de 5.000 para evitar 'Max query size exceeded'
                        cnpj_batch = 10000
                        for idx in range(0, len(found_cnpjs), cnpj_batch):
                            block = found_cnpjs[idx:idx + cnpj_batch]
                            sql_details = """
                            SELECT 
                                e.cnpj_basico AS cnpj_basico, e.razao_social AS razao_social,
                                estab.cnpj_ordem AS cnpj_ordem, estab.cnpj_dv AS cnpj_dv, 
                                estab.situacao_cadastral AS situacao_cadastral, estab.uf AS uf,
                                estab.ddd1 AS ddd1, estab.telefone1 AS telefone1, 
                                estab.ddd2 AS ddd2, estab.telefone2 AS telefone2, 
                                estab.correio_eletronico AS correio_eletronico,
                                estab.logradouro AS logradouro, estab.numero AS numero, 
                                estab.complemento AS complementos, estab.bairro AS bairro, 
                                estab.cep AS cep, estab.cnae_fiscal AS cnae_fiscal, 
                                mun.descricao AS municipio_nome
                            FROM hemn.estabelecimento AS estab
                            INNER JOIN hemn.empresas AS e ON estab.cnpj_basico = e.cnpj_basico
                            LEFT JOIN hemn.municipio AS mun ON estab.municipio = mun.codigo
                            WHERE e.cnpj_basico IN %(cnpjs)s AND estab.situacao_cadastral = '02'
                            """
                            # Log detalhado v5.1.5: Captura possível ambiguidade de UF
                            # print(f"[DEBUG] [MEI-DETAILS] Batch {idx}: {len(block)} CNPJs")
                            try:
                                res_details = ch_local.query(sql_details, {'cnpjs': block})
                                all_mei_results.extend(res_details.result_rows)
                                if not cols_mei: cols_mei = res_details.column_names
                            except Exception as e:
                                print(f"[ERROR] [MEI-DETAILS] ClickHouse Error: {e}")
                                raise

                        # 3. Filtragem Geográfica Final (Precisão v1.8.6)
                        # Identifica coluna de UF para isolamento regional
                        uf_col = next((c for c in df_in.columns if c.upper() in ['UF', 'ESTADO', 'UF_CLIENTE']), None)
                        if uf_col:
                            # Criar mapa CPF -> UF do Cliente para filtragem cirúrgica
                            client_uf_map = {}
                            for _, row in df_in.iterrows():
                                c = str(row.get('titanium_cpf', '')).strip()
                                n = str(row.get('titanium_nome', '')).upper().strip()
                                u = str(row[uf_col]).upper().strip() if pd.notna(row[uf_col]) else ""
                                if c: client_uf_map[c] = u
                                if n: client_uf_map[n] = u

                            final_filtered = []
                            for d in all_mei_results:
                                r_social = str(d[1])
                                r_uf = str(d[5])
                                # O MEI deve bater na UF do cliente que originou a busca
                                # Checamos se o CPF ou Nome do MEI e a UF batem com o cliente
                                is_match = False
                                for pattern, uf in client_uf_map.items():
                                    if pattern in r_social and uf == r_uf:
                                        is_match = True
                                        break
                                if is_match: final_filtered.append(d)
                            all_mei_results = final_filtered

                    if all_mei_results:
                        df_mei = pd.DataFrame(all_mei_results, columns=cols_mei).drop_duplicates(subset=['cnpj_basico'])
                        
                        # OTIMIZAÇÃO CRÍTICA: Criar mapas para lookup O(1) em vez de loop O(N^2)
                        # Sincronizado com v1.8.10 (search_cpfs_mei / search_names_mei)
                        cpf_lookup = {str(c).strip(): c for c in search_cpfs_mei}
                        mask_lookup = {f"***{str(c)[3:9]}**": c for c in search_cpfs_mei if len(str(c)) >= 9}
                        name_lookup = {str(n).upper().strip(): n for n in search_names_mei}

                        # OTIMIZAÇÃO v1.8.12: RegEx para busca O(N) em vez de O(N*M)
                        import re
                        name_pattern = re.compile('|'.join([re.escape(n) for n in name_lookup.keys() if len(n) > 5])) if name_lookup else None
                        
                        for d in df_mei.to_dict('records'):
                            addr = self._parse_address_columns(d)
                            cont = self._parse_contact_columns(d)
                            mapping = {'01': 'NULA', '02': 'ATIVA', '03': 'SUSPENSA', '04': 'INAPTA', '08': 'BAIXADA'}
                            
                            r_social = str(d['razao_social']).upper()
                            matched_key = None
                            
                            # 1. Tentar extrair o CPF/Mascara do final da Razão Social (Padrão MEI 2135)
                            parts = r_social.split()
                            if parts:
                                last_p = parts[-1].replace('.', '').replace('-', '')
                                if last_p in cpf_lookup:
                                    matched_key = cpf_lookup[last_p]
                                elif last_p in mask_lookup:
                                    matched_key = mask_lookup[last_p]
                            
                            # 2. Fallback: Busca por Nome via RegEx (Otimização Ultra v1.8.12)
                            if not matched_key and name_pattern:
                                match = name_pattern.search(r_social)
                                if match:
                                    matched_key = name_lookup.get(match.group())
                            
                            if matched_key:
                                all_results.append({
                                    'lookup_key': matched_key,
                                    'CNPJ': f"{str(int(d['cnpj_basico'])).zfill(8)}{str(int(d['cnpj_ordem'])).zfill(4)}{str(int(d['cnpj_dv'])).zfill(2)}",
                                    'RAZAO_SOCIAL': d['razao_social'], 
                                    'SITUACAO': mapping.get(str(d['situacao_cadastral']).zfill(2), 'ATIVA'),
                                    'CNAE': d['cnae_fiscal'], 'LOGRADOURO': str(addr[0]).upper(), 'NÚMERO': addr[1], 'COMPLEMENTO': addr[2],
                                    'BAIRRO': addr[3], 'CIDADE': str(addr[4]).upper(), 'UF_END': addr[5], 'CEP': addr[6],
                                    'TELEFONE': cont[0], 'TIPO': cont[1], 'EMAIL': cont[2],
                                    'CHAVE_SOCIO': 'MEI (BUSCA DIRETA)'
                                })

            # --- PHASE 2: IN-MEMORY MAPPING & FALLBACKS ---
            self._update_task(tid, progress=80, message="Consolidando base de dados...")
            
            if all_results:
                df_cache = pd.DataFrame(all_results)
                
                # Preparar colunas de lookup no DataFrame original
                df_in['socio_chave_lookup'] = df_in.apply(lambda r: f"{str(r['titanium_nome']).strip()} ***{str(r['titanium_cpf'])[3:9]}**" if len(str(r['titanium_cpf'])) >= 11 else "", axis=1)
                
                # Detectar coluna de UF no input para regra de desempate
                uf_input_col = next((c for c in df_in.columns if c.upper() in ['UF', 'ESTADO', 'UF_CLIENTE']), None)
                if uf_input_col:
                    df_in[uf_input_col] = df_in[uf_input_col].astype(str).str.strip().str.upper()

                # Merge 1: Chave Combinada (Socio Chave) - PRIORIDADE MÁXIMA
                df_in['lookup_key'] = df_in['socio_chave_lookup']
                df_merged = pd.merge(df_in, df_cache, on='lookup_key', how='left')
                
                # Merge 2: CPF Exato (Fallback se não houver nome ou se houver erro na chave)
                null_rows = df_merged['CNPJ'].isna()
                if null_rows.any():
                    df_no_match_cpf = df_in[null_rows].copy()
                    df_no_match_cpf['lookup_key'] = df_no_match_cpf['titanium_cpf']
                    df_merged_cpf = pd.merge(df_no_match_cpf.drop(columns=df_cache.columns.drop('lookup_key'), errors='ignore'), df_cache, on='lookup_key', how='left')
                    df_merged = pd.concat([df_merged[~null_rows], df_merged_cpf], ignore_index=True)

                # Merge 3: Nomes (apenas onde ainda não houve match)
                null_rows = df_merged['CNPJ'].isna()
                if null_rows.any() and not df_cache.empty:
                    # Normalizar chaves no cache para comparação de nomes
                    df_cache['titanium_nome'] = df_cache['lookup_key'].apply(normalize_name)
                    df_cache_names = df_cache.drop_duplicates(subset=['titanium_nome', 'CNPJ'])
                    
                    df_no_match = df_merged[null_rows].drop(columns=df_cache.columns.drop('titanium_nome', errors='ignore'), errors='ignore').copy()
                    df_no_match['titanium_nome'] = df_no_match['titanium_nome'].apply(normalize_name)
                    df_merged_names = pd.merge(df_no_match, df_cache_names, on='titanium_nome', how='left')
                    
                    df_merged = pd.concat([df_merged[~null_rows], df_merged_names], ignore_index=True)

                # Merge 4: MEI Fallback (onde lookup_key era o Nome diretamente da busca de empresas)
                null_rows = df_merged['CNPJ'].isna()
                if null_rows.any() and not df_cache.empty:
                    df_no_match_mei = df_merged[null_rows].copy()
                    
                    # Tentar merge por CPF bruto (O(1) no lookup do cache)
                    df_no_match_mei['lookup_key'] = df_no_match_mei['titanium_cpf']
                    df_merged_mei_cpf = pd.merge(df_no_match_mei.drop(columns=df_cache.columns.drop('lookup_key'), errors='ignore'), df_cache, on='lookup_key', how='left')
                    
                    # Onde ainda sobrar nulo, tentar por Nome bruto
                    null_still = df_merged_mei_cpf['CNPJ'].isna()
                    if null_still.any():
                        df_no_match_name = df_merged_mei_cpf[null_still].copy()
                        df_no_match_name['lookup_key'] = df_no_match_name['titanium_nome']
                        df_merged_mei_name = pd.merge(df_no_match_name.drop(columns=df_cache.columns.drop('lookup_key'), errors='ignore'), df_cache, on='lookup_key', how='left')
                        df_merged_mei_cpf = pd.concat([df_merged_mei_cpf[~null_still], df_merged_mei_name], ignore_index=True)
                    
                    df_merged = pd.concat([df_merged[~null_rows], df_merged_mei_cpf], ignore_index=True)

                # --- LÓGICA DE FILTRO INTELIGENTE POR UF (REGRA DO CLIENTE) ---
                if uf_input_col and not df_merged.empty and 'CNPJ' in df_merged.columns:
                    # 1. Contar ocorrências globais por chave no cache (Unicidade Nacional)
                    counts = df_cache['lookup_key'].value_counts().rename('total_brazil')
                    df_merged = df_merged.merge(counts, on='lookup_key', how='left')
                    
                    # 2. Aplicar Regras de Descarte
                    # Regra 1: Se total_brazil == 1 (MANTÉM SEMPRE)
                    # Regra 2: Se total_brazil > 1 E UF_END == UF_INPUT (MANTÉM)
                    # Regra 3: Se total_brazil > 1 E UF_END != UF_INPUT (DESCARTA)
                    mask_discard = (df_merged['total_brazil'] > 1) & (df_merged['UF_END'] != df_merged[uf_input_col]) & df_merged['CNPJ'].notna()
                    
                    # Remover linhas descartadas
                    df_merged = df_merged[~mask_discard].copy()
                    df_merged = df_merged.drop(columns=['total_brazil'], errors='ignore')
                        
                # 3. Remover registros que não foram encontrados (limpar linhas vazias no retorno)
                df_merged = df_merged.dropna(subset=['CNPJ'])
                found_count = len(df_merged)
                df_final = df_merged.drop(columns=['titanium_cpf', 'titanium_nome', 'socio_chave_lookup', 'lookup_key'], errors='ignore')
                
                # Reordenar colunas e renomear chave
                cols = list(df_final.columns)
                if 'CHAVE_SOCIO' in cols:
                    cols.insert(0, cols.pop(cols.index('CHAVE_SOCIO')))
                    df_final = df_final[cols]
                
                df_final = df_final.rename(columns={'CHAVE_SOCIO': 'CHAVE DO SOCIO'})
            else:
                found_count = 0
                df_final = df_in.drop(columns=['titanium_cpf', 'titanium_nome'], errors='ignore')

            # Salvar no Excel de forma ultra rapida
            status = self.get_task_status(tid)
            if status.get("status") == "CANCELLED": return
            self._update_task(tid, progress=95, message="Salvando arquivo .xlsx resultante...")
            df_final.to_excel(output_file, index=False)
            total_time = time.time() - start_time
            
            # Converter numpy.int64 para int python nativo para evitar erro 500 no FastAPI
            fc_native = int(found_count)
            total_native = int(total)
            
            msg = f"TITANIUM-DONE: V2.0 Processou {total_native} linhas. {fc_native} encontrados em {total_time:.1f}s."
            self._update_task(tid, status="COMPLETED", progress=100, message=msg, result_file=output_file, record_count=fc_native)

        except Exception as e:
            import traceback
            err_msg = f"{str(e)} | {traceback.format_exc()[-200:]}"
            self._update_task(tid, status="FAILED", message=f"TITANIUM-ERROR: {err_msg}")

    # --- EXTRACTION (FULL FILTERS) ---
    def start_extraction(self, filters, output_dir, username=None):
        summary_parts = []
        if filters.get('uf'): summary_parts.append(f"UF: {filters['uf']}")
        if filters.get('cidade'): summary_parts.append(f"Cidade: {filters['cidade']}")
        if filters.get('cnae'): summary_parts.append(f"CNAE: {filters['cnae']}")
        if filters.get('situacao'): 
            sit_map = {"02": "Ativas", "04": "Baixadas", "08": "Suspensas"}
            summary_parts.append(f"Status: {sit_map.get(filters['situacao'], filters['situacao'])}")
        
        f_summary = " | ".join(summary_parts) if summary_parts else "Extração Completa"
        
        tid = self._create_task(module="EXTRACTION", username=username, filters=f_summary)
        threading.Thread(target=self._run_extraction, args=(tid, filters, output_dir), daemon=True).start()
        return tid

    def _run_extraction(self, tid, filters, output_dir):
        print(f"[DEBUG] Starting _run_extraction for tid: {tid}")
        try:
            self._update_task(tid, status="PROCESSING", progress=1, message="Iniciando motores ClickHouse...")
            print(f"[DEBUG] [_run_extraction] Task {tid} set to PROCESSING")
            status = self.get_task_status(tid)
            if status.get("status") == "CANCELLED":
                print(f"[DEBUG] [_run_extraction] Task {tid} was CANCELLED before start")
                return
            output_file = os.path.join(output_dir, f"Extracao_{tid[:8]}.xlsx")
            
            estab_conds = []
            empresas_conds = []
            params = {}
            
            sit = filters.get("situacao", "02")
            if sit != "TODOS":
                estab_conds.append("estab_inner.situacao_cadastral = %(sit)s")
                params['sit'] = sit

            if filters.get("uf"): 
                estab_conds.append("estab_inner.uf = %(uf)s")
                params['uf'] = filters["uf"].strip().upper()
            
            if filters.get("cidade"): 
                estab_conds.append("m.descricao LIKE %(cid)s")
                params['cid'] = f"%{filters['cidade'].strip().upper()}%"
            
            if filters.get("cnae"): 
                cnaes = [c.strip() for c in filters["cnae"].split(',')]
                estab_conds.append("estab_inner.cnae_fiscal IN %(cnaes)s")
                params['cnaes'] = cnaes

            # Filtro de Perfil (MEI / NAO MEI) - APLICADO NA TABELA EMPRESAS
            perfil = str(filters.get("perfil", "TODOS")).upper().strip()
            print(f"[DEBUG] PERFIL FILTRO: {perfil}")
            if perfil == "MEI":
                empresas_conds.append("natureza_juridica = '2135'")
            elif perfil == "NAO MEI":
                empresas_conds.append("natureza_juridica != '2135'")

            # Filtro de Órgãos Governamentais
            if filters.get("sem_governo"):
                gov_keywords = [
                    "FEDERAL", "GOVERNO", "PUBLICO", "PUBLICA", "ESTADUAL", "ESTADO", 
                    "MUNICIPIO", "MUNICIPAL", "POLICIA", "BOMBEIRO", "BANCO DO BRASIL", "CORREIOS", 
                    "MINISTERIO", "ADVOCACIA-GERAL", "BANCO CENTRAL", "CASA CIVIL", "CONTROLADORIA-GERAL",
                    "GABINETE DE SEGURANCA", "SECRETARIA"
                ]
                # Filter in companies table (natureza_juridica check is also good, but name is what user asked)
                # Grouping keywords to avoid huge query, using multiSearchAny for performance
                empresas_conds.append("NOT multiSearchAnyCaseInsensitive(razao_social, %(gov_keys)s)")
                params['gov_keys'] = gov_keywords

            print(f"[DEBUG] [_run_extraction] filters built: estab_conds={len(estab_conds)}, empresas_conds={len(empresas_conds)}")

            tipo_req = filters.get("tipo_tel", "TODOS")
            if tipo_req == "CELULAR":
                estab_conds.append("((length(estab_inner.telefone1) >= 8 AND substring(estab_inner.telefone1, 1, 1) IN ('6','7','8','9')) OR (length(estab_inner.telefone2) >= 8 AND substring(estab_inner.telefone2, 1, 1) IN ('6','7','8','9')))")
            elif tipo_req == "FIXO":
                estab_conds.append("((length(estab_inner.telefone1) >= 8 AND substring(estab_inner.telefone1, 1, 1) IN ('2','3','4','5')) OR (length(estab_inner.telefone2) >= 8 AND substring(estab_inner.telefone2, 1, 1) IN ('2','3','4','5')))")
            elif tipo_req == "AMBOS":
                estab_conds.append("((length(estab_inner.telefone1) >= 8 AND substring(estab_inner.telefone1, 1, 1) IN ('6','7','8','9') AND length(estab_inner.telefone2) >= 8 AND substring(estab_inner.telefone2, 1, 1) IN ('2','3','4','5')) OR (length(estab_inner.telefone1) >= 8 AND substring(estab_inner.telefone1, 1, 1) IN ('2','3','4','5') AND length(estab_inner.telefone2) >= 8 AND substring(estab_inner.telefone2, 1, 1) IN ('6','7','8','9')))")
            elif filters.get("somente_com_telefone"):
                estab_conds.append("(estab_inner.telefone1 != '' OR estab_inner.telefone2 != '')")

            cep_file = filters.get("cep_file")
            cep_df = None
            cep_col, num_col = None, None
            if cep_file and os.path.exists(cep_file):
                self._update_task(tid, progress=2, message="Lendo planilha de filtro de CEPs...")
                try:
                    if cep_file.lower().endswith('.csv'):
                        try:
                            # Tenta com utf-8-sig para ignorar BOM
                            cep_df = pd.read_csv(cep_file, sep=';', dtype=str, on_bad_lines='skip', encoding='utf-8-sig')
                            if len(cep_df.columns) <= 1:
                                cep_df = pd.read_csv(cep_file, sep=',', dtype=str, on_bad_lines='skip', encoding='utf-8-sig')
                        except Exception:
                            cep_df = pd.read_csv(cep_file, sep=None, engine='python', dtype=str, on_bad_lines='skip', encoding='utf-8-sig')
                    else:
                        cep_df = pd.read_excel(cep_file, dtype=str)
                        
                    print(f"[DEBUG] [_run_extraction] CEP file loaded. Columns: {list(cep_df.columns)}")
                    
                    cep_col = next((c for c in cep_df.columns if "CEP" in str(c).upper()), None)
                    num_col = next((c for c in cep_df.columns if "NUMERO" in str(c).upper().replace('Ú', 'U')), None)
                    print(f"[DEBUG] [_run_extraction] Detected: cep_col='{cep_col}', num_col='{num_col}'")
                    
                    if cep_col:
                        local_df = cep_df.dropna(subset=[cep_col]).copy()
                        series_cep = local_df[cep_col].astype(str).str.replace(r'\D', '', regex=True)
                        series_cep = series_cep[series_cep != '']
                        series_cep = series_cep.str.zfill(8)
                        valid_ceps = [c for c in series_cep.unique() if c and c != '00000000' and len(c) == 8]
                        if valid_ceps:
                            estab_conds.append("estab_inner.cep IN %(ceps)s")
                            params['ceps'] = valid_ceps
                        local_df['_match_cep'] = series_cep
                        def clean_num_concatenated(row):
                            num = str(row.get(num_col, '')).replace('.0', '').strip().upper()
                            num = re.sub(r'\D', '', num)
                            cep = str(row.get('_match_cep', ''))
                            if num.startswith(cep) and len(num) > len(cep):
                                return num[len(cep):].lstrip('0')
                            raw_val = str(row.get(num_col, '')).split('.')[0].strip().upper()
                            return raw_val.lstrip('0') if raw_val.lstrip('0') else '0'
                        if num_col:
                            local_df['_match_num'] = local_df.apply(clean_num_concatenated, axis=1)
                        cep_df = local_df
                except Exception as e:
                    self._update_task(tid, status="FAILED", message=f"Erro ao analisar planilha CEP/NUMERO: {str(e)}")
                    return

            # REESTRUTURAÇÃO DA QUERY (FASE 4 - ULTRA ROBUSTO)
            estab_where = " AND ".join(estab_conds) if estab_conds else "1=1"
            empresas_where = " AND ".join(empresas_conds) if empresas_conds else "1=1"
            
            q = f"""
                SELECT 
                    e.razao_social AS NOME, 
                    CONCAT(estab.cnpj_basico, estab.cnpj_ordem, estab.cnpj_dv) AS CNPJ, 
                    estab.situacao_cadastral AS SITUACAO,
                    estab.cnae_fiscal AS CNAE, 
                    estab.logradouro AS RUA,
                    estab.numero AS NUMERO,
                    estab.bairro AS BAIRRO,
                    estab.CIDADE AS CIDADE, 
                    estab.uf AS UF, 
                    estab.cep AS CEP, 
                    estab.ddd1 AS DDD1, 
                    estab.telefone1 AS TEL1, 
                    estab.ddd2 AS DDD2, 
                    estab.telefone2 AS TEL2
                FROM hemn.empresas e
                INNER JOIN (
                    SELECT estab_inner.*, m.descricao as CIDADE 
                    FROM hemn.estabelecimento estab_inner 
                    LEFT JOIN hemn.municipio m ON estab_inner.municipio = m.codigo 
                    WHERE {estab_where} 
                    LIMIT 20000000
                ) AS estab ON e.cnpj_basico = estab.cnpj_basico
                WHERE {empresas_where}
                SETTINGS join_algorithm = 'auto'
            """
            
            # FASE 9: MOTOR DE LOTES HEMN (SINGLE OU MULTI QUERY)
            total_records_final = 0
            header_written = False
            
            import xlsxwriter
            workbook = xlsxwriter.Workbook(output_file, {'constant_memory': True, 'tmpdir': '/tmp'})
            sheet = workbook.add_worksheet("Extração Hemn")
            header_fmt = workbook.add_format({'bold': True, 'bg_color': '#3a7bd5', 'font_color': 'white'})

            ch_local = self._get_ch_client()

            # Caso especial: Otimização CEP + Número
            if cep_df is not None and num_col and '_match_num' in cep_df.columns:
                self._update_task(tid, progress=15, message="Otimizando consulta CEP+Número...")
                pairs = [tuple(x) for x in cep_df[['_match_cep', '_match_num']].drop_duplicates().values]
                batch_size_sql = 10000
                total_batches = (len(pairs) + batch_size_sql - 1) // batch_size_sql
                
                for b_idx in range(0, len(pairs), batch_size_sql):
                    status = self.get_task_status(tid)
                    if status.get("status") == "CANCELLED":
                        workbook.close()
                        return

                    batch_pairs = pairs[b_idx : b_idx + batch_size_sql]
                    # ClickHouse Tuple IN: (cep, numero) IN [(c1, n1), (c2, n2)]
                    current_params = params.copy()
                    current_params['pairs'] = batch_pairs
                    
                    # Injetar a condição de tupla
                    batch_estab_where = estab_where.replace("estab_inner.cep IN %(ceps)s", "(estab_inner.cep, estab_inner.numero) IN %(pairs)s")
                    if "(estab_inner.cep, estab_inner.numero) IN %(pairs)s" not in batch_estab_where:
                         # Caso não tivesse o IN ceps original:
                         batch_estab_where += " AND (estab_inner.cep, estab_inner.numero) IN %(pairs)s"

                    batch_q = q.replace(f"WHERE {estab_where}", f"WHERE {batch_estab_where}")
                    
                    prog_val = min(95, round(15 + (b_idx / len(pairs) * 80), 1))
                    self._update_task(tid, progress=prog_val, message=f"Consultando lote { (b_idx//batch_size_sql)+1 } / {total_batches}...")
                    
                    result = ch_local.query(batch_q, current_params)
                    df_batch = pd.DataFrame(result.result_rows, columns=result.column_names)
                    
                    if not df_batch.empty:
                        df_processed = self._process_extraction_dataframe(tid, df_batch, filters, workbook, sheet, header_fmt, header_written, total_records_final)
                        total_records_final += len(df_processed)
                        header_written = True
                
            else:
                # Caso padrão (Extração normal ou CEP sem Número)
                self._update_task(tid, progress=15, message="Executando consulta no ClickHouse...")
                result = ch_local.query(q, params)
                rows = result.result_rows
                cols = result.column_names
                total_rows_found = len(rows)
                
                self._update_task(tid, progress=20, message=f"Iniciando processamento de {total_rows_found:,} registros...")

                batch_size = 100000
                for i in range(0, total_rows_found, batch_size):
                    status = self.get_task_status(tid)
                    if status.get("status") == "CANCELLED":
                        workbook.close()
                        return

                    chunk = rows[i:i + batch_size]
                    df = pd.DataFrame(chunk, columns=cols)
                    
                    self._update_task(tid, progress=min(95, round(20 + (i/max(1, total_rows_found) * 75), 1)), 
                                      message=f"Processando: {i:,} / {total_rows_found:,} registros...")

                    if cep_df is not None and '_match_cep' in cep_df.columns:
                        df['_match_cep'] = df['CEP'].astype(str).str.replace(r'\D', '', regex=True).str.zfill(8)
                        valid_sheet_ceps = cep_df[['_match_cep']].drop_duplicates()
                        df = df.merge(valid_sheet_ceps, on='_match_cep', how='inner')
                        df = df.drop(columns=[c for c in ['_match_cep'] if c in df.columns])

                    if df.empty: continue
                    
                    df_processed = self._process_extraction_dataframe(tid, df, filters, workbook, sheet, header_fmt, header_written, total_records_final)
                    total_records_final += len(df_processed)
                    header_written = True

            workbook.close()
            # Fim da FASE 9

            self._update_task(tid, status="COMPLETED", progress=100, message=f"Extração Pronta! {total_records_final:,} encontrados.", result_file=output_file, record_count=total_records_final)
        except Exception as e:
            import traceback
            err_msg = traceback.format_exc()
            print(f"[CRITICAL] EXTRACTION THREAD FAILED for {tid}: {e}\n{err_msg}")
            try:
                self._update_task(tid, status="FAILED", message=f"TITANIUM-MT ERROR: {str(e)}")
            except:
                pass

    def _process_extraction_dataframe(self, tid, df, filters, workbook, sheet, header_fmt, header_written, start_row_count):
        """
        Sub-motor de processamento de dataframe para extração.
        Normaliza telefones, filtra operadoras e escreve no Excel.
        """
        if df.empty: return df

        # 1. Normalização de Telefones
        def check_tel(t):
            if not t or str(t).upper() in ['NAN', 'NONE']: return None
            num = re.sub(r'\D', '', str(t).strip().replace('.0', ''))
            if not num: return None
            return "CELULAR" if (len(num) == 9 or (len(num) == 8 and num[0] in '6789')) else "FIXO"

        def get_full(d, t):
            if not t or str(t).upper() in ['NAN', 'NONE']: return ""
            full = re.sub(r'\D', '', (str(d).replace('.0', '') if pd.notna(d) else "") + str(t).replace('.0', ''))
            if len(full) == 10 and full[2] in '6789': full = full[:2] + '9' + full[2:]
            return full

        df['full_t1'] = df.apply(lambda x: get_full(x['DDD1'], x['TEL1']), axis=1)
        df['full_t2'] = df.apply(lambda x: get_full(x['DDD2'], x['TEL2']), axis=1)
        df['t1_tipo'] = df['TEL1'].apply(check_tel)
        df['t2_tipo'] = df['TEL2'].apply(check_tel)

        tipo_req = filters.get("tipo_tel", "TODOS")
        if tipo_req == "AMBOS":
            mask = ((df['t1_tipo'] == "CELULAR") & (df['t2_tipo'] == "FIXO")) | ((df['t1_tipo'] == "FIXO") & (df['t2_tipo'] == "CELULAR"))
            df = df[mask].copy()
        elif tipo_req != "TODOS":
            df = df[(df['t1_tipo'] == tipo_req) | (df['t2_tipo'] == tipo_req)].copy()

        if df.empty: return df

        def select_phone(row):
            t1, t2 = row.get('full_t1', ''), row.get('full_t2', '')
            tipo1, tipo2 = row.get('t1_tipo'), row.get('t2_tipo')
            if tipo_req in ["CELULAR", "FIXO"]:
                if tipo1 == tipo_req: return t1
                return t2
            elif tipo_req == "AMBOS":
                parts = []
                if t1: parts.append(f"{tipo1}: {t1}")
                if t2: parts.append(f"{tipo2}: {t2}")
                return " | ".join(parts)
            if tipo1 == "CELULAR": return t1
            if tipo2 == "CELULAR": return t2
            return t1 if t1 else t2
            
        df['TELEFONE SOLICITADO'] = df.apply(select_phone, axis=1)
        df = df.drop(columns=[c for c in ['DDD1', 'TEL1', 'DDD2', 'TEL2', 't1_tipo', 't2_tipo', 'full_t1', 'full_t2'] if c in df.columns])
        
        # Enriquecimento de Operadora (em lotes)
        df = self._append_operator_column(tid, df)

        # Filtros de Operadora
        op_inc = str(filters.get("operadora_inc", "TODAS")).upper()
        op_exc = str(filters.get("operadora_exc", "NENHUMA")).upper()
        
        def check_op(row_val, target_op):
            if not row_val: return False
            rv = str(row_val).upper()
            to = str(target_op).upper()
            if to == "VIVO": return "VIVO" in rv or "TELEFONICA" in rv
            return to in rv

        if 'OPERADORA DO TELEFONE' in df.columns:
            if op_exc != "NENHUMA":
                df = df[~df['OPERADORA DO TELEFONE'].apply(lambda x: check_op(x, op_exc))]
            if op_inc != "TODAS":
                df = df[df['OPERADORA DO TELEFONE'].apply(lambda x: check_op(x, op_inc))]

        if df.empty: return df

        # Formatação Final
        df.columns = [str(c).upper().replace('_', ' ').strip() for c in df.columns]
        final_mapping = {'NOME': 'NOME DA EMPRESA', 'SITUACAO': 'SITUACAO CADASTRAL', 'RUA': 'LOGRADOURO', 'NUMERO': 'NUMERO DA FAIXADA'}
        df = df.rename(columns=final_mapping)
        
        sit_map = {'01':'NULA','02':'ATIVA','03':'SUSPENSA','04':'INAPTA','08':'BAIXADA'}
        if 'SITUACAO CADASTRAL' in df.columns:
            df['SITUACAO CADASTRAL'] = df['SITUACAO CADASTRAL'].astype(str).str.zfill(2).map(sit_map).fillna(df['SITUACAO CADASTRAL'])

        final_columns = ['CNPJ', 'NOME DA EMPRESA', 'SITUACAO CADASTRAL', 'CNAE', 'LOGRADOURO', 'NUMERO DA FAIXADA', 'BAIRRO', 'CIDADE', 'UF', 'CEP', 'TELEFONE SOLICITADO', 'OPERADORA DO TELEFONE']
        for c in final_columns:
            if c not in df.columns: df[c] = ""
            else: df[c] = df[c].astype(str).replace(['nan', 'NaN', 'None', '<NA>'], "")
        
        df_final = df[final_columns].fillna("")

        # Escrita no Excel
        EXCEL_LIMIT = 1000000 
        current_sheet_row = (start_row_count % EXCEL_LIMIT) + 1
        # Se for o primeiro lote de todos
        if not header_written:
            for col_idx, col_name in enumerate(df_final.columns):
                sheet.write(0, col_idx, col_name, header_fmt)
            current_sheet_row = 1

        data_matrix = df_final.values
        for r_idx, row_data in enumerate(data_matrix):
            # Nota: O controle de nova aba aqui é simplificado, 
            # assumimos que um único lote não estoura 1M se processado corretamente.
            for c_idx, val in enumerate(row_data):
                sheet.write(current_sheet_row, c_idx, val)
            current_sheet_row += 1
            
        return df_final

    # --- UNIFY ---
    def start_unify(self, file_paths, output_dir, username=None):
        f_summary = f"Unificar {len(file_paths)} arquivos"
        tid = self._create_task(module="UNIFY", username=username, filters=f_summary)
        threading.Thread(target=self._run_unify, args=(tid, file_paths, output_dir), daemon=True).start()
        return tid

    def _run_unify(self, tid, file_paths, output_dir):
        try:
            self._update_task(tid, status="PROCESSING", message="Unificando arquivos...")
            status = self.get_task_status(tid)
            if status.get("status") == "CANCELLED": return
            output_file = os.path.join(output_dir, f"Unificado_{tid[:8]}.xlsx")
            dfs = []
            for i, p in enumerate(file_paths):
                if p.endswith('.csv'):
                    dfs.append(pd.read_csv(p, sep=None, engine='python', dtype=str))
                else:
                    dfs.append(pd.read_excel(p, dtype=str))
                self._update_task(tid, progress=int(((i+1)/len(file_paths))*80))
            
            df_final = pd.concat(dfs, ignore_index=True)
            df_final.to_excel(output_file, index=False)
            self._update_task(tid, status="COMPLETED", progress=100, message="Arquivos unificados!", result_file=output_file, record_count=len(df_final))
        except Exception as e:
            self._update_task(tid, status="FAILED", message=f"Erro: {str(e)}")

    # --- CARRIER ---
    def batch_carrier(self, input_file, output_dir, phone_col, username=None):
        tid = self._create_task(module="CARRIER", username=username)
        threading.Thread(target=self._run_carrier, args=(tid, input_file, output_dir, phone_col), daemon=True).start()
        return tid

    def _run_carrier(self, tid, input_file, output_dir, phone_col):
        self._update_task(tid, status="PROCESSING", message="Iniciando Escaneamento Portabilidade-MT...")
        try:
            status = self.get_task_status(tid)
            if status.get("status") == "CANCELLED": return
            output_file = os.path.join(output_dir, f"Portabilidade_{tid[:8]}.xlsx")
            
            # Load Data
            if input_file.endswith('.csv'):
                with open(input_file, 'r', encoding='utf-8', errors='ignore') as f:
                    primeira = f.readline()
                sep = ';' if ';' in primeira else (',' if ',' in primeira else '\t')
                df = pd.read_csv(input_file, sep=sep, engine='python', dtype=str)
            else:
                df = pd.read_excel(input_file, dtype=str)
            
            total = len(df)
            self._update_task(tid, progress=5, message=f"Processando {total:,} registros...")

            # Determine Phone Column
            t_col = phone_col if (phone_col and phone_col in df.columns) else df.columns[0]
            
            # Normalize Phones
            df['titanium_tel'] = df[t_col].fillna('').astype(str).str.replace(r'\D', '', regex=True)
            df['titanium_tel'] = df['titanium_tel'].apply(lambda x: x[2:] if x.startswith('55') else x)
            
            phones_to_query = df['titanium_tel'].unique().tolist()
            # Double lookup: try 10 digits if 11 digit fails (some DBs have legacy format)
            phones_to_query_alt = [p[:len(p)-9] + p[len(p)-8:] for p in phones_to_query if len(p) == 11]
            all_queries = list(set(phones_to_query + phones_to_query_alt))

            op_results = {}
            op_map = self._get_carrier_map()
            
            # Batch Query SQLite (Titanium-MT Style)
            conn = sqlite3.connect(self.db_carrier)
            batch_size = 800
            for i in range(0, len(all_queries), batch_size):
                # Check cancellation
                if i % 4000 == 0:
                    status = self.get_task_status(tid)
                    if status.get("status") == "CANCELLED": 
                        conn.close()
                        return
                    self._update_task(tid, progress=int(5 + (i/len(all_queries))*85), message=f"Consultando Operadoras: {i:,}/{len(all_queries):,}...")

                batch = all_queries[i : i + batch_size]
                placeholders = ','.join(['?'] * len(batch))
                rows = conn.execute(f"SELECT telefone, operadora_id FROM portabilidade WHERE telefone IN ({placeholders})", batch).fetchall()
                for tel_db, op_id in rows:
                    op_results[str(tel_db)] = op_map.get(str(op_id), "OUTRA")
            conn.close()

            def _smart_map(t):
                # 1. Try SQLite portabilidade (Real Ported Data)
                res = None
                if t in op_results: res = op_results[t]
                if not res and len(t) == 11:
                    t10 = t[:2] + t[3:]
                    if t10 in op_results: res = op_results[t10]
                if not res:
                    t13 = "55" + t
                    if t13 in op_results: res = op_results[t13]
                
                if res and res != "OUTRA": return res
                
                # 2. Fallback: Prefix Lookup (Non-ported Original Carrier)
                num = re.sub(r'\D', '', t)
                if num.startswith("55"): num = num[2:]
                for length in range(7, 3, -1):
                    pref = num[:length]
                    if pref in self.prefix_tree:
                        return self.get_op_name(self.prefix_tree[pref])
                
                return res if res else "NÃO CONSTA"

            df['OPERADORA'] = df['titanium_tel'].map(_smart_map)
            
            # Cleanup and Save
            df.drop(columns=['titanium_tel'], inplace=True)
            df.to_excel(output_file, index=False)
            
            self._update_task(tid, status="COMPLETED", progress=100, message="Portabilidade Concluída!", result_file=output_file, record_count=total)
        except Exception as e:
            self._update_task(tid, status="FAILED", message=f"Erro: {str(e)}")

    def get_single_carrier(self, phone):
        try:
            conn = sqlite3.connect(self.db_carrier)
            tel = ''.join(filter(str.isdigit, str(phone)))
            if tel.startswith('55'): tel = tel[2:]
            
            # Smart Lookup (11 -> 10 -> 13)
            variations = [tel]
            if len(tel) == 11: variations.append(tel[:2] + tel[3:])
            variations.append("55" + tel)
            
            c = None
            for v in variations:
                c = conn.execute("SELECT operadora_id FROM portabilidade WHERE telefone = ?", (v,)).fetchone()
                if c: break

            if c:
                op_name = self.get_op_name(c[0])
                res = {"operadora": op_name, "tipo": "Móvel"}
            else:
                # Prefix Fallback for Single Lookup
                num = re.sub(r'\D', '', tel)
                op_name = "NÃO CONSTA"
                for length in range(7, 3, -1):
                    pref = num[:length]
                    if pref in self.prefix_tree:
                        op_name = self.get_op_name(self.prefix_tree[pref])
                        break
                res = {"operadora": op_name, "tipo": "Original/Prefix"}
            
            conn.close()
            return res
        except Exception as e:
            return {"operadora": f"ERRO: {str(e)}", "tipo": "N/D"}

    # --- SPLIT ---
    def start_split(self, input_file, output_dir, username=None):
        fname = os.path.basename(input_file)
        f_summary = f"Fatiar: {fname}"
        tid = self._create_task(module="SPLIT", username=username, filters=f_summary)
        threading.Thread(target=self._run_split, args=(tid, input_file, output_dir), daemon=True).start()
        return tid

    def _run_split(self, tid, input_file, output_dir):
        print(f"[SPLIT] Iniciando tarefa {tid} para arquivo: {input_file}")
        self._update_task(tid, status="PROCESSING", message="Iniciando fatiamento...")
        try:
            output_file = os.path.join(output_dir, f"Dividido_{tid[:8]}.xlsx")
            import xlsxwriter
            
            # Se for Excel, usamos o modo padrão (Excel gigante é raro, o limite é 1M de linhas)
            # Se for CSV, usamos chunks para evitar estourar a RAM
            is_csv = not input_file.lower().endswith(('.xlsx', '.xls', '.xlsm'))
            
            writer = pd.ExcelWriter(output_file, engine='xlsxwriter', engine_kwargs={'options': {'constant_memory': True}})
            total_rows = 0
            chunk_size = 1000000

            if is_csv:
                self._update_task(tid, message="Lendo CSV em blocos (otimizado)...")
                # Detectar separador e encoding de forma robusta
                sep = ','
                enc = 'utf-8'
                try:
                    with open(input_file, 'rb') as f:
                        raw = f.read(10240) # Aumentado para 10KB para amostragem melhor
                        # Tenta utf-8
                        try:
                            sample = raw.decode('utf-8')
                            enc = 'utf-8'
                        except:
                            sample = raw.decode('latin-1')
                            enc = 'latin-1'
                        
                        delims = [';', ',', '\t', '|']
                        max_count = 0
                        for d in delims:
                            count = sample.count(d)
                            if count > max_count:
                                max_count = count
                                sep = d
                    print(f"[SPLIT] Detecção: sep='{sep}', enc='{enc}'")
                except Exception as e:
                    print(f"[SPLIT] Erro na detecção: {e}")

                total_rows = sum(1 for _ in open(input_file, 'rb'))
                processed_rows = 0
                reader = pd.read_csv(input_file, sep=sep, chunksize=chunk_size, dtype=str, encoding=enc, on_bad_lines='skip', header=None, engine='c')
                
                for i, chunk in enumerate(reader):
                    sheet_name = f"Lote_{i+1}"
                    chunk.to_excel(writer, sheet_name=sheet_name, index=False)
                    processed_rows += len(chunk)
                    prog = min(99, int((processed_rows / (total_rows or 1)) * 100))
                    self._update_task(tid, progress=prog, message=f"Fatiando: {processed_rows:,}/{total_rows:,} linhas...")
                    print(f"[SPLIT] {tid} -> Processadas {processed_rows:,} linhas")
                total_rows = processed_rows
            else:
                self._update_task(tid, message="Lendo Excel gigante...")
                df = pd.read_excel(input_file, dtype=str)
                total_rows = len(df)
                for i in range(0, total_rows, chunk_size):
                    chunk = df.iloc[i : i + chunk_size]
                    sheet_name = f"Lote_{(i//chunk_size)+1}"
                    chunk.to_excel(writer, sheet_name=sheet_name, index=False)
                    self._update_task(tid, progress=int((i/total_rows)*100), message=f"Escrevendo {sheet_name}...")
            
            writer.close()
            print(f"[SPLIT] Sucesso: {output_file} ({total_rows} linhas)")
            self._update_task(tid, status="COMPLETED", progress=100, message=f"Dividido com sucesso! {total_rows:,} linhas.", result_file=output_file, record_count=total_rows)
        except Exception as e:
            print(f"[SPLIT ERROR] {tid}: {str(e)}")
            self._update_task(tid, status="FAILED", message=f"Erro: {str(e)}")

    def _get_carrier_map(self):
        op_map = {
            "55320":"VIVO", "55323":"VIVO", "55215":"VIVO", "55324":"VIVO", "55377":"VIVO",
            "55321":"CLARO", "55351":"CLARO", "55322":"CLARO", "55371":"CLARO", "55306":"ALGAR",
            "55341":"TIM", "55343":"SERCOMTEL", "55331":"OI", "55312":"ALGAR", "55345":"ALGAR",
            "55112":"ALGAR", "55121":"CLARO", "55123":"TIM", "55131":"OI", "55141":"TIM",
            "55143":"SERCOMTEL", "55204":"SERCOMTEL", "55301":"ARQIA", "55303":"SISTEER",
            "55305":"VIRGIN", "55315":"TELECALL", "55327":"ALGAR", "55348":"TRANSATEL",
            "55367":"CUBIC", "55393":"GLOBALSTAR", "55106":"AMERICADOMÉSTICA", "55307":"AMERICADOMÉSTICA",
            "55211":"BRISANET", "55322":"BRISANET", "55101":"TELECALL", "55191":"IPCORP"
        }
        full_map = {
            "55100":"Interjato", "55102":"Life Telecom", "55103":"DD Telecom", "55104":"DB3", "55105":"Unifique",
            "55107":"Vipnet", "55108":"Osi Telecom", "55109":"Tellig", "55111":"SuperTV", "55113":"Fonar",
            "55116":"Fidelity", "55117":"Transit", "55118":"Spin", "55119":"ZaaZ", "55120":"GTI", "55124":"Megatelecom",
            "55126":"IDT Brasil", "55127":"VIRTUAL", "55128":"Voxbras", "55129":"T-Leste", "55130":"WKVE",
            "55132":"CONVERGIA", "55133":"NWI", "55136":"DSLI", "55137":"Golden Line", "55138":"Tesa", "55139":"Netglobalis",
            "55140":"Hoje Telecom", "55142":"GT Group", "55144":"Sul Internet", "55145":"Cirion", "55147":"British Telecom",
            "55148":"Netserv", "55149":"BBS Options", "55150":"Cambridge", "55151":"Vero S.A.", "55152":"Alares",
            "55153":"GIGA MAIS", "55154":"Viafibra", "55155":"Big Telco", "55156":"Engevox", "55157":"One Telecom",
            "55158":"Voitel", "55161":"Vonex", "55162":"Mundivox", "55163":"Hello Brazil", "55164":"Brasil Tecpar",
            "55166":"Quex", "55167":"DIRECTCALL", "55168":"Tremnet", "55170":"Locaweb", "55171":"YIP", "55172":"BTT",
            "55173":"Brastel", "55174":"TELEFREE", "55176":"Adylnet", "55177":"Opção", "55178":"Nortelpa", "55179":"Option",
            "55180":"Plumium", "55181":"Datora", "55184":"BRFibra", "55185":"UltraNet", "55186":"Teletel", "55187":"EAI",
            "55188":"TVN VOZ", "55189":"CONECTA", "55192":"LIG16", "55193":"Vipway", "55194":"76 Telecom", "55196":"iVATi",
            "55197":"EAD", "55198":"Ligue Telecom", "55199":"Ensite", "55200":"Porto Velho", "55201":"Hit Telecom",
            "55202":"Smartspace", "55203":"Valenet", "55205":"UFINET", "55206":"Desktop", "55208":"Ponto Telecom",
            "55209":"WCS", "55210":"Morango", "55213":"Tri Telecom", "55214":"Orange", "55216":"Ampernet",
            "55217":"TERAPAR", "55218":"Grandi Telecom", "55219":"Redcontrol", "55220":"Net Angra", "55221":"GGNET",
            "55222":"ADP3", "55223":"Citta", "55224":"Algar VGL", "55225":"Conectcor", "55226":"Unitelco", "55227":"Tely",
            "55228":"GO1", "55229":"Tubaron", "55230":"Titania", "55231":"Brasilfone", "55232":"Bignet", "55233":"Superonda",
            "55234":"Córdia", "55235":"BRDigital", "55236":"MG Conecta", "55237":"Goiás Telecom", "55238":"Mhnet",
            "55239":"Vonare", "55240":"Predialnet", "55241":"Nedel", "55242":"Tcheturbo", "55245":"Toque Telecom",
            "55246":"Neo Telecom", "55247":"RED Telecom", "55248":"Itelco", "55249":"Você Telecom", "55250":"LINKTEL",
            "55251":"DBUG", "55252":"BLUE TELECOM", "55253":"ALAWEB", "55254":"Brasrede", "55255":"OXMAN",
            "55256":"Nova Tecnologia", "55258":"Conecta Provedor", "55259":"Sothis", "55260":"Conectv", "55261":"Empire",
            "55262":"Ves Telecom", "55263":"MD Brasil", "55264":"NGT Telecom", "55265":"QNET Telecom", "55266":"8BR",
            "55267":"ORION", "55268":"Nip Telecom", "55269":"Connectronic", "55270":"Mundo Telecom", "55271":"SpeedTravel",
            "55272":"PAK Telecom", "55273":"Process", "55274":"BRAZILIAN", "55275":"High Connect", "55277":"Gente",
            "55278":"Bitcom", "55279":"C3 Telecom", "55280":"NT2 Telecom", "55281":"CPNET", "55282":"Viva Vox",
            "55283":"Rocketnet", "55285":"Alfa Telecom", "55286":"Next Telecom", "55287":"Sulnet", "55288":"Fiber One",
            "55289":"ITANET", "55290":"Superip", "55291":"Link 10", "55292":"Gigalink", "55293":"Vip Telecom",
            "55294":"Iveloz", "55295":"Baldussi", "55296":"Global Lines", "55297":"Softdados", "55298":"Advance",
            "55299":"Ôtima Telecom", "55300":"Bras Nuvem", "55301":"Arqia", "55304":"Terapar", "55306":"Surf Telecom",
            "55308":"Ligue Telecom", "55309":"Unifique", "55310":"Vecto Mobile", "55311":"NLT", "55313":"Emnify",
            "55322":"Brisanet", "55343":"Sercomtel Celular", "55348":"Transatel", "55356":"Airnity", "55360":"Neko Serviços",
            "55364":"1nce", "55370":"Iez Telecom", "55375":"Superchip", "55388":"Connect Iot", "55391":"IPCorp",
            "55393":"Globalstar", "55401":"ACB Fibra", "55404":"Client CO", "55410":"Supranet", "55411":"Tel & Globe",
            "55420":"MNET", "55440":"IBI Telecom", "55460":"AMULTIPHONE", "55470":"Customer First", "55474":"BR DID",
            "55477":"ACESSE COMUNICACAO", "55479":"MAISVOIP", "55480":"Softpollus", "55481":"Redfox Fiber",
            "55482":"TRI D TELECOM", "55483":"Vono Tecnologia", "55484":"ABRATEL", "55485":"RCE IT",
            "55486":"PANDA NETWORK", "55487":"FIVENET", "55488":"GL Fibra", "55489":"Bitwave", "55490":"Nicnet",
            "55491":"TOTAL PHONE", "55492":"NETFLEX", "55493":"INOVA FIBRA", "55494":"Allfiber", "55495":"Rolim Net",
            "55496":"ALOSEC", "55497":"NET WAY", "55498":"Digital Net", "55499":"Seagate", "55512":"Plis Inteligência",
            "55534":"Vox One", "55538":"Lestetronics", "55553":"FB Net", "55557":"Soft System", "55570":"Atelex",
            "55576":"RMNetwork", "55580":"Pronto Fibra", "55584":"ITELECOM", "55585":"Global Fibra", "55589":"Osirnet",
            "55590":"LH TELECOM", "55600":"MEGALINK", "55603":"Cyber Internet", "55605":"Ame Telecom",
            "55614":"L T Soluções", "55618":"T. T. A. Soluções", "55623":"Sigatel", "55629":"Internet 10",
            "55630":"R2 Dados", "55633":"The Fiber", "55634":"Wn Telecom", "55639":"Niqturbo", "55640":"Nova NET",
            "55645":"JR Telecom", "55651":"Erictel", "55653":"Cn Telecom", "55654":"Lastnet", "55655":"Mega Net",
            "55660":"Viatec", "55662":"TR Telecom", "55665":"Indanet", "55668":"Brlognet", "55673":"UBA Conect",
            "55677":"BrasilNet", "55678":"Contato Internet", "55679":"Servstar", "55682":"Turbonet", "55684":"Gr@mnet",
            "55688":"Signet", "55694":"Handix", "55698":"Sati Telecom", "55701":"Drcall", "55703":"Innova",
            "55704":"Vale Vox", "55707":"G2G Internet", "55712":"Rio Grande", "55722":"GlobalNet", "55724":"New Voice",
            "55733":"Internet Play", "55746":"Onlink", "55751":"Upix Networks", "55761":"Conecte Telecom",
            "55764":"He Net", "55777":"METODO TELECOM", "55782":"Sonik", "55790":"WGO Multimidia", "55791":"4NET",
            "55820":"NPX", "55834":"Desktop Internet", "55853":"Assim", "55880":"Coelho Tecnologia",
            "55889":"Conectlan", "55890":"Btelway", "55916":"Multiware", "55947":"Brphonia", "55974":"Serra Geral",
            "55975":"Vulcanet", "55984":"FTTH Telecom"
        }
        op_map.update(full_map)
        
        # MERGE WITH DYNAMICALLY LOADED ANATEL DICT (From CSV)
        if hasattr(self, 'anatel_dict'):
            op_map.update(self.anatel_dict)
            
        # NORMALIZAÇÃO HEMN PARA FILTROS ROBUSTOS
        normalized = {}
        for k, v in op_map.items():
            vu = str(v).upper().strip()
            # Identificação Específica (evita que "VOICE/VOIP" seja detectado como "OI")
            if "TELEFONICA" in vu or "VIVO" in vu: normalized[k] = "VIVO / TELEFONICA"
            elif "CLARO" in vu: normalized[k] = "CLARO"
            elif "TIM" in vu: normalized[k] = "TIM"
            elif vu == "OI" or vu.startswith("OI ") or "OI S.A" in vu or "OI MOVEL" in vu or "TELEMAR" in vu: 
                normalized[k] = "OI"
            elif "ALGAR" in vu: normalized[k] = "ALGAR"
            elif "BRISANET" in vu: normalized[k] = "BRISANET"
            else: normalized[k] = vu
        return normalized

    def _append_operator_column(self, tid, df):
        self._update_task(tid, progress=90, message="Identificando operadoras...")
        try:
            phones_to_query = df['TELEFONE SOLICITADO'].dropna().astype(str).str.replace(r'\D', '', regex=True).tolist()
            phones_to_query = list(set([p for p in phones_to_query if p]))
            phones_to_query_clean = [p[2:] if p.startswith('55') else p for p in phones_to_query]
            phones_to_query_alt = [p[:len(p)-9] + p[len(p)-8:] for p in phones_to_query_clean if len(p) == 11]
            all_queries = list(set(phones_to_query_clean + phones_to_query_alt))

            conn = sqlite3.connect(self.db_carrier)
            op_results = {}
            op_map = self._get_carrier_map()
            
            batch_size = 900
            for i in range(0, len(all_queries), batch_size):
                batch = all_queries[i : i + batch_size]
                placeholders = ','.join(['?'] * len(batch))
                rows = conn.execute(f"SELECT telefone, operadora_id FROM portabilidade WHERE telefone IN ({placeholders})", batch).fetchall()
                for tel_db, op_id in rows:
                    op_results[str(tel_db)] = op_map.get(str(op_id), "OUTRA")
            conn.close()

            def _smart_map(t):
                if pd.isna(t) or not t: return "NÃO CONSTA"
                t = str(t).replace(r'\D', '')
                if t.startswith('55'): t = t[2:]
                
                res = None
                if t in op_results: res = op_results[t]
                if not res and len(t) == 11:
                    t10 = t[:2] + t[3:]
                    if t10 in op_results: res = op_results[t10]
                if not res:
                    t13 = "55" + t
                    if t13 in op_results: res = op_results[t13]
                
                if res and res != "OUTRA": return res
                
                num = re.sub(r'\D', '', t)
                if num.startswith("55"): num = num[2:]
                for length in range(7, 3, -1):
                    pref = num[:length]
                    if pref in self.prefix_tree:
                        return self.get_op_name(self.prefix_tree[pref]).upper()
                return "NÃO CONSTA"

            df['OPERADORA DO TELEFONE'] = df['TELEFONE SOLICITADO'].apply(_smart_map)
            return df
        except Exception as e:
            import traceback
            print(f"Erro no filtro de operadora: {e}")
            traceback.print_exc()
            df['OPERADORA DO TELEFONE'] = "ERRO"
            return df
