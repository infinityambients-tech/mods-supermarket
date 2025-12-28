
import json
import os

def find_save_file():
    # Common locations based on the game name "Supermarket Simulator" (or similar)
    local_app_data = os.environ.get('LOCALAPPDATA')
    user_profile = os.environ.get('USERPROFILE')
    
    possible_paths = []
    
    if user_profile:
        # Check LocalLow (Standard Unity) - using slot_0.es3 as found in debug script
        possible_paths.append(os.path.join(user_profile, "AppData", "LocalLow", "Nokta Games", "Supermarket Simulator", "slot_0.es3"))
    
    if local_app_data:
        # Check Local
        possible_paths.append(os.path.join(local_app_data, "Nokta Games", "Supermarket Simulator", "slot_0.es3"))

    for path in possible_paths:
        if os.path.exists(path):
            return path
            
    return None

def inspect_objects():
    save_file = find_save_file()
    if not save_file:
        print("Could not find slot_0.es3 in default location.")
        return

    print(f"Reading from: {save_file}")
    
    try:
        with open(save_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        print("--- Top Level Keys ---")
        print(list(data.keys()))
        
        progression = data.get('Progression', {})
        print("\n--- Progression Keys ---")
        # Progression might be a dict directly or valid JSON
        if isinstance(progression, dict):
            print(list(progression.keys()))
            
            val = progression.get('value', {})
            print("\n--- Progression/value Keys ---")
            if isinstance(val, dict):
                keys = list(val.keys())
                print(keys)
                
                # Filter for suspicious keys
                print("\n--- Potential Staff Keys ---")
                found = False
                for k in keys:
                    if any(s in k.lower() for s in ['emp', 'staff', 'worker', 'cashier', 'restocker', 'hired']):
                        print(f"Found: {k}")
                        found = True
                        # Print sample
                        sample = val[k]
                        if isinstance(sample, list) and len(sample) > 0:
                            print(json.dumps(sample[0], indent=2))
                        elif isinstance(sample, list):
                            print("[] (Empty List)")
                        else:
                            print(json.dumps(sample, indent=2))
                
                if not found:
                    print("No staff related keys found.")
                            
    except Exception as e:
        print(f"Error reading file: {e}")

if __name__ == "__main__":
    inspect_objects()
