import sys
import os
import pandas as pd
import time

# Adicionar caminho do servidor
sys.path.append('/var/www/hemn_cloud')
from cloud_engine import CloudEngine

print("Iniciando teste de unificação...")
engine = CloudEngine()

# Criar arquivos de teste
f1 = '/tmp/test_unify_1.csv'
f2 = '/tmp/test_unify_2.xlsx'

df1 = pd.DataFrame({'COLUNA_A': ['VAL_1', 'VAL_2'], 'COLUNA_B': ['X', 'Y']})
df2 = pd.DataFrame({'COLUNA_A': ['VAL_3', 'VAL_4'], 'COLUNA_B': ['Z', 'W']})

df1.to_csv(f1, index=False)
df2.to_excel(f2, index=False)

print(f"Arquivos de teste criados em: {f1}, {f2}")

# Iniciar unificação
tid = engine.start_unify([f1, f2], '/var/www/hemn_cloud/storage/results')
print(f"Tarefa iniciada: {tid}")

# Monitorar
for i in range(30):
    status = engine.get_task_status(tid)
    print(f"[{i}s] Status: {status.get('status')} - {status.get('message')} - Progresso: {status.get('progress')}%")
    if status.get('status') == 'COMPLETED':
        print(f"Sucesso! Arquivo gerado: {status.get('result_file')}")
        print(f"Total de registros: {status.get('record_count')}")
        break
    if status.get('status') == 'FAILED':
        print(f"Falha: {status.get('message')}")
        break
    time.sleep(1)

# Limpeza
try:
    os.remove(f1)
    os.remove(f2)
except:
    pass
