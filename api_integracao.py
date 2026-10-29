"""API de integração (v1): outros sistemas buscam empresas (PJ) com uma chave de acesso.

Usada pela "Importação inteligente" do discador. Cada chave pertence a um usuário daqui: os créditos e o extrato
são os dele, com as mesmas regras do Extrair Dados (perfis ilimitados não pagam; o mesmo CNPJ não é cobrado de
novo em 30 dias). Vem 1 telefone por empresa (o principal), escolhido como no Extrair Dados.

Rotas (cabeçalho "Authorization: Bearer <chave>"):
  GET  /integracao/v1/situacao          -> usuário e créditos (serve para testar a chave)
  POST /integracao/v1/empresas/contar   -> quantas empresas os filtros acham (estimativa por amostra)
  POST /integracao/v1/empresas/buscar   -> até 5.000 empresas por pedido, sem as de "excluir_cnpjs"
Chaves (login normal do painel, só ADMIN): GET/POST /integracao/chaves e DELETE /integracao/chaves/{id}.
Pelo terminal do servidor: python3 api_integracao.py criar <usuario> [nome] | listar | revogar <id>

Ligar no servidor (depois de app.include_router(router)):
    import api_integracao
    app.include_router(api_integracao.criar_rotas(engine, DB_PATH, get_current_user, log_transaction,
                       _compute_dejavu_overlap, _log_downloaded_cnpjs, _dejavu_skip_for_user))
"""
from __future__ import annotations

import hashlib
import os
import re
import secrets
import sqlite3
import sys
import threading
import time
import unicodedata
from datetime import datetime
from typing import List, Optional

import pandas as pd
from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field

UFS = ("AC", "AL", "AM", "AP", "BA", "CE", "DF", "ES", "GO", "MA", "MG", "MS", "MT", "PA", "PB", "PE", "PI", "PR", "RJ",
       "RN", "RO", "RR", "RS", "SC", "SE", "SP", "TO")
DDD_POR_UF = {
    'AC': ['68'], 'AL': ['82'], 'AM': ['92', '97'], 'AP': ['96'], 'BA': ['71', '73', '74', '75', '77'], 'CE': ['85', '88'],
    'DF': ['61'], 'ES': ['27', '28'], 'GO': ['62', '64'], 'MA': ['98', '99'], 'MG': ['31', '32', '33', '34', '35', '37', '38'],
    'MS': ['67'], 'MT': ['65', '66'], 'PA': ['91', '93', '94'], 'PB': ['83'], 'PE': ['81', '87'], 'PI': ['86', '89'],
    'PR': ['41', '42', '43', '44', '45', '46'], 'RJ': ['21', '22', '24'], 'RN': ['84'], 'RO': ['69'], 'RR': ['95'],
    'RS': ['51', '53', '54', '55'], 'SC': ['47', '48', '49'], 'SE': ['79'], 'SP': ['11', '12', '13', '14', '15', '16', '17', '18', '19'],
    'TO': ['63'],
}
# mesmos apelidos do filtro de operadora do Extrair Dados (o nome que vem da portabilidade/prefixo varia)
APELIDOS = {
    'VIVO': ['VIVO', 'TELEFONICA', 'GVT'], 'CLARO': ['CLARO', 'EMBRATEL', 'NEXTEL', 'NET '], 'TIM': ['TIM'],
    'OI': ['OI', 'TELEMAR', 'BRASIL TELECOM'], 'ALGAR': ['ALGAR', 'CTBC'], 'BRISANET': ['BRISANET'],
    'SERCOMTEL': ['SERCOMTEL'], 'TELECALL': ['TELECALL'],
}
ORGAOS_PUBLICOS = ["FEDERAL", "GOVERNO", "PUBLICO", "PUBLICA", "ESTADUAL", "ESTADO", "MUNICIPIO", "MUNICIPAL", "POLICIA",
                   "BOMBEIRO", "BANCO DO BRASIL", "CORREIOS", "MINISTERIO", "ADVOCACIA-GERAL", "BANCO CENTRAL", "CASA CIVIL",
                   "CONTROLADORIA-GERAL", "GABINETE DE SEGURANCA", "SECRETARIA"]
