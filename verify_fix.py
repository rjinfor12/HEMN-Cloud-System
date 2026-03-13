import pandas as pd
import time
from cloud_engine import CloudEngine

engine = CloudEngine(r"C:\HEMN_SYSTEM_DB\cnpj.db", r"C:\HEMN_SYSTEM_DB\hemn_carrier.db")

# Input mock with Row 2
data = [
    ["9752279473", "rogerio elias do nascimento junior"],
    ["00000000000", "USUARIO INEXISTENTE"]
]
df_input = pd.DataFrame(data, columns=["CPF", "NOME"])
input_file = r"C:\Users\Junior T.I\.gemini\antigravity\scratch\data_analysis\test_input.xlsx"
df_input.to_excel(input_file, index=False)

tid = engine.start_enrich(input_file, r"C:\Users\Junior T.I\.gemini\antigravity\scratch\data_analysis", "NOME", "CPF")

while True:
    status = engine.get_task_status(tid)
    print(f"Status: {status['status']} | Progress: {status['progress']}% | Message: {status.get('message')}")
    if status['status'] in ('COMPLETED', 'FAILED'):
        if status['status'] == 'COMPLETED':
            res_df = pd.read_excel(status['result_file'])
            print("\n=== RESULTADO FINAL ===")
            print(res_df[['CPF', 'NOME', 'CNPJ', 'SITUACAO']])
            print(f"\nLinhas no arquivo: {len(res_df)}")
            print(f"Record Count Reportado: {status.get('record_count')}")
        break
    time.sleep(2)
