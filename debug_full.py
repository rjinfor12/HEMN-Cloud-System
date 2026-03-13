import os
import sys

from consolidation_engine import ConsolidationEngine

engine = ConsolidationEngine('a', 'b')

def my_log(msg):
    print("LOG:", msg)

engine.log = my_log

db_path = r'C:/Users/Junior T.I/OneDrive/Área de Trabalho/cruzar/cnpj.db'
output = r'C:/Users/Junior T.I/OneDrive/Área de Trabalho/cruzar/debug_ext.xlsx'
filters = {'UF': 'SP', 'SITUAÇÃO': 'ATIVA', 'TIPO_TELEFONE': 'CELULAR', 'CIDADE': ''}

try:
    engine.extract_by_filter(db_path, output, filters)
except Exception as e:
    import traceback
    traceback.print_exc()
