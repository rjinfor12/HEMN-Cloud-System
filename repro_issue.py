
import os
import pandas as pd
import re
import csv
import sqlite3

class MockEngine:
    def __init__(self):
        self.anatel_dict = {}
        self.prefix_tree = []
        self._load_data_assets()

    def log(self, msg): print(msg)

    def _load_data_assets(self):
        assets_dir = "data_assets"
        dict_path = os.path.join(assets_dir, "cod_operadora.csv")
        prefix_path = os.path.join(assets_dir, "prefix_anatel.csv")
        
        # Encoding test: many BR files use latin1/iso-8859-1
        if os.path.exists(dict_path):
            try:
                # Try UTF-8 first (current implementation)
                with open(dict_path, mode='r', encoding='utf-8') as f:
                    reader = csv.reader(f)
                    for row in reader:
                        if len(row) >= 2:
                            self.anatel_dict[row[0].strip()] = row[1].strip()
                print(f"Loaded {len(self.anatel_dict)} operators with UTF-8")
            except Exception as e:
                print(f"UTF-8 failed: {e}")
                # Try ISO-8859-1
                try:
                    with open(dict_path, mode='r', encoding='iso-8859-1') as f:
                        reader = csv.reader(f)
                        for row in reader:
                            if len(row) >= 2:
                                self.anatel_dict[row[0].strip()] = row[1].strip()
                    print(f"Loaded {len(self.anatel_dict)} operators with ISO-8859-1")
                except Exception as e2:
                    print(f"ISO-8859-1 failed: {e2}")

        if os.path.exists(prefix_path):
            df_prefix = pd.read_csv(prefix_path, sep=';', dtype=str)
            self.prefix_tree = list(zip(df_prefix['number'], df_prefix['company']))
            self.prefix_tree.sort(key=lambda x: len(x[0]), reverse=True)
            print(f"Loaded {len(self.prefix_tree)} prefixes")

    def get_carrier_name(self, code):
        return self.anatel_dict.get(str(code), f"CÓD {code}")

    def identify_original_carrier(self, phone, skip_9=False):
        num = re.sub(r'\D', '', str(phone))
        if num.startswith("55") and len(num) >= 12: num = num[2:]
        if num.startswith("0"): num = num[1:]
        
        # Test specific 9th digit logic
        search_num = num
        if skip_9 and len(num) == 11 and num[2] == '9':
            search_num = num[:2] + num[3:] # DDD + (prefix without 9)
            print(f"Testing with 9-digit skip: {num} -> {search_num}")

        for prefix, company_code in self.prefix_tree:
            if search_num.startswith(prefix):
                return self.get_carrier_name(company_code)
        return "NOT FOUND"

engine = MockEngine()

# Test cases
test_numbers = [
    "11927801234", # Mobile with 9
    "1127801234",  # Fixed/Old mobile
    "21999999999",
    "1120101234"
]

print("\n--- RESULTS WITHOUT SKIP 9 ---")
for t in test_numbers:
    print(f"{t}: {engine.identify_original_carrier(t, skip_9=False)}")

print("\n--- RESULTS WITH SKIP 9 ---")
for t in test_numbers:
    print(f"{t}: {engine.identify_original_carrier(t, skip_9=True)}")
