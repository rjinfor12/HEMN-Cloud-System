from fastapi import FastAPI, HTTPException, Depends, Header, Request, UploadFile, File, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
import sqlite3
import os
import jwt
from datetime import datetime, timedelta
from typing import Optional, List
import shutil
import uuid

# Importações customizadas
import cloud_engine
print(f"[DEBUG] cloud_engine file: {cloud_engine.__file__}")
from cloud_engine import CloudEngine

app = FastAPI(title="HEMN Web Suite API")

import sys

# Setup de Pastas (Caminhos Absolutos para robustez e compatibilidade com PyInstaller)
def get_app_dir():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

def get_resource_dir():
    if getattr(sys, 'frozen', False):
        return sys._MEIPASS
    return os.path.dirname(os.path.abspath(__file__))

APP_DIR = get_app_dir()
RESOURCE_DIR = get_resource_dir()

# Priorizar pasta estática local se existir (permite atualizações sem recompilar)
LOCAL_STATIC = os.path.join(APP_DIR, "static")
if os.path.exists(LOCAL_STATIC) and os.path.isdir(LOCAL_STATIC):
    STATIC_DIR = LOCAL_STATIC
else:
    STATIC_DIR = os.path.join(RESOURCE_DIR, "static")

UPLOAD_DIR = os.path.join(APP_DIR, "storage", "uploads")
RESULT_DIR = os.path.join(APP_DIR, "storage", "results")

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(RESULT_DIR, exist_ok=True)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/")
async def read_index():
    # Prefer index_vps.html in root, then static
    root_vps = os.path.join(APP_DIR, "index_vps.html")
    if os.path.exists(root_vps):
        return FileResponse(root_vps)
    
    static_vps = os.path.join(STATIC_DIR, "index_vps.html")
    if os.path.exists(static_vps):
        return FileResponse(static_vps)
        
    # Fallback to index.html in root
    return FileResponse(os.path.join(APP_DIR, "index.html"))

@app.get("/admin/monitor")
async def read_monitor():
    return FileResponse(os.path.join(STATIC_DIR, "admin_monitor.html"))

# Permite acesso de qualquer lugar
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_PATH = os.path.join(APP_DIR, "hemn_cloud.db")
print(f"[DEBUG] DB_PATH: {DB_PATH}")
SECRET_KEY = "HEMN_SECRET_SUPER_SAFE_123"
ALGORITHM = "HS256"

from fastapi.responses import JSONResponse
import traceback

@app.middleware("http")
async def catch_exceptions_middleware(request: Request, call_next):
    try:
        return await call_next(request)
    except Exception as exc:
        err_msg = traceback.format_exc()
        print(f"CRITICAL ERROR on {request.url.path}: {exc}\n{err_msg}")
        with open(os.path.join(APP_DIR, "server_error.log"), "a", encoding="utf-8") as f:
            f.write(f"\n[{datetime.now().isoformat()}] CRITICAL on {request.url.path}:\n{err_msg}\n")
        return JSONResponse(status_code=500, content={"error": "Internal Server Error", "detail": str(exc)})


# Inicializar Engine
engine = CloudEngine(
    db_path=DB_PATH, db_cnpj_path=os.path.join(APP_DIR, "cnpj.db"),
    db_carrier_path=os.path.join(APP_DIR, "hemn_carrier.db")
)

# --- MODELS ---
class LoginRequest(BaseModel):
    username: str
    password: str

class ExtractionFilter(BaseModel):
    uf: Optional[str] = None
    cidade: Optional[str] = None
    cnae: Optional[str] = None
    tipo_tel: Optional[str] = "TODOS"
    situacao: Optional[str] = "02"
    somente_com_telefone: Optional[bool] = False
    cep_file: Optional[str] = None

class UnifyRequest(BaseModel):
    file_ids: List[str]

class EnrichRequest(BaseModel):
    file_id: Optional[str] = None
    name_col: Optional[str] = None
    cpf_col: Optional[str] = None
    manual: Optional[bool] = False
    name: Optional[str] = None
    cpf: Optional[str] = None


class CarrierRequest(BaseModel):
    file_id: str
    phone_col: str

class SplitRequest(BaseModel):
    file_id: str

class LeadSearchRequest(BaseModel):
    search_type: str # 'cpf', 'nome', 'telefone'
    search_term: str
    scope: str # 'ESTADO', 'REGIAO', 'BRASIL'
    uf: Optional[str] = None
    regiao_nome: Optional[str] = None

