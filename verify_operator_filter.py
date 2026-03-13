import pandas as pd
from cloud_engine import CloudEngine

# Initialize the engine
print("Initializing Engine...")
engine = CloudEngine(db_cnpj_path="cnpj.db", db_carrier_path="hemn_carrier.db")

# 1. Create a dummy dataframe with known operators
# We use typical prefixes:
# 1199... (VIVO), 1198... (VIVO/TIM), 1197... (VIVO), 1194... (VIVO)
# Let's use some real numbers that the prefix tree or DB will resolve.
# Since we don't know the exact DB contents, we rely on prefix tree logic fallback.
# Prefix 1199999 (VIVO), Prefix 1198111 (TIM), Prefix 1199111 (CLARO) - hypothetically.
# We'll just put some and see what `get_single_carrier` says first.

test_numbers = ["11999999999", "11981111111", "34991111111", "11944444444", "31988888888"]

print("\n--- Identifying Test Numbers ---")
for num in test_numbers:
    print(f"{num}: {engine.get_single_carrier(num)}")

# Now mock a dataframe
df = pd.DataFrame({
    "telefone1": ["11999999999", "11981111111", "34991111111", "11944444444"],
    "telefone2": ["", "", "11981111111", ""]  # Line 3 has two numbers
})

print("\n--- Original DataFrame ---")
print(df)

print("\n--- Testing INCLUSION = TODAS, EXCLUSION = NENHUMA ---")
res1 = engine._filter_by_operator_df("tid_1", df.copy(), "TODAS", "NENHUMA")
print(res1)

print("\n--- Testing INCLUSION = VIVO, EXCLUSION = NENHUMA ---")
res2 = engine._filter_by_operator_df("tid_2", df.copy(), "VIVO", "NENHUMA")
print(res2)

print("\n--- Testing INCLUSION = TODAS, EXCLUSION = TIM ---")
res3 = engine._filter_by_operator_df("tid_3", df.copy(), "TODAS", "TIM")
print(res3)
