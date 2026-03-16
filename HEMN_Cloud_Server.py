from fastapi import FastAPI, HTTPException, Depends, Header, Request, UploadFile, File, BackgroundTasks, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field
import requests
import sys
import sqlite3
import os
import jwt
from datetime import datetime, timedelta
from typing import Optional, List
import shutil
import uuid

# Importa├º├Áes customizadas
import cloud_engine
print(f"[DEBUG] cloud_engine file: {cloud_engine.__file__}")
from cloud_engine import CloudEngine
import json
import numpy as np

class NpEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer): return int(obj)
        if isinstance(obj, np.floating): return float(obj)
        if isinstance(obj, np.ndarray): return obj.tolist()
        return super(NpEncoder, self).default(obj)

app = FastAPI(title="HEMN Web Suite API")
router = APIRouter(prefix="/areadocliente")

class LeadSearchRequest(BaseModel):
    search_type: str # 'cpf', 'nome', 'telefone'
    search_term: str
    scope: str # 'ESTADO', 'REGIAO', 'BRASIL'
    uf: Optional[str] = None
    regiao_nome: Optional[str] = None

class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str
    confirm_password: str

# ASAAS Config
ASAAS_API_KEY = "$aact_prod_000MzkwODA2MWY2OGM3MWRlMDU2NWM3MzJlNzZmNGZhZGY6OjEzMDJlNTFjLTgwODgtNGRmNi1iZTA3LWVkYmE0YzI5Y2UwYzo6JGFhY2hfODExNDEyNmEtZWI2Yy00OGFlLWI4OTktZjYyZjljMDdkNmIw"
ASAAS_URL = "https://www.asaas.com/api/v3"

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

# Priorizar pasta est├ítica local se existir (permite atualiza├º├Áes sem recompilar)
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
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))

@app.get("/areadocliente")
@app.get("/areadocliente/")
@app.get("/areadoclieente")      # Suporte ao erro de digitação comum
@app.get("/areadoclieente/")     # Suporte ao erro de digitação comum
async def read_index_prefixed():
    # Prioritize index_vps.html for production parity
    vps_path = os.path.join(APP_DIR, "index_vps.html")
    if os.path.exists(vps_path):
        return FileResponse(vps_path)
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))

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


# Inicializar Engine com deteco de ambiente
import platform
is_linux = (platform.system() == 'Linux')

if is_linux:
    # Caminhos do VPS / Linux
    engine = CloudEngine(
        db_cnpj_path="/var/www/hemn_cloud/cnpj.db",
        db_carrier_path="/var/www/hemn_cloud/hemn_carrier.db"
    )
else:
    # Caminhos Locais / Windows
    engine = CloudEngine(
        db_cnpj_path=r"C:\HEMN_SYSTEM_DB\cnpj.db",
        db_carrier_path=r"C:\HEMN_SYSTEM_DB\hemn_carrier.db"
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
    operadora_inc: Optional[str] = "TODAS"
    operadora_exc: Optional[str] = "NENHUMA"
    perfil: Optional[str] = "TODOS"

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

# --- ASAAS MODELS ---
class CreditCardModel(BaseModel):
    holderName: str
    number: str
    expiryMonth: str
    expiryYear: str
    ccv: str

class CardHolderModel(BaseModel):
    name: str
    email: str
    cpfCnpj: str
    postalCode: str
    addressNumber: str
    phone: str

class PaymentCreateRequest(BaseModel):
    amount: float
    billingType: str  # 'PIX' ou 'CREDIT_CARD'
    cpfCnpj: Optional[str] = None
    creditCard: Optional[CreditCardModel] = None
    creditCardHolder: Optional[CardHolderModel] = None


# --- AUTH HELPERS ---
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
        conn = sqlite3.connect(DB_PATH, timeout=30)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute(
            "INSERT INTO credit_transactions (username, type, amount, module, description, task_id, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (username, type, amount, module, description, task_id, now_br)
        )
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"CRITICAL: Erro ao logar transação: {e}")
        traceback.print_exc()