# --- AUTH HELPERS ---
def create_token(username: str):
    expire = datetime.utcnow() + timedelta(hours=24)
    return jwt.encode({"sub": username, "exp": expire}, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Não autorizado")
    token = authorization.split(" ")[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        conn = sqlite3.connect(DB_PATH, timeout=30)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.row_factory = sqlite3.Row
        user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        conn.close()
        if not user: raise HTTPException(status_code=401)
        return dict(user)
    except:
        raise HTTPException(status_code=401, detail="Sessão expirada")

def check_clinicas_access(user: dict = Depends(get_current_user)):
    if user["role"] not in ["ADMIN", "CLINICAS"]:
        raise HTTPException(status_code=403, detail="Acesso restrito ao perfil Clínicas ou Administrador")
    return user

def log_transaction(username: str, type: str, amount: float, module: str, description: str, task_id: str = None):
    try:
        now_br = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"[DEBUG] [{now_br}] Tentando logar transação para {username}: {type} {amount} no módulo {module}")
        conn = sqlite3.connect(DB_PATH, timeout=30)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute(
            "INSERT INTO credit_transactions (username, type, amount, module, description, task_id, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (username, type, amount, module, description, task_id, now_br)
        )
        conn.commit()
        conn.close()
        print(f"[DEBUG] Transação logada com sucesso para {username}")
    except Exception as e:
        print(f"CRITICAL: Erro ao logar transação: {e}")
        traceback.print_exc()

# --- ENDPOINTS DE ARQUIVOS ---

@app.post("/upload")
async def upload_file(file: UploadFile = File(...), user: dict = Depends(get_current_user)):
    file_id = f"{uuid.uuid4()}_{file.filename}"
    file_path = os.path.join(UPLOAD_DIR, file_id)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return {"file_id": file_id, "filename": file.filename}

@app.get("/download/{task_id}")
async def download_result(task_id: str, user: dict = Depends(get_current_user)):
    task = engine.get_task_status(task_id)
    if task["status"] != "COMPLETED":
        raise HTTPException(status_code=400, detail="Arquivo ainda não está pronto.")
    
    count = task.get("record_count", 0)
    
    # Conferir se já foi pago (evitar duplicidade de cobrança e de log no extrato)
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.execute("PRAGMA journal_mode=WAL")
    already_paid = conn.execute(
        "SELECT 1 FROM credit_transactions WHERE username = ? AND task_id = ? AND type = 'DEBIT'",
        (user["username"], task_id)
    ).fetchone()
    conn.close()

    if not already_paid:
        # Descontar créditos se não for limit >= 9 Mi
        if user["total_limit"] < 9000000:
            available = user["total_limit"] - user["current_usage"]
            if available < count:
                raise HTTPException(status_code=403, detail=f"Saldo insuficiente. Necessário: {count:,} Cr | Disponível: {available:,.0f} Cr")
                
            conn = sqlite3.connect(DB_PATH, timeout=30)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("UPDATE users SET current_usage = current_usage + ? WHERE username = ?", (count, user["username"]))
            conn.commit()
            conn.close()

        # Logar transação apenas na PRIMEIRA vez
        module = task.get("module", "DOWNLOAD")
        log_transaction(
            user["username"], 
            "DEBIT", 
            count, 
            module, 
            f"Download de {count:,} registros ({os.path.basename(task['result_file'])})",
            task_id=task_id
        )
    
    return FileResponse(task["result_file"], filename=os.path.basename(task["result_file"]))

# --- ENDPOINTS DE TAREFAS (HEMN SUITE) ---

import json

class NpEncoder(json.JSONEncoder):
    def default(self, obj):
        if hasattr(obj, 'item'):
            try:
                # Cast numpy types to int or float based on class name
                if type(obj).__name__.startswith('int'): return int(obj)
                if type(obj).__name__.startswith('float'): return float(obj)
                return obj.item()
            except:
                pass
        if type(obj).__module__ == 'numpy':
            return obj.tolist()
        return super(NpEncoder, self).default(obj)

@app.get("/tasks/{task_id}")
def get_task(task_id: str, user: dict = Depends(get_current_user)):
    status_data = engine.get_task_status(task_id)
    # The ultimate JSON-safe sanitizer: serialize to string and back to dict
    clean_json_str = json.dumps(status_data, cls=NpEncoder)
    return json.loads(clean_json_str)

@app.post("/tasks/unify")
def start_unify(req: UnifyRequest, user: dict = Depends(get_current_user)):
    paths = [os.path.join(UPLOAD_DIR, fid) for fid in req.file_ids]
    tid = engine.start_unify(paths, RESULT_DIR, username=user["username"])
    return {"task_id": tid}

@app.post("/leads/search")
def search_leads(req: LeadSearchRequest, user: dict = Depends(check_clinicas_access)):
    # Limpeza básica do termo
    term = req.search_term.strip()
    if not term:
        raise HTTPException(status_code=400, detail="Termo de pesquisa é obrigatório")
    
    # Validação de escopo
    if req.scope == 'ESTADO' and not req.uf:
        raise HTTPException(status_code=400, detail="UF é obrigatória para pesquisa por estado")
    if req.scope == 'REGIAO' and not req.regiao_nome:
        raise HTTPException(status_code=400, detail="Nome da região é obrigatório")

    try:
        results = engine.search_leads(
            search_type=req.search_type,
            search_term=term,
            scope=req.scope,
            uf=req.uf,
            regiao=req.regiao_nome
        )
        # Log transaction as a record (0 credits)
        try:
            log_transaction(user["username"], "DEBIT", 0.0, "CLINICAS", f"Consulta PF: {term}")
        except Exception as te:
            print(f"[ERROR] Failed to log PF search transaction: {te}")
            
        return results
    except Exception as e:
        print(f"[ERROR] Lead Search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/tasks/enrich")
def start_enrich(req: EnrichRequest, user: dict = Depends(get_current_user)):
    if req.manual:
        # Limpeza básica do CPF
        cpf_clean = ''.join(filter(str.isdigit, str(req.cpf or "")))
        res = engine.deep_search(req.name, cpf_clean)
        
        # Débito de Consulta Manual se não for ilimitado
        if user["total_limit"] < 9000000:
            conn = sqlite3.connect(DB_PATH, timeout=30)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("UPDATE users SET current_usage = current_usage + 0.5 WHERE username = ?", (user["username"],))
            conn.commit()
            conn.close()
        
        # Logar transação SEMPRE
        log_transaction(user["username"], "DEBIT", 0.5, "MANUAL", f"Busca Unitária: {req.name or req.cpf}")
            
        return res.to_dict(orient="records")
    
    if not req.file_id:
        raise HTTPException(status_code=400, detail="Nenhum arquivo (file_id) fornecido. Envie o arquivo primeiro.")
    
    path = os.path.join(UPLOAD_DIR, req.file_id)
    import inspect
    print(f"[DEBUG] engine: {type(engine)}, sig: {inspect.signature(engine.start_enrich)}")
    tid = engine.start_enrich(path, RESULT_DIR, req.name_col, req.cpf_col, username=user["username"])
    # Logar início de processamento
    log_transaction(user["username"], "CREDIT", 0, "ENRICH", f"Iniciado processamento em lote: {req.file_id}")
    return {"task_id": tid}

@app.post("/tasks/extract")
def start_extract(filters: ExtractionFilter, user: dict = Depends(get_current_user)):
    # Logar início de extração
    log_transaction(user["username"], "CREDIT", 0, "EXTRACT", f"Iniciada extração de dados: {filters.uf} - {filters.cidade}")
    
    tid = engine.start_extraction(filters.dict(), RESULT_DIR, username=user["username"])
    return {"task_id": tid}

@app.post("/tasks/carrier")
def start_carrier(req: CarrierRequest, user: dict = Depends(get_current_user)):
    path = os.path.join(UPLOAD_DIR, req.file_id)
    tid = engine.batch_carrier(path, RESULT_DIR, req.phone_col, username=user["username"])
    # Logar início de processamento
    log_transaction(user["username"], "CREDIT", 0, "CARRIER", f"Iniciada consulta de operadoras em lote")
    return {"task_id": tid}

@app.get("/tasks/carrier/single")
def get_single_carrier(phone: str, user: dict = Depends(get_current_user)):
    # Débito de Consulta de Operadora se não for ilimitado
    if user["total_limit"] < 9000000:
        conn = sqlite3.connect(DB_PATH, timeout=30)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("UPDATE users SET current_usage = current_usage + 0.1 WHERE username = ?", (user["username"],))
        conn.commit()
        conn.close()

    # Logar transação SEMPRE
    log_transaction(user["username"], "DEBIT", 0.1, "CARRIER", f"Portabilidade Individual: {phone}")
        
    return engine.get_single_carrier(phone)

@app.post("/tasks/split")
def start_split(req: SplitRequest, user: dict = Depends(get_current_user)):
    path = os.path.join(UPLOAD_DIR, req.file_id)
    tid = engine.start_split(path, RESULT_DIR, username=user["username"])
    return {"task_id": tid}

@app.get("/tasks/active")
def get_active_tasks(user: dict = Depends(get_current_user)):
    return engine.get_user_tasks(user["username"])

@app.post("/tasks/{task_id}/cancel")
def cancel_task(task_id: str, user: dict = Depends(get_current_user)):
    # Verify ownership
    status = engine.get_task_status(task_id)
    if status.get("username") != user["username"] and user["role"] != "ADMIN":
        raise HTTPException(status_code=403, detail="Não autorizado a cancelar esta tarefa.")
    success = engine.cancel_task(task_id)
    return {"status": "ok" if success else "error"}

# --- AUTH & ADMIN (LEGACY COMPAT) ---

@app.post("/login")
async def login(request: Request):
    try: data = await request.form()
    except: data = await request.json()
    u, p = data.get("username"), data.get("password")
    
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.row_factory = sqlite3.Row
    user = conn.execute("SELECT * FROM users WHERE username = ? AND password = ?", (u, p)).fetchone()
    if user:
        if user["status"] != "ACTIVE": 
            conn.close()
            raise HTTPException(status_code=403, detail="Acesso bloqueado.")
        token = create_token(u)
        conn.execute("UPDATE users SET last_login = ? WHERE username = ?", (datetime.now().isoformat(), u))
        conn.commit()
        conn.close()
        return {"access_token": token, "token_type": "bearer"}
    conn.close()
    raise HTTPException(status_code=401, detail="Usuário ou senha incorretos.")

@app.get("/me")
def get_me(user: dict = Depends(get_current_user)):
    return user

@app.get("/admin/users")
def list_users(user: dict = Depends(get_current_user)):
    if user["role"] != "ADMIN": 
        raise HTTPException(status_code=403, detail="Acesso restrito.")
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.row_factory = sqlite3.Row
    users = conn.execute("SELECT * FROM users").fetchall()
    conn.close()
    return [dict(u) for u in users]

@app.get("/admin/monitor/stats")
def get_monitor_stats(user: dict = Depends(get_current_user)):
    if user["role"] != "ADMIN": 
        raise HTTPException(status_code=403, detail="Acesso restrito a administradores.")
    
    # 1. System Stats (Linux /proc fallback)
    sys_stats = {"cpu": 0, "ram": 0, "disk": 0}
    try:
        # RAM
        if os.path.exists("/proc/meminfo"):
            with open("/proc/meminfo", "r") as f:
                lines = f.readlines()
                total = int(lines[0].split()[1])
                available = int(lines[2].split()[1]) # MemAvailable is better than MemFree
                sys_stats["ram"] = round(100 - (available / total * 100), 1)
        
        # CPU (Load average as % scaling)
        if os.path.exists("/proc/loadavg"):
            with open("/proc/loadavg", "r") as f:
                load = float(f.read().split()[0])
                # We assume 4 cores for scaling or just raw load for visual
                sys_stats["cpu"] = min(100.0, round(load * 25, 1)) 

        # Disk
        usage = shutil.disk_usage("/")
        sys_stats["disk"] = round((usage.used / usage.total) * 100, 1)
    except:
        pass

    # 2. Engine Stats
    engine_stats = engine.get_internal_stats()
    
    # 3. ClickHouse Stats
    ch_stats = engine.get_ch_metrics()
    
    return {
        "system": sys_stats,
        "engine": engine_stats,
        "clickhouse": ch_stats,
        "timestamp": datetime.now().isoformat()
    }

@app.put("/admin/users/{username}")
def update_user(username: str, data: dict, user: dict = Depends(get_current_user)):
    if user["role"] != "ADMIN": raise HTTPException(status_code=403)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    old_user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    
    for k, v in data.items():
        conn.execute(f"UPDATE users SET {k} = ? WHERE username = ?", (v, username))
    
    # Se o limite aumentou, logar como crédito/recarga
    if "total_limit" in data and old_user:
        diff = float(data["total_limit"]) - float(old_user["total_limit"])
        if diff > 0:
            log_transaction(username, "CREDIT", diff, "ADMIN", f"Recarga de créditos via Administrador")
            
    conn.commit()
    conn.close()
    return {"status": "ok"}

@app.get("/credits/statement")
def get_statement(days: Optional[int] = None, user: dict = Depends(get_current_user), limit: int = 100):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    
    query = "SELECT * FROM credit_transactions WHERE username = ?"
    params = [user["username"]]
    
    if days is not None:
        query += " AND timestamp >= date('now', '-' || ? || ' days')"
        params.append(days)
    
    query += " ORDER BY timestamp DESC LIMIT ?"
    params.append(limit)
    
    logs = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(l) for l in logs]

