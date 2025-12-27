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
        """Unlocks all product licenses."""
        try:
            # Create backup
            self.backup_system.create_backup(save_path)
            
            with open(save_path, 'r', encoding='utf-8') as f:
                save_data = json.load(f)
            
            # This is a bit more complex as it's usually a list
            # We'll search for the list and fill it with IDs 1-100 (enough for current game)
            modified = self._find_and_unlock_licenses(save_data)
            
            if modified:
                with open(save_path, 'w', encoding='utf-8') as f:
                    json.dump(save_data, f, indent=2)
                return True
            return False
        except Exception as e:
            print(f"Error unlocking licenses: {e}")
            return False

    def _find_and_unlock_licenses(self, data):
        """Recursively find unlockedLicenses list and populate it."""
        if isinstance(data, dict):
            for key, value in data.items():
                if key.lower() in ['unlockedlicenses', 'licenses']:
                    if isinstance(value, list):
                        # Add IDs 0 to 120 (approx max licenses)
                        data[key] = list(range(120))
                        return True
                
                if isinstance(value, (dict, list)):
                    if self._find_and_unlock_licenses(value):
                        return True
        elif isinstance(data, list):
            for item in data:
                if self._find_and_unlock_licenses(item):
                    return True
        return False

    def _modify_field_generic(self, save_path, field_patterns, value, operation):
        try:
            # Create backup first
            backup_path = self.backup_system.create_backup(save_path)
            if not backup_path:
                print("Warning: Backup could not be created.")
            
            # Load JSON
            with open(save_path, 'r', encoding='utf-8') as f:
                save_data = json.load(f)
            
            # Find and modify field
            modified = self._find_and_modify_field(save_data, field_patterns, value, operation)
            
            if modified:
                # Save changes
                with open(save_path, 'w', encoding='utf-8') as f:
                    json.dump(save_data, f, indent=2)
                return True
            else:
                print(f"Fields {field_patterns} not found.")
                return False
                
        except Exception as e:
            print(f"Error modifying save: {e}")
            return False

    def _find_and_modify_field(self, data, field_patterns, new_val, operation):
        """Recursively search for fields matching patterns."""
        if isinstance(data, dict):
            for key, value in data.items():
                if key.lower() in field_patterns:
                    if isinstance(value, (int, float)):
                        if operation == 'add':
                            data[key] = value + new_val
                        elif operation == 'set':
                            data[key] = new_val
                        return True
                
                # Recursive search
                if isinstance(value, dict):
                    if self._find_and_modify_field(value, field_patterns, new_val, operation):
                        return True
                elif isinstance(value, list):
                    for item in value:
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
                'points': self._find_field_value(save_data, ['storeexpansionpoints', 'upgradepoints', 'points'])
            }
        except Exception:
            return {'money': 0, 'level': 0, 'xp': 0, 'points': 0}
            
    def _find_field_value(self, data, field_patterns):
        if isinstance(data, dict):
            for key, value in data.items():
                if key.lower() in field_patterns:
                    if isinstance(value, (int, float)):
                        return value
                
                if isinstance(value, dict):
                    val = self._find_field_value(value, field_patterns)
                    if val is not None: return val
                elif isinstance(value, list):
                    for item in value:
                        val = self._find_field_value(item, field_patterns)
                        if val is not None: return val
        return None
