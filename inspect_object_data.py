
import json
import os

# Path to a save file - attempting to find one dynamically or use a fixed path if known
# Based on previous context, the user has save files.
# I'll try to find a save file in the common location or ask the user if needed.
# For now, I'll search in the standard AppData location or the user's workspace if one was copied there.

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
        print("Could not find SaveFile.es3 in default location.")
        return

    print(f"Reading from: {save_file}")
    
    try:
        with open(save_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        progression = data.get('Progression', {}).get('value', {})
        
        keys_to_inspect = [
            'DisplayDatas', 
            'CheckoutDatas', 
            'RackDatas', 
            'FurnitureDatas'
        ]
        
        for key in keys_to_inspect:
            items = progression.get(key, [])
            print(f"\n--- {key} (Count: {len(items)}) ---")
            if items and isinstance(items, list):
                # Print first item
                print(json.dumps(items[0], indent=2))
            elif items:
                print(f"Type: {type(items)}")
                print(json.dumps(items, indent=2))
            else:
                print("Empty or None")
                
    except Exception as e:
        print(f"Error reading file: {e}")

if __name__ == "__main__":
    inspect_objects()
