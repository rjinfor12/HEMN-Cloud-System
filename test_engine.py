from consolidation_engine import ConsolidationEngine
import os

db = r"C:\Users\Junior T.I\OneDrive\Área de Trabalho\cruzar\cnpj.db"
out = r"C:\Users\Junior T.I\OneDrive\Área de Trabalho\cruzar\test_paulista.xlsx"

engine = ConsolidationEngine(target_dir="", output_file="", log_callback=print)

filters = {
    "CIDADE": "Paulista",
    "UF": "PE",
    "CNAE": "",
    "SITUAÇÃO": "ATIVA"
}

print("Iniciando teste de extração...")
try:
    success = engine.extract_by_filter(db, out, filters)
    print(f"Resultado: {success}")
except Exception as e:
    print(f"FALHA EXPLÍCITA NO MOTOR: {str(e)}")
