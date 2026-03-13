import sys
sys.path.append(r"C:\Users\Junior T.I\scratch\data_analysis")
from consolidation_engine import ConsolidationEngine

def print_log(msg):
    print(msg)

engine = ConsolidationEngine(target_dir="", output_file="", log_callback=print_log)
engine.split_large_file(
    r"C:\Users\Junior T.I\scratch\data_analysis\sp_small.csv",
    r"C:\Users\Junior T.I\.gemini\antigravity\scratch\data_analysis\test_split_engine_small.xlsx"
)
