import json
import os

save_path = r'C:\Users\igorz\AppData\LocalLow\Nokta Games\Supermarket Simulator\slot_0.es3'

if os.path.exists(save_path):
    with open(save_path, 'r', encoding='utf-8', errors='ignore') as f:
        try:
            data = json.load(f)
            if 'Storage' in data:
                print("--- STORAGE ---")
                print(json.dumps(data['Storage'], indent=2)[:2000]) # Limit output
            
            if 'NewCustomization' in data:
                print("\n--- NEWCUSTOMIZATION ---")
                print(json.dumps(data['NewCustomization'], indent=2)[:2000])
            
            # Check for other likely keys
            likely_keys = ['Furniture', 'Display', 'Equipment', 'Layout']
            for lk in likely_keys:
                if lk in data:
                    print(f"\n--- {lk.upper()} ---")
                    print(json.dumps(data[lk], indent=2)[:2000])

        except Exception as e:
            print(f"Error: {e}")
else:
    print("Save file not found.")