@app.get("/admin/statement/{target_username}")
def get_user_statement(target_username: str, days: Optional[int] = None, user: dict = Depends(get_current_user), limit: int = 200):
    if user["role"] != "ADMIN":
        raise HTTPException(status_code=403, detail="Acesso restrito a administradores.")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    
    query = "SELECT * FROM credit_transactions WHERE username = ?"
    params = [target_username]
    if days is not None:
        query += " AND timestamp >= date('now', '-' || ? || ' days')"
        params.append(days)
    
    query += " ORDER BY timestamp DESC LIMIT ?"
    params.append(limit)
    
    logs = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(l) for l in logs]

@app.get("/admin/stats/{target_username}")
def get_user_stats(target_username: str, user: dict = Depends(get_current_user)):
    if user["role"] != "ADMIN":
        raise HTTPException(status_code=403, detail="Acesso restrito a administradores.")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    target_user = conn.execute("SELECT * FROM users WHERE username = ?", (target_username,)).fetchone()
    if not target_user:
        conn.close()
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")
    target_user = dict(target_user)

    today = datetime.now().strftime('%Y-%m-%d')
    spent_today = conn.execute(
        "SELECT SUM(amount) as total FROM credit_transactions WHERE username = ? AND type = 'DEBIT' AND date(timestamp) = ?",
        (target_username, today)
    ).fetchone()["total"] or 0

    this_month = datetime.now().strftime('%Y-%m')
    spent_month = conn.execute(
        "SELECT SUM(amount) as total FROM credit_transactions WHERE username = ? AND type = 'DEBIT' AND strftime('%Y-%m', timestamp) = ?",
        (target_username, this_month)
    ).fetchone()["total"] or 0

    chart_data = []
    for i in range(6, -1, -1):
        day = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
        val = conn.execute(
            "SELECT SUM(amount) as total FROM credit_transactions WHERE username = ? AND type = 'DEBIT' AND date(timestamp) = ?",
            (target_username, day)
        ).fetchone()["total"] or 0
        chart_data.append({"date": day, "amount": val})

    conn.close()
    return {
        "spent_today": spent_today,
        "spent_month": spent_month,
        "chart": chart_data,
        "balance": target_user["total_limit"] - target_user["current_usage"],
        "viewing_user": target_username
    }

