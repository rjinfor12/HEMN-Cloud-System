from fastapi import FastAPI, HTTPException, Depends, Header, Request, UploadFile, File, BackgroundTasks, APIRouter, Response
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
from dotenv import load_dotenv
from passlib.context import CryptContext

# Load environment variables
load_dotenv()

SYSTEM_VERSION = "v2.2.0-PREMIUM" # Single source of truth
SECRET_KEY = os.getenv("SECRET_KEY", "HEMN_SECRET_SUPER_SAFE_123")
ALGORITHM = "HS256"
# Security: Password Hashing (Robust PBKDF2 to avoid OS-level issues with bcrypt)
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

# Importações customizadas
import cloud_engine
print(f"[DEBUG] cloud_engine file: {cloud_engine.__file__}")
from cloud_engine import CloudEngine

app = FastAPI(title="HEMN Web Suite API")
router = APIRouter()

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

@app.get("/version")
async def get_system_version():
    return {"version": SYSTEM_VERSION}

@app.get("/")
async def read_index_landing():
    return FileResponse(os.path.join(APP_DIR, "index.html"))

# Static Mounts
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
app.mount("/areadocliente/static", StaticFiles(directory=STATIC_DIR), name="static_prefixed")

@router.get("/")
@router.get("/index.html")
async def read_index(request: Request):
    # Prefer index_vps.html in root, then static
    root_vps = os.path.join(APP_DIR, "index_vps.html")
    if os.path.exists(root_vps):
        return FileResponse(root_vps)
    
    static_vps = os.path.join(STATIC_DIR, "index_vps.html")
    if os.path.exists(static_vps):
        return FileResponse(static_vps)
        
    return FileResponse(os.path.join(APP_DIR, "index.html"))

@router.get("/admin/monitor")
async def read_monitor():
    root_vps = os.path.join(APP_DIR, "admin_monitor_vps.html")
    if os.path.exists(root_vps):
        return FileResponse(root_vps)
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
    sem_governo: Optional[bool] = False
    cep_file: Optional[str] = None
    filtrar_ddd_regiao: Optional[bool] = False
    operadora_inc: Optional[str] = "TODAS"
    operadora_exc: Optional[str] = "NENHUMA"
    perfil: Optional[str] = "TODOS"
    filterSummary: Optional[str] = None

class UnifyRequest(BaseModel):
    file_ids: List[str]

class EnrichRequest(BaseModel):
    file_id: Optional[str] = None
    name_col: Optional[str] = None
    cpf_col: Optional[str] = None
    manual: Optional[bool] = False
    name: Optional[str] = None
    cpf: Optional[str] = None
    cnpj: Optional[str] = None
    phone: Optional[str] = None
    perfil: Optional[str] = "TODOS"


class CarrierRequest(BaseModel):
    file_id: str
    phone_col: str


class LeadSearchRequest(BaseModel):
    search_type: str # 'cpf', 'nome', 'telefone'
    search_term: str
    scope: str # 'ESTADO', 'REGIAO', 'BRASIL'
    uf: Optional[str] = None
    regiao_nome: Optional[str] = None

class MultiFileRequest(BaseModel):
    file_ids: List[str]
    filterSummary: Optional[str] = None

# --- AUTH HELPERS ---
def verify_password(plain_password, hashed_password):
    try:
        # PBKDF2 is robust and avoids the 72-char limit or handler init issues
        return pwd_context.verify(str(plain_password), hashed_password)
    except Exception as e:
        print(f"[AUTH] Error verifying password: {e}")
        # Fallback for plain text if migration is in progress
        return plain_password == hashed_password

def get_password_hash(password):
    return pwd_context.hash(str(password))

