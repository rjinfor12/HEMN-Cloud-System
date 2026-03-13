import pandas as pd
import time
import os
from cloud_engine import CloudEngine

engine = CloudEngine(r"C:\HEMN_SYSTEM_DB\cnpj.db", r"C:\HEMN_SYSTEM_DB\hemn_carrier.db")

# Input mock
data = [
    ["9752279473", "rogerio elias do nascimento junior"],
    ["00000000000", "USUARIO INEXISTENTE"]
]
df_input = pd.DataFrame(data, columns=["CPF", "NOME"])
input_file = r"C:\Users\Junior T.I\.gemini\antigravity\scratch\data_analysis\test_input_final.xlsx"
df_input.to_excel(input_file, index=False)

output_dir = r"C:\Users\Junior T.I\.gemini\antigravity\scratch\data_analysis"
tid = engine.start_enrich(input_file, output_dir, "NOME", "CPF")

print(f"Tarefa iniciada: {tid}")
while True:
    status = engine.get_task_status(tid)
    if status['status'] in ('COMPLETED', 'FAILED'):
        print(f"Status Final: {status['status']} | Msg: {status.get('message')}")
        if status['status'] == 'COMPLETED':
            res_df = pd.read_excel(status['result_file'])
            print("\n=== REGISTROS ENCONTRADOS ===")
            print(res_df[['CPF', 'NOME', 'CNPJ', 'RAZAO_SOCIAL', 'SITUACAO']])
            print(f"\nTotal de linhas no Excel: {len(res_df)}")
            print(f"Found Count reportado: {status.get('record_count')}")
        break
    time.sleep(1)