@app.get("/credits/stats")
def get_stats(user: dict = Depends(get_current_user)):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    
    # Agrupamentos por período para o Dashboard
    # Dia Atual
    today = datetime.now().strftime('%Y-%m-%d')
    spent_today = conn.execute(
        "SELECT SUM(amount) as total FROM credit_transactions WHERE username = ? AND type = 'DEBIT' AND date(timestamp) = ?",
        (user["username"], today)
    ).fetchone()["total"] or 0
    
    # Mes Atual
    this_month = datetime.now().strftime('%Y-%m')
    spent_month = conn.execute(
        "SELECT SUM(amount) as total FROM credit_transactions WHERE username = ? AND type = 'DEBIT' AND strftime('%Y-%m', timestamp) = ?",
        (user["username"], this_month)
    ).fetchone()["total"] or 0
    
    # Histórico p/ Gráfico (Últimos 7 dias)
    chart_data = []
    for i in range(6, -1, -1):
        day = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
        val = conn.execute(
            "SELECT SUM(amount) as total FROM credit_transactions WHERE username = ? AND type = 'DEBIT' AND date(timestamp) = ?",
            (user["username"], day)
        ).fetchone()["total"] or 0
        chart_data.append({"date": day, "amount": val})
        
    conn.close()
    return {
        "spent_today": spent_today,
        "spent_month": spent_month,
        "chart": chart_data,
        "balance": user["total_limit"] - user["current_usage"]
    }

@app.post("/admin/users")
def create_user(data: dict, user: dict = Depends(get_current_user)):
    if user["role"] != "ADMIN": raise HTTPException(status_code=403)
    conn = sqlite3.connect(DB_PATH)
    try:
        cols = ", ".join(data.keys())
        placeholders = ", ".join(["?"] * len(data))
        conn.execute(f"INSERT INTO users ({cols}) VALUES ({placeholders})", list(data.values()))
        conn.commit()
    except Exception as e:
        conn.close()
        raise HTTPException(status_code=400, detail=str(e))
    conn.close()
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    import uuid
    uvicorn.run(app, host="0.0.0.0", port=8000)