PERFIS_ILIMITADOS = ("ADMIN", "MAYK", "CLINICAS", "CONSORCIO")  # os mesmos que não pagam o download do Extrair Dados
TABELA = "hemn.comercial_pj"
MAX_POR_PEDIDO = 5_000
MAX_EXCLUIR = 200_000
AMOSTRA = 3_000            # empresas lidas para estimar a contagem (telefone escolhido + operadora)
TEMPO_BUSCA = 90           # segundos por pedido de busca; passou disso devolve o que achou com "parcial": true
LIMITES = {"contar": 120, "buscar": 30}  # pedidos por minuto por chave
CONFIG_CH = {"max_execution_time": 60, "max_query_size": 20_000_000, "readonly": 2}  # 2 = só leitura, aceita estes ajustes
COLUNAS = ("cnpj, razao_social, nome_fantasia, cnae_fiscal, municipio_nome, uf, bairro, ddd1, telefone1, ddd2, telefone2, "
           "natureza_juridica, data_inicio_atividades")


# ---------------------------------------------------------------- pedidos

class Filtros(BaseModel):
    uf: str = Field(..., description="Sigla do estado (obrigatório)")
    cidade: str = Field("", description="Nome da cidade (vazio = o estado todo)")
    cnaes: List[str] = Field(default_factory=list, description="Atividades: classe (5 dígitos) ou subclasse (7 dígitos)")
    porte: str = Field("todas", description="todas | mei | sem_mei")
    idade_min_meses: Optional[int] = Field(None, ge=0, le=1200)
    idade_max_meses: Optional[int] = Field(None, ge=0, le=1200)
    tipo_telefone: str = Field("todos", description="celular | fixo | todos (todos: celular primeiro)")
    operadora_incluir: str = Field("", description="Só desta operadora (VIVO, CLARO, TIM, OI, ALGAR...)")
    operadora_excluir: str = Field("", description="Sem esta operadora")
    ddd_regiao: bool = Field(False, description="Só telefone com DDD do estado")
    sem_orgaos_publicos: bool = False


class PedidoBusca(Filtros):
    quantidade: int = Field(100, ge=1, le=MAX_POR_PEDIDO)
    excluir_cnpjs: List[str] = Field(default_factory=list, description="CNPJs que não podem vir (ex.: os que já estão na campanha)")


class NovaChave(BaseModel):
    username: str
    nome: str = ""


