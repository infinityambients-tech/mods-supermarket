import json
import os

save_path = r'C:\Users\igorz\AppData\LocalLow\Nokta Games\Supermarket Simulator\slot_0.es3'

if os.path.exists(save_path):
    with open(save_path, 'r', encoding='utf-8', errors='ignore') as f:
        try:
            data = json.load(f)
            if 'Employees' in data:
                print("--- EMPLOYEES ---")
                print(json.dumps(data['Employees'], indent=2))
            
            if 'Storage' in data:
                print("\n--- STORAGE ---")
                print(json.dumps(data['Storage'], indent=2))
            
            def search_supplier(data, path=''):
                if isinstance(data, dict):
                    for k, v in data.items():
                        cp = f"{path}/{k}"
                        if any(x in k.lower() for x in ['supplier', 'discount', 'reputation', 'relation', 'skill', 'capacity', 'occupy', 'count']):
                            print(f"SUPPLIER/STAT KEY: {cp} = {v}")
                        search_supplier(v, cp)
                elif isinstance(data, list) and len(data) > 0:
                    for i, v in enumerate(data[:3]): # Search first 3 items
                        search_supplier(v, f"{path}[{i}]")

            search_supplier(data)

        except Exception as e:
            print(f"Error: {e}")
else:
    print("Save file not found.")
