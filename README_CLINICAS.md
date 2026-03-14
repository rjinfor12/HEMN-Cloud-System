# Guia de Implementação: Módulo Clínicas (Leads Master)

Este módulo permite a pesquisa unitária instantânea em uma base de dados ClickHouse contendo milhões de registros (leads).

## 1. Requisitos do Sistema

- **ClickHouse**: Deve estar instalado e rodando no servidor VPS.
- **Python**: Versão 3.8+ com os pacotes `clickhouse-connect` e `pandas` instalados.
  ```bash
  pip install clickhouse-connect pandas
  ```

## 2. Estrutura da Base de Dados

A tabela `leads` no ClickHouse possui a seguinte estrutura (criada automaticamente pelo script de ingestão):

| Coluna | Tipo | Descrição |
| :--- | :--- | :--- |
| `cpf` | String | CPF do cliente (somente números) |
| `nome` | String | Nome completo |
| `dt_nascimento` | String | Data de nascimento (formato original da planilha) |
| `tel_fixo1` | String | Telefone fixo |
| `celular1` | String | Celular principal |
| `uf` | String | Estado (ex: SP, RJ) |
| `regiao` | String | Regional (ex: SUDESTE, SUL) |

## 3. Ingestão de Dados (Planilhas de 45GB)

Para subir os dados das planilhas que estão na sua Área de Trabalho para o sistema:

1.  Certifique-se de que as planilhas estão na pasta: `C:\Users\Junior T.I\OneDrive\Área de Trabalho\csv`
2.  Abra um terminal na pasta do projeto.
3.  Execute o script de ingestão:
    ```bash
    python ingest_leads.py
    ```
    *O script processa os arquivos em blocos de 100.000 registros para não sobrecarregar a memória RAM.*

## 4. Controle de Acesso

- **Perfil CLINICAS**: Criamos um novo nível de acesso. Usuários com este perfil verão **apenas** o módulo de Clínicas.
- **Administrador**: Continua tendo acesso total, incluindo a pesquisa de leads.

### Como criar um acesso para Clínica:
1. Vá em **Gestão Titanium Cloud** (Admin).
2. Clique em **Novo Usuário**.
3. No campo **CARGO / ROLE**, selecione **PERFIL CLÍNICAS**.

## 5. Funcionamento da Pesquisa

O sistema permite filtrar por:
- **Brasil Todo**: Pesquisa em toda a base nacional.
- **Região**: Filtra por SUDESTE, SUL, NORTE, etc.
- **Estado (UF)**: Filtra por um estado específico para maior velocidade.

> **Importante**: A pesquisa por ClickHouse é otimizada para ser instantânea, mesmo com 45GB de dados, graças aos índices de MergeTree.
