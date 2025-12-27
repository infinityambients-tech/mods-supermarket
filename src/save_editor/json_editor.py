import json
import shutil
from pathlib import Path
from .backup_system import BackupSystem

class SaveEditor:
    def __init__(self):
        self.backup_system = BackupSystem()
    
    def modify_money(self, save_path, amount, operation='add'):
        """Modifies money in the save file."""
        return self._modify_field_generic(save_path, ['money', 'cash', 'balance', 'wallet', 'currentmoney'], amount, operation)

    def modify_level(self, save_path, level):
        """Modifies store level."""
        return self._modify_field_generic(save_path, ['storelevel', 'level'], level, 'set')

    def modify_xp(self, save_path, xp):
        """Modifies store XP."""
        return self._modify_field_generic(save_path, ['storeexperiencepoints', 'experience', 'xp'], xp, 'set')

    def modify_store_points(self, save_path, points):
        """Modifies store upgrade/expansion points."""
        return self._modify_field_generic(save_path, ['storeexpansionpoints', 'upgradepoints', 'points'], points, 'set')

    def unlock_all_licenses(self, save_path):
        """Unlocks all product licenses and ensures they show up."""
        try:
            self.backup_system.create_backup(save_path)
            with open(save_path, 'r', encoding='utf-8') as f:
                save_data = json.load(f)
            
            # IDs 21-105 are typical stable product licenses. Going too high can break game logic.
            safe_license_ids = list(range(21, 106))
            
            # Update multiple potential license keys to ensure visibility
            l1 = self._update_list_field(save_data, ['unlockedlicenses', 'licenses'], safe_license_ids)
            l2 = self._update_list_field(save_data, ['m_unlockedproductlicenses', 'unlockedproductlicenses'], safe_license_ids)
            
            if l1 or l2:
                self._save_es3_format(save_path, save_data)
                return True
            return False
        except Exception as e:
            print(f"Error unlocking licenses: {e}")
            return False

    def reset_licenses(self, save_path):
        """Resets licenses to basic (ID 21 only) to fix possible corruption."""
        try:
            self.backup_system.create_backup(save_path)
            with open(save_path, 'r', encoding='utf-8') as f:
                save_data = json.load(f)
            
            l1 = self._update_list_field(save_data, ['unlockedlicenses', 'licenses'], [21], overwrite=True)
            l2 = self._update_list_field(save_data, ['m_unlockedproductlicenses', 'unlockedproductlicenses'], [21], overwrite=True)
            
            self._save_es3_format(save_path, save_data)
            return True
        except Exception as e:
            print(f"Error resetting licenses: {e}")
            return False

    def _update_list_field(self, data, patterns, new_list, overwrite=False):
        """Recursively find lists and update them."""
        modified = False
        if isinstance(data, dict):
            for key, value in data.items():
                if key.lower() in patterns and isinstance(value, list):
                    if overwrite:
                        data[key] = sorted(new_list)
                    else:
                        current_ids = [int(i) for i in value if str(i).isdigit()]
                        data[key] = sorted(list(set(current_ids + new_list)))
                    modified = True
                elif isinstance(value, (dict, list)):
                    if self._update_list_field(value, patterns, new_list, overwrite):
                        modified = True
        elif isinstance(data, list):
            for item in data:
                if self._update_list_field(item, patterns, new_list, overwrite):
                    modified = True
        return modified

    def repair_interaction(self, save_path):
        """Fixes interaction/movement bugs by resetting specific stats to 1.0."""
        return self._modify_field_generic(save_path, ['movementspeed', 'speed', 'reachdistance', 'reach'], 1.0, 'set')

    def modify_rating(self, save_path, rating):
        """Modifies store rating/satisfaction."""
        return self._modify_field_generic(save_path, ['storerating', 'reputation', 'satisfaction', 'satisfactionpoints'], rating, 'set')

    def boost_staff_stats(self, save_path, multiplier=10):
        """Boosts speed and accuracy for all hired employees."""
        try:
            self.backup_system.create_backup(save_path)
            with open(save_path, 'r', encoding='utf-8') as f:
                save_data = json.load(f)
            
            modified = self._find_and_boost_staff(save_data, multiplier)
            
            if modified:
                with open(save_path, 'w', encoding='utf-8') as f:
                    json.dump(save_data, f, indent=2)
                return True
            return False
        except Exception as e:
            print(f"Error boosting staff: {e}")
            return False

    def _find_and_boost_staff(self, data, mult):
        """Recursively find employee lists and boost stats safely."""
        modified = False
        if isinstance(data, dict):
            for key, value in data.items():
                # Strictly target identifying keys for employee lists
                if key.lower() in ['purchasedemployees', 'hiredemployees', 'cashiers', 'restockers'] and isinstance(value, list):
                    for emp in value:
                        if isinstance(emp, dict):
                            # Boost only internal employee fields
                            for s_key in list(emp.keys()):
                                if s_key.lower() in ['speed', 'movementspeed', 'accuracy', 'workspeed']:
                                    emp[s_key] = 10.0
                                    modified = True
                elif isinstance(value, (dict, list)):
                    if self._find_and_boost_staff(value, mult):
                        modified = True
        elif isinstance(data, list):
            for item in data:
                if self._find_and_boost_staff(item, mult):
                    modified = True
        return modified


    def _modify_field_generic(self, save_path, field_patterns, value, operation):
        try:
            self.backup_system.create_backup(save_path)
            with open(save_path, 'r', encoding='utf-8') as f:
                save_data = json.load(f)
            
            modified = self._find_and_modify_field(save_data, field_patterns, value, operation)
            
            if modified:
                self._save_es3_format(save_path, save_data)
                return True
            return False
        except Exception as e:
            print(f"Error modifying save: {e}")
            return False

    def _save_es3_format(self, path, data):
        """Saves JSON with ES3-compatible formatting (Tabs, Spaces)."""
        content = json.dumps(data, indent="\t")
        # ES3 often uses "key" : "value" (space before colon)
        content = content.replace('": ', '" : ')
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)

    def _find_and_modify_field(self, data, field_patterns, new_val, operation):
        """Recursively search for fields matching patterns, handles ES3 'value' wrapper."""
        if isinstance(data, dict):
            for key, value in data.items():
                if key.lower() in field_patterns:
                    # Handle both direct value and ES3 { "__type": ..., "value": ... }
                    if isinstance(value, (int, float)):
                        if operation == 'add': data[key] = value + new_val
                        elif operation == 'set': data[key] = new_val
                        return True
                    elif isinstance(value, dict) and "value" in value:
                        # Modify the nested value
                        v = value["value"]
                        if isinstance(v, (int, float)):
                            if operation == 'add': value["value"] = v + new_val
                            elif operation == 'set': value["value"] = new_val
                            return True
                
                # Recursive search
                if isinstance(value, (dict, list)):
                    if self._find_and_modify_field(value, field_patterns, new_val, operation):
                        return True
        elif isinstance(data, list):
            for item in data:
                if self._find_and_modify_field(item, field_patterns, new_val, operation):
                    return True
        return False
    
    def get_current_stats(self, save_path):
        """Reads current money, level, and XP from save file."""
        try:
            with open(save_path, 'r', encoding='utf-8') as f:
                save_data = json.load(f)
            return {
                'money': self._find_field_value(save_data, ['money', 'cash', 'balance', 'wallet', 'currentmoney']),
                'level': self._find_field_value(save_data, ['storelevel', 'level']),
                'xp': self._find_field_value(save_data, ['storeexperiencepoints', 'experience', 'xp']),
                'points': self._find_field_value(save_data, ['storeexpansionpoints', 'upgradepoints', 'points']),
                'rating': self._find_field_value(save_data, ['storerating', 'reputation', 'satisfaction', 'satisfactionpoints'])
            }
        except Exception:
            return {'money': 0, 'level': 0, 'xp': 0, 'points': 0, 'rating': 0}
            
    def _find_field_value(self, data, field_patterns):
        """Recursively retrieve field value, handles ES3 'value' wrapper."""
        if isinstance(data, dict):
            for key, value in data.items():
                if key.lower() in field_patterns:
                    if isinstance(value, (int, float)):
                        return value
                    elif isinstance(value, dict) and "value" in value:
                        v = value["value"]
                        if isinstance(v, (int, float)):
                            return v
                
                if isinstance(value, (dict, list)):
                    val = self._find_field_value(value, field_patterns)
                    if val is not None: return val
        return None