# --- ASAAS ENDPOINTS ---
@router.post("/payments/create")
async def create_payment_endpoint(req: PaymentCreateRequest, user: dict = Depends(get_current_user)):
    h = {"access_token": ASAAS_API_KEY, "Content-Type": "application/json"}
    
    payload = {
        "customer": None, # Will find or create
        "billingType": req.billingType,
        "value": req.amount,
        "dueDate": (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d"),
        "description": f"Recarga de créditos - {user['username']}",
        "externalReference": user["username"]
    }

    # Procura cliente pelo CPF/CNPJ ou Email
    cpf = req.cpfCnpj or (req.creditCardHolder.cpfCnpj if req.creditCardHolder else None)
    email = req.creditCardHolder.email if req.creditCardHolder else f"{user['username']}@hemn.com.br"
    
    cust_res = requests.get(f"{ASAAS_URL}/customers?cpfCnpj={cpf}", headers=h).json()
    if cust_res.get("data"):
        customer_id = cust_res["data"][0]["id"]
    else:
        new_cust = requests.post(f"{ASAAS_URL}/customers", headers=h, json={
            "name": user["username"],
            "cpfCnpj": cpf,
            "email": email
        }).json()
        customer_id = new_cust.get("id")
    
    if not customer_id:
        raise HTTPException(status_code=400, detail="Erro ao processar cliente no ASAAS")
        
    payload["customer"] = customer_id
    
    if req.billingType == "CREDIT_CARD":
        if not req.creditCard or not req.creditCardHolder:
            raise HTTPException(status_code=400, detail="Dados do cartão ausentes")
        payload["creditCard"] = req.creditCard.dict()
        payload["creditCardHolderInfo"] = req.creditCardHolder.dict()
        payload["remoteIp"] = "127.0.0.1" 

    res = requests.post(f"{ASAAS_URL}/payments", headers=h, json=payload).json()
    if "id" not in res:
        raise HTTPException(status_code=400, detail=str(res.get("errors", "Erro desconhecido")))

    pay_id = res["id"]
    pix_data = {"pix_payload": None, "pix_image_base64": None}
    
    if req.billingType == "PIX":
        pix_res = requests.get(f"{ASAAS_URL}/payments/{pay_id}/pixQrCode", headers=h).json()
        pix_data["pix_payload"] = pix_res.get("payload")
        pix_data["pix_image_base64"] = pix_res.get("encodedImage")

    # Salva no banco local
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("""
        INSERT INTO asaas_payments (id, username, amount, credits, status, pix_payload, pix_image_base64)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (pay_id, user["username"], req.amount, req.amount * 100, "PENDING", pix_data["pix_payload"], pix_data["pix_image_base64"]))
    conn.commit()
    conn.close()

    return {
        "payment_id": pay_id,
        "status": res.get("status"),
        "pix_payload": pix_data["pix_payload"],
        "pix_image_base64": pix_data["pix_image_base64"]
    }

@router.post("/webhook/asaas")
async def asaas_webhook(request: Request):
    data = await request.json()
    event = data.get("event")
    payment = data.get("payment", {})
    pay_id = payment.get("id")
    
    log_msg = f"[{datetime.now()}] Webhook {event} para {pay_id}\n"
    with open(os.path.join(APP_DIR, "webhook_asaas.log"), "a") as f:
        f.write(log_msg)

    if event in ["PAYMENT_RECEIVED", "PAYMENT_CONFIRMED"]:
        conn = sqlite3.connect(DB_PATH, timeout=30)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.row_factory = sqlite3.Row
        local_pay = conn.execute("SELECT * FROM asaas_payments WHERE id = ?", (pay_id,)).fetchone()
        
        if local_pay and local_pay["status"] == "PENDING":
            username = local_pay["username"]
            credits = local_pay["credits"]
            
            # Update user balance
            conn.execute("UPDATE users SET total_limit = total_limit + ? WHERE username = ?", (credits, username))
            conn.execute("UPDATE asaas_payments SET status = 'RECEIVED', confirmed_at = ? WHERE id = ?", (datetime.now().isoformat(), pay_id))
            
            # Log transaction
            now_br = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            conn.execute(
                "INSERT INTO credit_transactions (username, type, amount, module, description, timestamp) VALUES (?, ?, ?, ?, ?, ?)",
                (username, "CREDIT", credits, "ASAAS", f"Recarga confirmada via {payment.get('billingType')}", now_br)
            )
            conn.commit()
            print(f"[ASAAS] Pagamento {pay_id} processado com sucesso para {username}")
        conn.close()
        
    return {"status": "ok"}

@router.post("/leads/search")
def search_leads_endpoint(req: LeadSearchRequest, user: dict = Depends(check_clinicas_access)):
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
@router.post("/upload")
async def upload_file(file: UploadFile = File(...), user: dict = Depends(get_current_user)):
    file_id = f"{uuid.uuid4()}_{file.filename}"
    file_path = os.path.join(UPLOAD_DIR, file_id)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return {"file_id": file_id, "filename": file.filename}

@app.get("/download/{task_id}")
@router.get("/download/{task_id}")
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

    module = task.get("module", "DOWNLOAD")
    if not already_paid and module not in ["SPLIT", "UNIFY"]:
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

@app.get("/download-direct/{task_id}")
@router.get("/download-direct/{task_id}")
def download_direct(task_id: str, user: dict = Depends(get_current_user)):
    """Versão do download projetada para window.location.href (browser direto)"""
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.row_factory = sqlite3.Row
    task = conn.execute("SELECT * FROM background_tasks WHERE id = ?", (task_id,)).fetchone()
    
    if not task:
        conn.close()
        raise HTTPException(status_code=404, detail="Tarefa não encontrada")

    if task["status"] != "COMPLETED" or not task["result_file"]:
        conn.close()
        raise HTTPException(status_code=400, detail="Arquivo não disponível para download")

    # Verificar se já foi cobrado
    tx = conn.execute("SELECT * FROM credit_transactions WHERE task_id = ? AND type = 'DEBIT'", (task_id,)).fetchone()
    count = int(task["record_count"] or 0)
    conn.close()

    if not tx:
        # Cobrar créditos se necessário
        if user["total_limit"] < 9000000:
            available = user["total_limit"] - user["current_usage"]
            if available < count:
                raise HTTPException(status_code=403, detail=f"Saldo insuficiente ({available:,.0f} Cr)")
            
            conn = sqlite3.connect(DB_PATH, timeout=30)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("UPDATE users SET current_usage = current_usage + ? WHERE username = ?", (count, user["username"]))
            conn.commit()
            conn.close()

        log_transaction(
            user["username"], 
            "DEBIT", 
            count, 
            task["module"] or "DOWNLOAD", 
            f"Download Direct: {count:,} registros",
            task_id=task_id
        )
    
    return FileResponse(task["result_file"], filename=os.path.basename(task["result_file"]))

# --- ENDPOINTS DE TAREFAS (HEMN SUITE) ---

@app.get("/tasks/{task_id}")
@router.get("/tasks/{task_id}")
def get_task(task_id: str, user: dict = Depends(get_current_user)):
    status_data = engine.get_task_status(task_id)
    # The ultimate JSON-safe sanitizer
    return JSONResponse(status_data)

@app.post("/tasks/unify")
@router.post("/tasks/unify")
def start_unify(req: UnifyRequest, user: dict = Depends(get_current_user)):
    paths = [os.path.join(UPLOAD_DIR, fid) for fid in req.file_ids]
    tid = engine.start_unify(paths, RESULT_DIR, username=user["username"])
    return {"task_id": tid}

@app.post("/tasks/enrich")
@router.post("/tasks/enrich")
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
    return JSONResponse(content={"task_id": tid})

@app.post("/tasks/extract")
@router.post("/tasks/extract")
def start_extract(filters: ExtractionFilter, user: dict = Depends(get_current_user)):
    # Logar início de extração
    log_transaction(user["username"], "CREDIT", 0, "EXTRACT", f"Iniciada extração de dados: {filters.uf} - {filters.cidade}")
    
    # Garantir mapeamento explícito
    f_dict = {
        "uf": filters.uf,
        "cidade": filters.cidade,
        "cnae": filters.cnae,
        "tipo_tel": filters.tipo_tel,
        "situacao": filters.situacao,
        "somente_com_telefone": filters.somente_com_telefone,
        "cep_file": filters.cep_file,
        "operadora_inc": filters.operadora_inc,
        "operadora_exc": filters.operadora_exc,
        "perfil": filters.perfil
    }
    
    tid = engine.start_extraction(f_dict, RESULT_DIR, username=user["username"])
    return JSONResponse(content={"task_id": tid})

@app.post("/tasks/carrier")
@router.post("/tasks/carrier")
def start_carrier(req: CarrierRequest, user: dict = Depends(get_current_user)):
    path = os.path.join(UPLOAD_DIR, req.file_id)
    tid = engine.batch_carrier(path, RESULT_DIR, req.phone_col, username=user["username"])
    # Logar início de processamento
    log_transaction(user["username"], "CREDIT", 0, "CARRIER", f"Iniciada consulta de operadoras em lote")
    return JSONResponse(content={"task_id": tid})

@app.get("/tasks/carrier/single")
@router.get("/tasks/carrier/single")
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
@router.post("/tasks/split")
def start_split(req: SplitRequest, user: dict = Depends(get_current_user)):
    print(f"[API] Recebido pedido de fatiamento: {req.file_id} por {user['username']}")
    path = os.path.join(UPLOAD_DIR, req.file_id)
    tid = engine.start_split(path, RESULT_DIR, username=user["username"])
    print(f"[API] Tarefa de fatiamento criada: {tid}")
    return JSONResponse(content={"task_id": tid})

@app.get("/tasks/active")
@router.get("/tasks/active")
def get_active_tasks(user: dict = Depends(get_current_user)):
    return engine.get_user_tasks(user["username"])

@app.post("/tasks/{task_id}/cancel")
@router.post("/tasks/{task_id}/cancel")
def cancel_task(task_id: str, user: dict = Depends(get_current_user)):
    # Verify ownership
    status = engine.get_task_status(task_id)
    if status.get("username") != user["username"] and user["role"] != "ADMIN":
        raise HTTPException(status_code=403, detail="Não autorizado a cancelar esta tarefa.")
    success = engine.cancel_task(task_id)
    return {"status": "ok" if success else "error"}

# --- AUTH & ADMIN (LEGACY COMPAT) ---

@app.post("/login")
@router.post("/login")
async def login(request: Request):
    try:
        body = await request.body()
        content_type = request.headers.get("Content-Type", "")
        print(f"[DEBUG] Login attempt | Content-Type: {content_type} | Raw Body: {body}")
        
        data = {}
        if "application/json" in content_type:
            data = json.loads(body)
        else:
            import urllib.parse
            data = dict(urllib.parse.parse_qsl(body.decode()))
            
        u = data.get("username")
        p = data.get("password")
        
        print(f"[DEBUG] Parsed credentials: username='{u}' password='{p}'")
    except Exception as e:
        print(f"[ERROR] Fail to parse login data: {e}")
        raise HTTPException(status_code=400, detail="Erro ao processar dados de login")
    
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

@router.post("/user/change-password")
async def change_password(req: PasswordChangeRequest, user: dict = Depends(get_current_user)):
    if req.new_password != req.confirm_password:
        raise HTTPException(status_code=400, detail="A nova senha e a confirmação não coincidem.")
    
    if len(req.new_password) < 4:
        raise HTTPException(status_code=400, detail="A nova senha deve ter pelo menos 4 caracteres.")

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    # Verify current password
    db_user = conn.execute("SELECT * FROM users WHERE username = ? AND password = ?", (user["username"], req.current_password)).fetchone()
    if not db_user:
        conn.close()
        raise HTTPException(status_code=401, detail="Senha atual incorreta.")
    
    # Update password
    conn.execute("UPDATE users SET password = ? WHERE username = ?", (req.new_password, user["username"]))
    conn.commit()
    conn.close()
    return {"status": "success", "message": "Senha alterada com sucesso."}

@app.get("/me")
@router.get("/me")
async def get_me(user: dict = Depends(get_current_user)):
    # Sincronização automática de pagamentos pendentes
    try:
        conn = sqlite3.connect(DB_PATH, timeout=30)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.row_factory = sqlite3.Row
        pendings = conn.execute("SELECT * FROM asaas_payments WHERE username = ? AND status = 'PENDING'", (user["username"],)).fetchall()
        
        if pendings:
            h = {"access_token": ASAAS_API_KEY}
            for p in pendings:
                res = requests.get(f"{ASAAS_URL}/payments/{p['id']}", headers=h).json()
                status = res.get("status")
                if status in ["RECEIVED", "CONFIRMED", "RECEIVED_IN_CASH"]:
                    credits = p["credits"]
                    conn.execute("UPDATE users SET total_limit = total_limit + ? WHERE username = ?", (credits, user["username"]))
                    conn.execute("UPDATE asaas_payments SET status = 'RECEIVED', confirmed_at = ? WHERE id = ?", (datetime.now().isoformat(), p['id']))
                    now_br = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    conn.execute(
                        "INSERT INTO credit_transactions (username, type, amount, module, description, timestamp) VALUES (?, ?, ?, ?, ?, ?)",
                        (user["username"], "CREDIT", credits, "SYNC", f"Sincronização: Recarga confirmada", now_br)
                    )
            conn.commit()
            # Atualizar dados do usuário no retorno
            user = conn.execute("SELECT * FROM users WHERE username = ?", (user["username"],)).fetchone()
            user = dict(user)
        conn.close()
    except Exception as e:
        print(f"[RECHARGE SYNC ERROR] {e}")
        
    return user

@app.get("/admin/users")
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

@app.get("/admin/monitor/stats")
@router.get("/admin/monitor/stats")
def get_monitor_stats(user: dict = Depends(get_current_user)):
    if user["role"] != "ADMIN": 
        raise HTTPException(status_code=403, detail="Acesso restrito a administradores.")
    
    # 1. System Stats (Linux /proc fallback)
    sys_stats = {"cpu": 0, "ram": 0, "disk": 0}
    try:
        # RAM
        if os.path.exists("/proc/meminfo"):
            with open("/proc/meminfo", "r") as f:
                mem_data = {}
                for line in f:
                    parts = line.split()
                    if len(parts) >= 2:
                        mem_data[parts[0].rstrip(':')] = int(parts[1])
                
                total = mem_data.get("MemTotal", 0)
                available = mem_data.get("MemAvailable", mem_data.get("MemFree", 0))
                if total > 0:
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
@router.put("/admin/users/{username}")
def update_user(username: str, data: dict, user: dict = Depends(get_current_user)):
    if user["role"] != "ADMIN": raise HTTPException(status_code=403)
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.row_factory = sqlite3.Row
    old_user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    
    for k, v in data.items():
        conn.execute(f"UPDATE users SET {k} = ? WHERE username = ?", (v, username))
    
    # Se o limite aumentou, logar como cr├®dito/recarga
    if "total_limit" in data and old_user:
        diff = float(data["total_limit"]) - float(old_user["total_limit"])
        if diff > 0:
            log_transaction(username, "CREDIT", diff, "ADMIN", f"Recarga de créditos via Administrador")
            
    conn.commit()
    conn.close()
    return {"status": "ok"}

@router.get("/credits/statement")
def get_statement(days: Optional[int] = None, user: dict = Depends(get_current_user), limit: int = 100):
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.execute("PRAGMA journal_mode=WAL")
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
@router.get("/admin/statement/{target_username}")
def get_user_statement(target_username: str, days: Optional[int] = None, user: dict = Depends(get_current_user), limit: int = 200):
    if user["role"] != "ADMIN":
        raise HTTPException(status_code=403, detail="Acesso restrito a administradores.")
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.execute("PRAGMA journal_mode=WAL")
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
@router.get("/admin/stats/{target_username}")
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
        "balance": user["total_limit"] - user["current_usage"]
    }

@app.post("/admin/users")
@router.post("/admin/users")
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

app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    import uuid
    uvicorn.run(app, host="0.0.0.0", port=8000)
