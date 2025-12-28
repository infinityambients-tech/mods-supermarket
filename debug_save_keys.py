import json
import os

save_path = r'C:\Users\igorz\AppData\LocalLow\Nokta Games\Supermarket Simulator\slot_0.es3'
output_file = 'save_structure_dump.txt'

def traverse(data, path=''):
    if isinstance(data, dict):
        for k, v in data.items():
            current_path = f"{path}/{k}"
            # Log specific interesting keys or just all keys at top levels
            if any(x in k.lower() for x in ['level', 'xp', 'progression', 'store']):
                with open(output_file, 'a', encoding='utf-8') as f:
                    f.write(f"{current_path}: {type(v).__name__}\n")
            
            # Print values for level-like keys
            if 'level' in k.lower() and isinstance(v, (int, float, dict)):
                 with open(output_file, 'a', encoding='utf-8') as f:
                    f.write(f"  VALUE: {v}\n")

            if isinstance(v, (dict, list)):
                traverse(v, current_path)
    elif isinstance(data, list):
        for i, item in enumerate(data):
             traverse(item, f"{path}[{i}]")

if os.path.exists(save_path):
    print(f"Reading {save_path}...")
    try:
        with open(save_path, 'r', encoding='utf-8', errors='ignore') as f:
            data = json.load(f)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("--- SCAN START ---\n")
            
        traverse(data)
        print(f"Done. Check {output_file}")
    except Exception as e:
        print(f"Error: {e}")
else:
    print("Save file not found.")