def _sem_acento(texto: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", str(texto or "")) if not unicodedata.combining(c)).upper()


def _validar(f: Filtros) -> dict:
    uf = (f.uf or "").strip().upper()
    if uf not in UFS:
        raise HTTPException(400, "Escolha o estado.")
    cnaes = []
    for c in f.cnaes or []:
        d = re.sub(r"\D", "", str(c))
        if len(d) not in (2, 3, 4, 5, 7):
            raise HTTPException(400, f"Atividade (CNAE) inválida: {c}")
        if d not in cnaes:
            cnaes.append(d)
    if len(cnaes) > 30:
        raise HTTPException(400, "Escolha no máximo 30 atividades.")
    if f.porte not in ("todas", "mei", "sem_mei") or f.tipo_telefone not in ("celular", "fixo", "todos"):
        raise HTTPException(400, "Filtros inválidos.")
    if f.idade_min_meses is not None and f.idade_max_meses is not None and f.idade_min_meses > f.idade_max_meses:
        raise HTTPException(400, "Idade da empresa: o primeiro número precisa ser menor que o segundo.")
    incluir, excluir = (f.operadora_incluir or "").strip().upper(), (f.operadora_excluir or "").strip().upper()
    if incluir and incluir not in APELIDOS or excluir and excluir not in APELIDOS:
        raise HTTPException(400, "Operadora inválida.")
    if incluir and incluir == excluir:
        raise HTTPException(400, "A mesma operadora não pode estar em incluir e em excluir.")
    return {"uf": uf, "cidade": " ".join(_sem_acento(f.cidade).split()), "cnaes": cnaes, "porte": f.porte,
            "idade_min": f.idade_min_meses, "idade_max": f.idade_max_meses, "tipo": f.tipo_telefone, "incluir": incluir,
            "excluir": excluir, "ddd_regiao": bool(f.ddd_regiao), "sem_orgaos": bool(f.sem_orgaos_publicos)}


def _resumo(v: dict) -> str:
    partes = [f"{v['uf']}/{v['cidade']}" if v["cidade"] else v["uf"]]
    if v["cnaes"]:
        partes.append(f"{len(v['cnaes'])} CNAE")
    partes += {"mei": ["só MEI"], "sem_mei": ["sem MEI"]}.get(v["porte"], [])
    partes += {"celular": ["celular"], "fixo": ["fixo"]}.get(v["tipo"], [])
    if v["incluir"]:
        partes.append(f"só {v['incluir']}")
    if v["excluir"]:
        partes.append(f"sem {v['excluir']}")
    return " · ".join(partes)


def montar_where(v: dict, cidade_na_base: str = "", excluir: list[str] | None = None) -> tuple[str, dict]:
    """O WHERE da consulta e os parâmetros (cidade_na_base: o nome como está na tabela)."""
    conds = ["situacao_cadastral = '02'", "uf = %(uf)s"]
    params: dict = {"uf": v["uf"]}
    if cidade_na_base:
        conds.append("municipio_nome = %(cidade)s")
        params["cidade"] = cidade_na_base
    if v["cnaes"]:
        conds.append("(" + " OR ".join(f"startsWith(cnae_fiscal, %(cnae{i})s)" for i in range(len(v["cnaes"]))) + ")")
        params.update({f"cnae{i}": c for i, c in enumerate(v["cnaes"])})
    if v["porte"] == "mei":
        conds.append("natureza_juridica = '2135'")
    elif v["porte"] == "sem_mei":
        conds.append("natureza_juridica != '2135'")
    if v["idade_min"] is not None or v["idade_max"] is not None:
        meses = ("dateDiff('month', toDateOrNull(concat(substring(data_inicio_atividades, 1, 4), '-', "
                 "substring(data_inicio_atividades, 5, 2), '-', substring(data_inicio_atividades, 7, 2))), today())")
        conds.append("length(data_inicio_atividades) = 8")
        if v["idade_min"] is not None:
            conds.append(f"{meses} >= %(idade_min)s")
            params["idade_min"] = v["idade_min"]
        if v["idade_max"] is not None:
            conds.append(f"{meses} <= %(idade_max)s")
            params["idade_max"] = v["idade_max"]
    if v["sem_orgaos"]:
        conds.append("NOT multiSearchAnyCaseInsensitive(razao_social, %(orgaos)s)")
        params["orgaos"] = ORGAOS_PUBLICOS
    digitos = {"celular": "('6','7','8','9')", "fixo": "('2','3','4','5')"}.get(v["tipo"])
    if digitos:
        conds.append(f"((length(telefone1) >= 8 AND substring(telefone1, 1, 1) IN {digitos}) OR "
                     f"(length(telefone2) >= 8 AND substring(telefone2, 1, 1) IN {digitos}))")
    else:
        conds.append("(length(telefone1) >= 8 OR length(telefone2) >= 8)")
    if v["ddd_regiao"]:
        conds.append("(ddd1 IN %(ddds)s OR ddd2 IN %(ddds)s)")
        params["ddds"] = DDD_POR_UF[v["uf"]]
    if excluir:
        conds.append("cnpj NOT IN %(excluir)s")
        params["excluir"] = excluir
    return " AND ".join(conds), params


# ---------------------------------------------------------------- telefone principal (mesma regra do Extrair Dados)

def _completo(ddd, tel) -> str:
    n = re.sub(r"\D", "", f"{ddd or ''}{tel or ''}")
    if len(n) == 10 and n[2] in "6789":
        n = n[:2] + "9" + n[2:]  # celular antigo de 8 dígitos ganha o 9
    if not n or not n.strip("0") or not n[2:].strip("0") or len(n) not in (10, 11):
        return ""
    return n


def _tipo(tel) -> str:
    n = re.sub(r"\D", "", str(tel or ""))
    if not n:
        return ""
    return "celular" if len(n) == 9 or (len(n) == 8 and n[0] in "6789") else "fixo"


def escolher_telefone(linha: dict, v: dict) -> str:
    """O telefone principal da empresa: celular ou fixo pedido, do DDD do estado se "ddd_regiao"; em "todos",
    celular antes de fixo (como o TELEFONE SOLICITADO do Extrair Dados)."""
    ddds = DDD_POR_UF.get(v["uf"], []) if v["ddd_regiao"] else None
    opcoes = []
    for ddd, tel in ((linha["ddd1"], linha["telefone1"]), (linha["ddd2"], linha["telefone2"])):
        numero, tipo = _completo(ddd, tel), _tipo(tel)
        if numero and tipo and (ddds is None or str(ddd or "").strip() in ddds):
            opcoes.append((tipo, numero))
    ordem = {"celular": ["celular"], "fixo": ["fixo"]}.get(v["tipo"], ["celular", "fixo"])
    for tipo in ordem:
        for t, numero in opcoes:
            if t == tipo:
                return numero
    return ""


def operadora_curta(nome: str) -> str:
    """'VIVO / TELEFONICA' -> 'VIVO'. Vazio quando não consta."""
    n = _sem_acento(nome)
    for curta, apelidos in APELIDOS.items():
        if any(a in n for a in apelidos):
            return curta
    return "" if not n or "CONSTA" in n or n == "ERRO" else n.split("/")[0].strip()


# ---------------------------------------------------------------- chaves de acesso

def _hash(chave: str) -> str:
    return hashlib.sha256(chave.encode("utf-8")).hexdigest()


def _conexao(db_path: str) -> sqlite3.Connection:
    con = sqlite3.connect(db_path, timeout=30)
    con.execute("PRAGMA journal_mode=WAL")
    con.row_factory = sqlite3.Row
    return con


def garantir_tabela(db_path: str) -> None:
    con = _conexao(db_path)
    try:
        con.execute("""CREATE TABLE IF NOT EXISTS api_chaves (
            id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT NOT NULL COLLATE NOCASE, nome TEXT DEFAULT '',
            prefixo TEXT NOT NULL, hash TEXT NOT NULL UNIQUE, criada TEXT NOT NULL, criada_por TEXT DEFAULT '',
            ultimo_uso TEXT DEFAULT '', usos INTEGER DEFAULT 0, ativa INTEGER DEFAULT 1)""")
        con.commit()
    finally:
        con.close()


def criar_chave(db_path: str, username: str, nome: str = "", criada_por: str = "") -> dict:
    """A chave completa só aparece aqui (no banco fica só o hash)."""
    garantir_tabela(db_path)
    con = _conexao(db_path)
    try:
        usuario = con.execute("SELECT username FROM users WHERE username = ? COLLATE NOCASE", (username,)).fetchone()
        if not usuario:
            raise ValueError(f"Usuário não encontrado: {username}")
        chave = "ak_" + secrets.token_urlsafe(32)
        agora = datetime.now().isoformat(timespec="seconds")
        cur = con.execute("INSERT INTO api_chaves (username, nome, prefixo, hash, criada, criada_por) VALUES (?, ?, ?, ?, ?, ?)",
                          (usuario["username"], nome.strip()[:80], chave[:10], _hash(chave), agora, criada_por))
        con.commit()
        return {"id": cur.lastrowid, "username": usuario["username"], "nome": nome.strip()[:80], "prefixo": chave[:10],
                "criada": agora, "chave": chave}
    finally:
        con.close()


def listar_chaves(db_path: str) -> list[dict]:
    garantir_tabela(db_path)
    con = _conexao(db_path)
    try:
        return [dict(r) for r in con.execute("SELECT id, username, nome, prefixo, criada, criada_por, ultimo_uso, usos, ativa "
                                             "FROM api_chaves ORDER BY id DESC")]
    finally:
        con.close()


def revogar_chave(db_path: str, chave_id: int) -> bool:
    garantir_tabela(db_path)
    con = _conexao(db_path)
    try:
        n = con.execute("UPDATE api_chaves SET ativa = 0 WHERE id = ?", (chave_id,)).rowcount
        con.commit()
        return bool(n)
    finally:
        con.close()


# ---------------------------------------------------------------- rotas

def criar_rotas(engine, db_path: str, get_current_user, log_transaction, compute_dejavu_overlap,
                log_downloaded_cnpjs, dejavu_skip_for_user) -> APIRouter:
    rotas = APIRouter(tags=["Integração"])
    garantir_tabela(db_path)
    trava = threading.Lock()
    pedidos: dict[str, list[float]] = {}
    ultimo_registro: dict[int, float] = {}
    cidades_cache: dict[str, tuple[float, dict]] = {}

    def limitar(chave_id: int, tipo: str) -> None:
        agora = time.monotonic()
        k = f"{chave_id}:{tipo}"
        with trava:
            recentes = [t for t in pedidos.get(k, []) if agora - t < 60]
            if len(recentes) >= LIMITES[tipo]:
                raise HTTPException(429, "Muitos pedidos em pouco tempo. Aguarde um minuto.")
            pedidos[k] = recentes + [agora]

    def usuario_da_chave(authorization: str = Header(None)) -> dict:
        chave = authorization[7:].strip() if authorization and authorization.startswith("Bearer ") else ""
        if not chave.startswith("ak_"):
            raise HTTPException(401, "Chave de acesso ausente ou inválida.")
        con = _conexao(db_path)
        try:
            linha = con.execute("SELECT c.id AS _chave_id, u.* FROM api_chaves c JOIN users u ON u.username = c.username "
                                "COLLATE NOCASE WHERE c.hash = ? AND c.ativa = 1", (_hash(chave),)).fetchone()
            if not linha:
                raise HTTPException(401, "Chave de acesso inválida ou cancelada.")
            usuario = dict(linha)
            if str(usuario.get("status") or "ACTIVE").upper() != "ACTIVE":
                raise HTTPException(403, "O usuário desta chave está bloqueado.")
            agora = time.monotonic()
            if agora - ultimo_registro.get(usuario["_chave_id"], 0) > 30:  # anota o uso sem escrever a cada pedido
                ultimo_registro[usuario["_chave_id"]] = agora
                try:  # banco ocupado (ex.: a limpeza que roda quando o serviço sobe): só não anota desta vez
                    anotar = sqlite3.connect(db_path, timeout=2)
                    try:
                        anotar.execute("UPDATE api_chaves SET ultimo_uso = ?, usos = usos + 1 WHERE id = ?",
                                       (datetime.now().isoformat(timespec="seconds"), usuario["_chave_id"]))
                        anotar.commit()
                    finally:
                        anotar.close()
                except sqlite3.Error as e:
                    print(f"[API_INTEGRACAO] uso da chave {usuario['_chave_id']} não anotado: {e}", flush=True)
            return usuario
        finally:
            con.close()

    def ilimitado(u: dict) -> bool:
        try:
            return u.get("role") in PERFIS_ILIMITADOS or float(u.get("total_limit") or 0) >= 9_000_000
        except (TypeError, ValueError):
            return False

    def consultar(sql: str, params: dict) -> list[dict]:
        cliente = engine._get_ch_client()
        if cliente is None:
            raise HTTPException(503, "Base de dados indisponível no momento. Tente de novo em instantes.")
        try:
            r = cliente.query(sql, params, settings=CONFIG_CH)
            return [dict(zip(r.column_names, l)) for l in r.result_rows]
        except HTTPException:
            raise
        except Exception as e:
            print(f"[API_INTEGRACAO] consulta falhou: {e}", flush=True)
            raise HTTPException(503, "A base de dados não respondeu a tempo. Tente filtros menores ou de novo em instantes.")
        finally:
            try:
                cliente.close()
            except Exception:
                pass

    def nome_da_cidade(uf: str, cidade: str) -> str:
        """O nome como está na base (sem acento, maiúsculo). Compara só as letras: "Santa Bárbara d'Oeste" acha
        "SANTA BARBARA D'OESTE"."""
        agora = time.monotonic()
        with trava:
            cache = cidades_cache.get(uf)
        if not cache or agora - cache[0] > 6 * 3600:
            nomes = [l["municipio_nome"] for l in consultar(
                f"SELECT DISTINCT municipio_nome FROM {TABELA} WHERE uf = %(uf)s", {"uf": uf})]
            cache = (agora, {re.sub(r"[^A-Z]", "", n): n for n in nomes if n})
            with trava:
                cidades_cache[uf] = cache
        achado = cache[1].get(re.sub(r"[^A-Z]", "", cidade))
        if not achado:
            raise HTTPException(400, f"Cidade não encontrada em {uf}: {cidade.title()}")
        return achado

    def preparar(linhas: list[dict], v: dict) -> list[dict]:
        """Escolhe o telefone principal, descobre a operadora (portabilidade + prefixo, como no Extrair Dados) e
        aplica o filtro de operadora. Devolve só as empresas com telefone."""
        com_tel = []
        for l in linhas:
            numero = escolher_telefone(l, v)
            if numero:
                com_tel.append({**l, "_telefone": numero})
        if not com_tel:
            return []
        df = pd.DataFrame({"TELEFONE SOLICITADO": [l["_telefone"] for l in com_tel]})
        df = engine._append_operator_column(None, df)
        for l, op in zip(com_tel, df["OPERADORA DO TELEFONE"].tolist()):
            l["_operadora"] = operadora_curta(op)
        if v["incluir"]:
            com_tel = [l for l in com_tel if l["_operadora"] == v["incluir"]]
        if v["excluir"]:
            com_tel = [l for l in com_tel if l["_operadora"] != v["excluir"]]
        return com_tel

    def empresa(l: dict) -> dict:
        d = str(l.get("data_inicio_atividades") or "")
        razao = re.sub(r"\s+\d{11}$", "", " ".join(str(l.get("razao_social") or "").split()))  # MEI: sem o CPF no fim
        return {"cnpj": str(l["cnpj"]), "razao_social": razao, "nome_fantasia": " ".join(str(l.get("nome_fantasia") or "").split()),
                "telefone": l["_telefone"], "operadora": l["_operadora"], "cnae": str(l.get("cnae_fiscal") or ""),
                "cnae_descricao": "", "abertura": f"{d[:4]}-{d[4:6]}-{d[6:8]}" if len(d) == 8 and d.isdigit() else "",
                "mei": str(l.get("natureza_juridica") or "") == "2135", "bairro": str(l.get("bairro") or "").strip(),
                "cidade": str(l.get("municipio_nome") or ""), "uf": str(l.get("uf") or "")}

    @rotas.get("/integracao/v1/situacao", summary="Quem é o usuário da chave e quantos créditos tem")
    def situacao(usuario: dict = Depends(usuario_da_chave)):
        livre = ilimitado(usuario)
        saldo = None if livre else max(0, int(float(usuario.get("total_limit") or 0) - float(usuario.get("current_usage") or 0)))
        return {"usuario": usuario["username"], "ilimitado": livre, "creditos": saldo}

    @rotas.post("/integracao/v1/empresas/contar", summary="Quantas empresas os filtros acham (não gasta créditos)")
    def contar(filtros: Filtros, usuario: dict = Depends(usuario_da_chave)):
        limitar(usuario["_chave_id"], "contar")
        v = _validar(filtros)
        where, params = montar_where(v, nome_da_cidade(v["uf"], v["cidade"]) if v["cidade"] else "")
        total = int(consultar(f"SELECT count() AS n FROM {TABELA} WHERE {where}", params)[0]["n"])
        if not total:
            return {"total": 0, "aproximado": False}
        amostra = consultar(f"SELECT {COLUNAS} FROM {TABELA} WHERE {where} ORDER BY cityHash64(cnpj) LIMIT {AMOSTRA}", params)
        boas = len(preparar(amostra, v))
        if total <= len(amostra):
            return {"total": boas, "aproximado": False}
        return {"total": round(total * boas / len(amostra)), "aproximado": True}

    @rotas.post("/integracao/v1/empresas/buscar", summary="Traz empresas com 1 telefone principal (gasta 1 crédito por empresa)")
    def buscar(pedido: PedidoBusca, usuario: dict = Depends(usuario_da_chave)):
        limitar(usuario["_chave_id"], "buscar")
        v = _validar(pedido)
        livre = ilimitado(usuario)
        saldo = float(usuario.get("total_limit") or 0) - float(usuario.get("current_usage") or 0)
        if not livre and saldo < 1:
            raise HTTPException(402, "Sem créditos. Fale com o suporte para recarregar.")
        excluir = sorted({re.sub(r"\D", "", str(c))[:14] for c in pedido.excluir_cnpjs if str(c).strip()})
        if len(excluir) > MAX_EXCLUIR:
            raise HTTPException(400, f"Envie no máximo {MAX_EXCLUIR:,} CNPJs em excluir_cnpjs.".replace(",", "."))
        where, params = montar_where(v, nome_da_cidade(v["uf"], v["cidade"]) if v["cidade"] else "", excluir)
        pagina = min(20_000, max(500, pedido.quantidade * (3 if v["incluir"] or v["excluir"] else 2)))
        achadas: list[dict] = []
        vistos: set[str] = set(excluir)
        inicio, deslocamento, esgotou = time.monotonic(), 0, False
        while len(achadas) < pedido.quantidade:
            linhas = consultar(f"SELECT {COLUNAS} FROM {TABELA} WHERE {where} ORDER BY cityHash64(cnpj) "
                               f"LIMIT {pagina} OFFSET {deslocamento}", params)
            deslocamento += len(linhas)
            novas = [l for l in linhas if str(l["cnpj"]) not in vistos]
            vistos.update(str(l["cnpj"]) for l in novas)
            achadas += preparar(novas, v)[:pedido.quantidade - len(achadas)]
            if len(linhas) < pagina:
                esgotou = True
                break
            if time.monotonic() - inicio > TEMPO_BUSCA:
                break
        # créditos: o mesmo CNPJ já pago nos últimos 30 dias não é cobrado de novo (regra do Extrair Dados)
        cnpjs = [str(l["cnpj"]) for l in achadas]
        ja_pagos = set() if livre or dejavu_skip_for_user(usuario) else compute_dejavu_overlap(usuario["username"], set(cnpjs))
        if not livre:  # saldo menor que o pedido: vêm as já pagas e as que o saldo cobre
            pagas = {id(l) for l in [l for l in achadas if str(l["cnpj"]) not in ja_pagos][:int(saldo)]}
            achadas = [l for l in achadas if str(l["cnpj"]) in ja_pagos or id(l) in pagas]
        cobradas = len([l for l in achadas if str(l["cnpj"]) not in ja_pagos])
        if achadas:
            if not livre and cobradas:
                con = _conexao(db_path)
                try:
                    con.execute("UPDATE users SET current_usage = current_usage + ? WHERE username = ?", (cobradas, usuario["username"]))
                    con.commit()
                finally:
                    con.close()
            log_transaction(usuario["username"], "DEBIT", cobradas, "API_EMPRESAS",
                            f"API (chave {usuario['_chave_id']}): {len(achadas):,} empresas, {cobradas:,} cobradas · {_resumo(v)}")
            if not livre and not dejavu_skip_for_user(usuario):
                log_downloaded_cnpjs(usuario["username"], [str(l["cnpj"]) for l in achadas], f"api-{usuario['_chave_id']}")
        parcial = not esgotou and len(achadas) < pedido.quantidade
        restante = None if livre else max(0, int(saldo - cobradas))
        return {"empresas": [empresa(l) for l in achadas], "parcial": parcial, "esgotou": esgotou,
                "cobradas": cobradas, "creditos": restante}

    def so_admin(usuario: dict = Depends(get_current_user)) -> dict:
        if usuario.get("role") != "ADMIN":
            raise HTTPException(403, "Só o administrador gerencia as chaves de acesso.")
        return usuario

    @rotas.get("/integracao/chaves", summary="Lista as chaves de acesso (sem mostrar a chave)")
    def get_chaves(admin: dict = Depends(so_admin)):
        return listar_chaves(db_path)

    @rotas.post("/integracao/chaves", summary="Cria uma chave para um usuário (a chave aparece só nesta resposta)")
    def post_chave(pedido: NovaChave, admin: dict = Depends(so_admin)):
        try:
            return criar_chave(db_path, pedido.username, pedido.nome, admin["username"])
        except ValueError as e:
            raise HTTPException(400, str(e)) from e

    @rotas.delete("/integracao/chaves/{chave_id}", summary="Cancela uma chave (para de funcionar na hora)")
    def delete_chave(chave_id: int, admin: dict = Depends(so_admin)):
        if not revogar_chave(db_path, chave_id):
            raise HTTPException(404, "Chave não encontrada.")
        return {"ok": True}

    return rotas


if __name__ == "__main__":  # gerenciar chaves pelo terminal do servidor
    banco = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hemn_cloud.db")
    acao = sys.argv[1] if len(sys.argv) > 1 else ""
    if acao == "criar" and len(sys.argv) >= 3:
        nova = criar_chave(banco, sys.argv[2], " ".join(sys.argv[3:]), "terminal")
        print(f"Chave criada para {nova['username']} (id {nova['id']}). Guarde agora, ela não aparece de novo:\n{nova['chave']}")
    elif acao == "listar":
        for c in listar_chaves(banco):
            print(f"{c['id']:>4}  {c['prefixo']}…  {c['username']:<20} {'ativa' if c['ativa'] else 'cancelada':<10} "
                  f"usos {c['usos']:<6} último uso {c['ultimo_uso'] or '-'}  {c['nome']}")
    elif acao == "revogar" and len(sys.argv) == 3:
        print("Chave cancelada." if revogar_chave(banco, int(sys.argv[2])) else "Chave não encontrada.")
    else:
        print(__doc__)
