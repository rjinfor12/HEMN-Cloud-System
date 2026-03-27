import sys
sys.path.append("/var/www/hemn_cloud")
from cloud_engine import CloudEngine
import pandas as pd
import numpy as np

# Initialize Engine
ce = CloudEngine(
    db_cnpj_path="/var/www/hemn_cloud/cnpj.db",
    db_carrier_path="/var/www/hemn_cloud/hemn_carrier.db"
)

# Test Data
df = pd.DataFrame({
    "DDD1": ["11", "81", "81", "00"],
    "TEL1": ["967752824", "988887777", "00000000", "00000000"],
    "DDD2": ["81", "11", "", ""],
    "TEL2": ["999991111", "933334444", "", ""],
    "RAZAO_SOCIAL": ["REGIONAL_SEC", "REGIONAL_PRI", "JUNK_PE", "ALL_ZERO"],
    "SITUACAO_CADASTRAL": ["02", "02", "02", "02"],
    "CNPJ": ["111", "222", "333", "444"],
    "CNAE_FISCAL_PRINCIPAL": ["4399103", "4399103", "4399103", "4399103"]
})

filters = {"uf": "PE", "filtrar_ddd_regiao": True, "tipo_tel": "TODOS"}

# Mock objects to satisfy the function signature
class MockSheet:
    def write_row(self, *args, **kwargs): pass
class MockWB: pass

print("Starting _process_extraction_dataframe test...")
try:
    # Notice: we pass the signature: tid, df, filters, workbook, sheet, header_fmt, header_written, start_row_count
    processed = ce._process_extraction_dataframe("test_tid", df, filters, MockWB(), MockSheet(), None, True, 0)
    
    print(f"Results Found: {len(processed)}")
    if not processed.empty:
        print("Final Dataframe Peek:")
        # Column names are UPPER and underscores are SPACE
        print(processed[["RAZAO SOCIAL", "TELEFONE SOLICITADO"]].to_dict("records"))
        
        # Validation
        all_regional = all(str(t).startswith(("81", "87")) for t in processed["TELEFONE SOLICITADO"])
        no_junk = not any("0000" in str(t) for t in processed["TELEFONE SOLICITADO"])
        
        if all_regional: print("VERIFY: All numbers are Regional PE (81/87) - SUCCESS")
        else: print("VERIFY: Found non-regional numbers - FAIL")
            
        if no_junk: print("VERIFY: No junk all-zero numbers found - SUCCESS")
        else: print("VERIFY: Found junk numbers - FAIL")
        
        # Specific check for prioritization
        rec_sec = processed[processed["RAZAO SOCIAL"] == "REGIONAL_SEC"]
        if not rec_sec.empty and rec_sec.iloc[0]["TELEFONE SOLICITADO"] == "81999991111":
             print("VERIFY: Prioritized regional secondary over non-regional primary - SUCCESS")
        else:
             print("VERIFY: Failed to prioritize regional phone - FAIL")

    else:
        print("Buffer is empty. Check logic.")
except Exception as e:
    import traceback
    print(f"Error during execution: {e}")
    traceback.print_exc()