def create_token(username: str):
    expire = datetime.utcnow() + timedelta(hours=24)
    return jwt.encode({"sub": username, "exp": expire}, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(authorization: str = Header(None), token: Optional[str] = None):
    auth_token = None
    if authorization and authorization.startswith("Bearer "):
        auth_token = authorization.split(" ")[1]
    elif token:
        auth_token = token
        
    if not auth_token:
        raise HTTPException(status_code=401, detail="Não autorizado")
        
    try:
        payload = jwt.decode(auth_token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        conn = sqlite3.connect(DB_PATH, timeout=30)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.row_factory = sqlite3.Row
        user = conn.execute("SELECT * FROM users WHERE username = ? COLLATE NOCASE", (username,)).fetchone()
        conn.close()
        if not user: raise HTTPException(status_code=401)
        return dict(user)
    except:
        raise HTTPException(status_code=401, detail="Sessão expirada")

def check_clinicas_access(user: dict = Depends(get_current_user)):
    if user["role"] not in ["ADMIN", "CLINICAS"]:
        raise HTTPException(status_code=403, detail="Acesso restrito ao perfil Cl\u00ednicas ou Administrador")
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

@router.post("/upload")
async def upload_file(file: UploadFile = File(...), user: dict = Depends(get_current_user)):
    file_id = f"{uuid.uuid4()}_{file.filename}"
    file_path = os.path.join(UPLOAD_DIR, file_id)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return {"file_id": file_id, "filename": file.filename}

@router.get("/download/{task_id}")
async def download_result(task_id: str, user: dict = Depends(get_current_user)):
    task = engine.get_task_status(task_id)
    if task["status"] != "COMPLETED":
        raise HTTPException(status_code=400, detail="Arquivo ainda n\u00e3o est\u00e1 pronto.")
    
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
        # Descontar créditos se não for limit >= 9 Mi ou perfil MAYK
        if user["total_limit"] < 9000000 and user["role"] != "MAYK":
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

@router.get("/download-direct/{task_id}")
async def download_direct(task_id: str, user: dict = Depends(get_current_user)):
    """Versão do download projetada para window.location.href (browser direto com token na URL)"""
    task = engine.get_task_status(task_id)
    if not task or task.get("status") == "NOT_FOUND":
        raise HTTPException(status_code=404, detail="Tarefa não encontrada")
        
    if task["status"] != "COMPLETED" or not task.get("result_file"):
        raise HTTPException(status_code=400, detail="Arquivo ainda não está pronto.")
    
    count = task.get("record_count", 0)
    
    # Conferir se já foi pago
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.execute("PRAGMA journal_mode=WAL")
    already_paid = conn.execute(
        "SELECT 1 FROM credit_transactions WHERE username = ? AND task_id = ? AND type = 'DEBIT'",
        (user["username"], task_id)
    ).fetchone()
    conn.close()

    if not already_paid:
        # Descontar créditos se não for limit >= 9 Mi ou perfil MAYK
        if user["total_limit"] < 9000000 and user["role"] != "MAYK":
            available = user["total_limit"] - user["current_usage"]
            if available < count:
                raise HTTPException(status_code=403, detail=f"Saldo insuficiente ({available:,.0f} Cr)")
                
            conn = sqlite3.connect(DB_PATH, timeout=30)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("UPDATE users SET current_usage = current_usage + ? WHERE username = ?", (count, user["username"]))
            conn.commit()
            conn.close()

        # Logar transação
        module = task.get("module", "DOWNLOAD")
        log_transaction(
            user["username"], 
            "DEBIT", 
            count, 
            module, 
            f"Download Direct: {count:,} registros",
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

@router.get("/tasks/{task_id}")
def get_task(task_id: str, user: dict = Depends(get_current_user)):
    status_data = engine.get_task_status(task_id)
    # The ultimate JSON-safe sanitizer: serialize to string and back to dict
    clean_json_str = json.dumps(status_data, cls=NpEncoder)
    return json.loads(clean_json_str)

@router.post("/tasks/unify")
def start_unify(req: UnifyRequest, user: dict = Depends(get_current_user)):
    paths = [os.path.join(UPLOAD_DIR, fid) for fid in req.file_ids]
    tid = engine.start_unify(paths, RESULT_DIR, username=user["username"])
    return {"task_id": tid}

@router.post("/leads/search")
def search_leads(req: LeadSearchRequest, user: dict = Depends(check_clinicas_access)):
    # Limpeza básica do termo
    term = req.search_term.strip()
    if not term:
        raise HTTPException(status_code=400, detail="Termo de pesquisa \u00e9 obrigat\u00f3rio")
    
    # Validação de escopo
    if req.scope == 'ESTADO' and not req.uf:
        raise HTTPException(status_code=400, detail="UF \u00e9 obrigat\u00f3ria para pesquisa por estado")
    if req.scope == 'REGIAO' and not req.regiao_nome:
        raise HTTPException(status_code=400, detail="Nome da regi\u00e3o \u00e9 obrigat\u00f3rio")

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

@router.post("/tasks/enrich")
def start_enrich(req: EnrichRequest, user: dict = Depends(get_current_user)):
    if req.manual:
        # Limpeza básica do CPF
        cpf_clean = ''.join(filter(str.isdigit, str(req.cpf or "")))
        cnpj_clean = ''.join(filter(str.isdigit, str(req.cnpj or "")))
        phone_clean = ''.join(filter(str.isdigit, str(req.phone or "")))
        
        res = engine.deep_search(req.name, cpf_clean, cnpj=cnpj_clean, phone=phone_clean)
        
        # Débito de Consulta Manual se não for ilimitado ou MAYK
        if user["total_limit"] < 9000000 and user["role"] != "MAYK":
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
    
    # Otimização v1.9.0: Trava de Concorrência
    if user["role"] != "ADMIN" and engine.count_active_tasks(user["username"]) > 0:
        raise HTTPException(status_code=403, detail="Voc\u00ea j\u00e1 possui uma pesquisa em andamento. Aguarde a conclus\u00e3o ou cancele-a antes de iniciar outra.")

    path = os.path.join(UPLOAD_DIR, req.file_id)
    print(f"[DEBUG] /tasks/enrich - File: {req.file_id}, Perfil: {req.perfil}, User: {user['username']}")
    tid = engine.start_enrich(path, RESULT_DIR, req.name_col, req.cpf_col, username=user["username"], perfil=req.perfil)
    # Logar início de processamento
    log_transaction(user["username"], "CREDIT", 0, "ENRICH", f"Iniciado processamento em lote: {req.file_id}")
    return {"task_id": tid}

@router.post("/tasks/extract")
def start_extract(filters: ExtractionFilter, user: dict = Depends(get_current_user)):
    # Otimização v1.9.0: Trava de Concorrência
    if user["role"] != "ADMIN" and engine.count_active_tasks(user["username"]) > 0:
        raise HTTPException(status_code=403, detail="Você já possui uma extração em andamento. Aguarde a conclusão ou cancele-a antes de iniciar outra.")

    # Logar início de extração
    log_transaction(user["username"], "CREDIT", 0, "EXTRACT", f"Iniciada extração de dados: {filters.uf} - {filters.cidade}")
    
    f_dict = filters.dict()
    if f_dict.get("cep_file"):
        f_dict["cep_file"] = os.path.join(UPLOAD_DIR, f_dict["cep_file"])
        print(f"[DEBUG] start_extract: resolved cep_file to {f_dict['cep_file']}")
        
    tid = engine.start_extraction(f_dict, RESULT_DIR, username=user["username"])
    # Notificar o motor das mudanças (Force update)
    print(f"[EXTRACT] Iniciando com filtros: {f_dict}")
    return {"task_id": tid}

@router.post("/tasks/carrier")
def start_carrier(req: CarrierRequest, user: dict = Depends(get_current_user)):
    # Otimização v1.9.0: Trava de Concorrência
    if user["role"] != "ADMIN" and engine.count_active_tasks(user["username"]) > 0:
        raise HTTPException(status_code=403, detail="Você já possui uma consulta de operadoras em andamento.")

    path = os.path.join(UPLOAD_DIR, req.file_id)
    tid = engine.batch_carrier(path, RESULT_DIR, req.phone_col, username=user["username"])
    # Logar início de processamento
    log_transaction(user["username"], "CREDIT", 0, "CARRIER", f"Iniciada consulta de operadoras em lote")
    return {"task_id": tid}

@router.get("/tasks/carrier/single")
def get_single_carrier(phone: str, user: dict = Depends(get_current_user)):
    # Débito de Consulta de Operadora se não for ilimitado ou MAYK
    if user["total_limit"] < 9000000 and user["role"] != "MAYK":
        conn = sqlite3.connect(DB_PATH, timeout=30)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("UPDATE users SET current_usage = current_usage + 0.1 WHERE username = ?", (user["username"],))
        conn.commit()
        conn.close()

    # Logar transação SEMPRE
    log_transaction(user["username"], "DEBIT", 0.1, "CARRIER", f"Portabilidade Individual: {phone}")
        
    return engine.get_single_carrier(phone)


# --- INTELIGÊNCIA COMERCIAL (MAPA) ---

@router.get("/tasks/intelligence/map-leads")
async def get_map_leads(sw_lat: float, sw_lng: float, ne_lat: float, ne_lng: float, user: dict = Depends(get_current_user)):
    return engine.get_map_leads(sw_lat, sw_lng, ne_lat, ne_lng)

@router.get("/tasks/intelligence/map-coverage")
async def get_map_coverage(sw_lat: float, sw_lng: float, ne_lat: float, ne_lng: float, user: dict = Depends(get_current_user)):
    return engine.get_map_coverage(sw_lat, sw_lng, ne_lat, ne_lng)

@router.post("/tasks/intelligence/export-view")
async def start_intelligence_export(sw_lat: float, sw_lng: float, ne_lat: float, ne_lng: float, user: dict = Depends(get_current_user)):
    tid = engine.start_intelligence_export(sw_lat, sw_lng, ne_lat, ne_lng, RESULT_DIR, username=user["username"])
    # Logar início de exportação
    log_transaction(user["username"], "CREDIT", 0, "INTELLIGENCE", f"Iniciada exportação geográfica da visão do mapa")
    return {"task_id": tid}

@router.post("/tasks/intelligence/ingest")
async def start_intelligence_ingest(req: MultiFileRequest, user: dict = Depends(get_current_user)):
    # Mapear IDs para caminhos reais
    paths = []
    for fid in req.file_ids:
        # Se for um arquivo de sync local (id == name), procurar em results
        if os.path.exists(os.path.join(RESULT_DIR, fid)):
            paths.append(os.path.join(RESULT_DIR, fid))
        else:
            paths.append(os.path.join(UPLOAD_DIR, fid))
            
    tid = engine.ingest_intelligence_coverage(paths, username=user["username"])
    # Logar início de ingestão
    log_transaction(user["username"], "CREDIT", 0, "INTELLIGENCE", f"Iniciada ingestão permanente de cobertura ({len(paths)} arquivos)")
    return {"task_id": tid}

@router.post("/admin/geo/sync-local")
async def sync_local_geo(user: dict = Depends(get_current_user)):
    if user["role"] != "ADMIN": raise HTTPException(status_code=403)
    files = engine.list_local_results(RESULT_DIR)
    return {"status": "ok", "files": files}

@router.get("/tasks/state/active")
@router.get("/tasks/active")
def get_active_tasks(response: Response, user: dict = Depends(get_current_user)):
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, post-check=0, pre-check=0"
    response.headers["Pragma"] = "no-cache"
    # Incluir tarefas concluídas recentemente para o frontend pegar o download_url
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.row_factory = sqlite3.Row
    tasks = conn.execute(
        "SELECT * FROM background_tasks WHERE username = ? COLLATE NOCASE AND (status IN ('QUEUED', 'PROCESSING') OR (status IN ('COMPLETED', 'FAILED') AND created_at > datetime('now','-5 hours'))) ORDER BY created_at DESC",
        (user["username"],)
    ).fetchall()
    conn.close()
    return [dict(t) for t in tasks]

@router.get("/tasks/{task_id}")
def get_task_status(task_id: str, response: Response, user: dict = Depends(get_current_user)):
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
    # Simple status check for specific ID
    status = engine.get_task_status(task_id)
    if not status or status.get("username") != user["username"] and user["role"] != "ADMIN":
        return {"status": "NOT_FOUND"}
    return status

@router.post("/tasks/{task_id}/cancel")
def cancel_task(task_id: str, user: dict = Depends(get_current_user)):
    # Verify ownership
    status = engine.get_task_status(task_id)
    if status.get("username") != user["username"] and user["role"] != "ADMIN":
        raise HTTPException(status_code=403, detail="Não autorizado a cancelar esta tarefa.")
    success = engine.cancel_task(task_id)
    return {"status": "ok" if success else "error"}

# --- AUTH & ADMIN (LEGACY COMPAT) ---

@router.post("/login")
async def login(request: Request):
    try:
        data = await request.form()
    except:
        data = await request.json()

    u, p = data.get("username"), data.get("password")
    if not u or not p:
        raise HTTPException(status_code=400, detail="Nome de usuário e senha são obrigatórios.")

    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.row_factory = sqlite3.Row
    user = conn.execute("SELECT * FROM users WHERE username = ? COLLATE NOCASE", (u,)).fetchone()

    is_correct = False
    if user:
        stored_password = user["password"]
        if verify_password(p, stored_password):
            is_correct = True
            # Migration check: if not already pbkdf2_sha256, migrate it
            # (In this context, if the verify works but it wasn't hashed with the current scheme)
            if not stored_password.startswith("$pbkdf2-sha256$"):
                new_hash = get_password_hash(p)
                conn.execute("UPDATE users SET password = ? WHERE username = ? COLLATE NOCASE", (new_hash, u))
                conn.commit()

    if is_correct:
        if user["status"] != "ACTIVE":
            conn.close()
            raise HTTPException(status_code=403, detail="Acesso bloqueado.")
        token = create_token(u)
        conn.execute("UPDATE users SET last_login = ? WHERE username = ? COLLATE NOCASE", (datetime.now().isoformat(), u))
        conn.commit()
        conn.close()
        return {"access_token": token, "token_type": "bearer"}

    conn.close()
    raise HTTPException(status_code=401, detail="Usuário ou senha incorretos.")

@router.get("/me")
def get_me(user: dict = Depends(get_current_user)):
    user_data = dict(user)
    user_data["system_version"] = SYSTEM_VERSION
    return user_data

@router.get("/me/db_version")
def get_db_version(user: dict = Depends(get_current_user)):
    # Remove restriction to allow all users to see the base date in the UI
    return {"version": engine.get_db_version()}

@router.get("/admin/users")
def list_users(user: dict = Depends(get_current_user)):
    if user["role"] != "ADMIN": 
        raise HTTPException(status_code=403, detail="Acesso restrito.")
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.row_factory = sqlite3.Row
    users = conn.execute("SELECT * FROM users").fetchall()
    conn.close()
    return [dict(u) for u in users]

@router.get("/admin/monitor/stats")
async def get_monitor_stats(user: dict = Depends(get_current_user)):
    if user["role"] != "ADMIN": raise HTTPException(status_code=403)
    return engine.get_monitor_stats()

@router.get("/admin/monitor/carrier-status")
async def get_carrier_status(user: dict = Depends(get_current_user)):
    if user["role"] != "ADMIN": raise HTTPException(status_code=403)
    return engine.get_carrier_status()

@router.post("/admin/monitor/update-carrier")
async def start_carrier_update(user: dict = Depends(get_current_user)):
    if user["role"] != "ADMIN": raise HTTPException(status_code=403)
    tid = engine.start_carrier_update(user["username"])
    return {"status": "ok", "task_id": tid}

@router.post("/admin/monitor/update-receita")
async def start_receita_update(user: dict = Depends(get_current_user)):
    if user["role"] != "ADMIN": raise HTTPException(status_code=403)
    
    tid = str(uuid.uuid4())[:8]
    # Create the task in DB first so the UI sees it immediately
    import sqlite3
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute(
        "INSERT INTO background_tasks (id, username, module, status, progress, message, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (tid, user["username"], "DATABASE_UPDATE", "PROCESSING", 0, "Iniciando orquestrador de atualização...", datetime.utcnow().isoformat() + "Z")
    )
    conn.commit()
    conn.close()

    # Determine paths
    orchestrator = os.path.join(APP_DIR, "data_analysis", "vps_receita_orchestrator.py")
    python_bin = os.path.join(APP_DIR, "venv", "bin", "python")
    if not os.path.exists(python_bin):
        python_bin = sys.executable # Fallback

    # Orchestrator might be in the root if it was copied there during deployment
    if not os.path.exists(orchestrator):
        orchestrator = os.path.join(APP_DIR, "vps_receita_orchestrator.py")

    # Trigger orchestrator
    import subprocess
    cmd = [python_bin, orchestrator, "--force", "--task_id", tid]
    subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, cwd=APP_DIR)
    
    return {"status": "ok", "task_id": tid}

@router.post("/admin/tasks/cleanup")
async def cleanup_tasks(user: dict = Depends(get_current_user)):
    if user["role"] != "ADMIN": raise HTTPException(status_code=403)
    success = engine.cleanup_all_tasks()
    return {"status": "ok" if success else "error"}

@router.get("/admin/monitor/stats_legacy")
def get_monitor_stats_legacy(user: dict = Depends(get_current_user)):
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
        "system_version": SYSTEM_VERSION,
        "system": sys_stats,
        "engine": engine_stats,
        "clickhouse": ch_stats,
        "recent_activities": engine_stats.get("recent_activities", []),
        "timestamp": datetime.now().isoformat()
    }

@router.get("/admin/debug/tasks")
def debug_tasks(user: dict = Depends(get_current_user)):
    if user["role"] != "ADMIN": raise HTTPException(status_code=403)
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.row_factory = sqlite3.Row
    tasks = conn.execute("SELECT * FROM background_tasks ORDER BY created_at DESC LIMIT 20").fetchall()
    conn.close()
    
    logs = []
    if os.path.exists("cloud_engine_debug.log"):
        try:
            with open("cloud_engine_debug.log", "r") as f:
                logs = f.readlines()[-50:]
        except:
            pass
            
    return {
        "database_tasks": [dict(t) for t in tasks],
        "engine_logs": logs
    }

@router.put("/admin/users/{username}")
def update_user(username: str, data: dict, user: dict = Depends(get_current_user)):
    if user["role"] != "ADMIN": raise HTTPException(status_code=403)
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.row_factory = sqlite3.Row
    old_user = conn.execute("SELECT * FROM users WHERE username = ? COLLATE NOCASE", (username,)).fetchone()
    
    if not old_user:
        conn.close()
        raise HTTPException(status_code=404, detail="Usu\u00e1rio n\u00e3o encontrado")
    
    if data:
        fields = []
        values = []
        for k, v in data.items():
            if k == "password" and v:
                v = get_password_hash(v)
            fields.append(f"{k} = ?")
            values.append(v)
        
        values.append(username)
        query = f"UPDATE users SET {', '.join(fields)} WHERE username = ? COLLATE NOCASE"
        
        try:
            conn.execute(query, values)
            conn.commit()
        except Exception as e:
            conn.rollback()
            conn.close()
            raise HTTPException(status_code=500, detail=f"Erro ao atualizar banco: {e}")
    
    # Se o limite aumentou, logar como crédito/recarga
    if "total_limit" in data and old_user:
        diff = float(data["total_limit"]) - float(old_user["total_limit"])
        if diff > 0:
            log_transaction(username, "CREDIT", diff, "ADMIN", f"Recarga de créditos via Administrador")
            
    conn.commit()
    conn.close()
    return {"status": "ok"}

@router.get("/credits/statement")
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

@router.get("/admin/statement/{target_username}")
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

@router.get("/admin/stats/{target_username}")
def get_user_stats(target_username: str, user: dict = Depends(get_current_user)):
    if user["role"] != "ADMIN":
        raise HTTPException(status_code=403, detail="Acesso restrito a administradores.")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    target_user = conn.execute("SELECT * FROM users WHERE username = ? COLLATE NOCASE", (target_username,)).fetchone()
    if not target_user:
        conn.close()
        raise HTTPException(status_code=404, detail="Usu\u00e1rio n\u00e3o encontrado.")
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
        "total_limit": target_user["total_limit"],
        "current_usage": target_user["current_usage"],
        "vencimento_dia": target_user.get("vencimento_dia"),
        "valor_mensal": target_user.get("valor_mensal"),
        "role": target_user.get("role"),
        "viewing_user": target_username
    }

@router.get("/credits/stats")
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
        "balance": user["total_limit"] - user["current_usage"],
        "total_limit": user["total_limit"],
        "current_usage": user["current_usage"],
        "vencimento_dia": user.get("vencimento_dia"),
        "valor_mensal": user.get("valor_mensal")
    }

@router.post("/admin/users")
def create_user(data: dict, user: dict = Depends(get_current_user)):
    if user["role"] != "ADMIN": raise HTTPException(status_code=403)
    conn = sqlite3.connect(DB_PATH)
    try:
        if "password" in data:
            data["password"] = get_password_hash(data["password"])
        cols = ", ".join(data.keys())
        placeholders = ", ".join(["?"] * len(data))
        conn.execute(f"INSERT INTO users ({cols}) VALUES ({placeholders})", list(data.values()))
        conn.commit()
    except Exception as e:
        conn.close()
        raise HTTPException(status_code=400, detail=str(e))
    conn.close()
    return {"status": "ok"}

# Include Router
app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    import uuid
    uvicorn.run(app, host="0.0.0.0", port=8000)
