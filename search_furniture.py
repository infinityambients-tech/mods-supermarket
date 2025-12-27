import json
import os

save_path = r'C:\Users\igorz\AppData\LocalLow\Nokta Games\Supermarket Simulator\slot_0.es3'

def search_keys(data, path=''):
    if isinstance(data, dict):
        for k, v in data.items():
            cp = f"{path}/{k}"
            # Common names for objects in Supermarket Simulator
            if any(x in k.lower() for x in ['furniture', 'display', 'shelf', 'rack', 'checkout', 'register', 'fridge', 'freezer', 'light', 'pos', 'rot', 'item', 'placed']):
                print(f"KEY FOUND: {cp} = {str(v)[:100]}")
            search_keys(v, cp)
    elif isinstance(data, list):
        for i, v in enumerate(data):
            search_keys(v, f"{path}[{i}]")

if os.path.exists(save_path):
    with open(save_path, 'r', encoding='utf-8', errors='ignore') as f:
        try:
            data = json.load(f)
            search_keys(data)
        except Exception as e:
            print(f"Error: {e}")
else:
    print("Save file not found.")
