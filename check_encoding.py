import chardet

def detect_encoding(file_path):
    with open(file_path, 'rb') as f:
        raw_data = f.read(10000)
    result = chardet.detect(raw_data)
    print(f"File: {file_path}")
    print(f"Detected Encoding: {result['encoding']} (Confidence: {result['confidence']})")

detect_encoding('c:/Users/Junior T.I/.gemini/antigravity/scratch/data_analysis/index_vps.html')
detect_encoding('c:/Users/Junior T.I/.gemini/antigravity/scratch/data_analysis/index.html')
