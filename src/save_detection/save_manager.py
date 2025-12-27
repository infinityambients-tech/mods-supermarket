from pathlib import Path
from datetime import datetime
import json
import shutil
import os
from typing import Dict, List

class MultiSaveManager:
    def __init__(self, scanner):
        self.scanner = scanner
        self.backup_folder = Path(os.environ.get('USERPROFILE', '')) / "SupermarketSaveBackups"
        self.backup_folder.mkdir(exist_ok=True)
    
    def find_and_classify_all_saves(self) -> Dict:
        """Finds and classifies all saves in system"""
        # Re-run detection to populate scanner.found_saves and locations
        self.scanner.found_saves = [] # Clear previous results
        self.scanner.detect_game_installation()
        
        all_saves = {
            'primary': None,
            'slots': [],
            'backups': [],
            'cloud': [],
            'old_versions': [] 
        }
        
        for save_info in self.scanner.found_saves:
            save_type = self._classify_save(save_info)
            
            if save_type == 'primary':
                all_saves['primary'] = save_info
            elif save_type == 'slot':
                all_saves['slots'].append(save_info)
            elif save_type == 'backup':
                all_saves['backups'].append(save_info)
            elif save_type == 'cloud':
                all_saves['cloud'].append(save_info)
            else:
                all_saves['old_versions'].append(save_info)
        
        # If no primary found, pick latest from slots or cloud
        if not all_saves['primary']:
            candidates = all_saves['slots'] + all_saves['cloud']
            if candidates:
                all_saves['primary'] = max(candidates, key=lambda x: x['modified'])
        
        return all_saves

    def _classify_save(self, save_info: Dict) -> str:
        path = str(save_info['path']).lower()
        name = save_info['filename'].lower()
        
        if 'steam' in path and 'remote' in path:
            return 'cloud'
        if 'backup' in name or '.bak' in name:
            return 'backup'
        if 'slot' in name:
            return 'slot'
        if 'savedata.json' in name:
            # Assume standard save is primary if it matches standard name
            return 'slot' # effectively a slot, will be promoted if best candidate
        return 'old_versions'
    
    def modify_all_saves(self, amount: float, operation: str = 'set') -> Dict:
        """Modifies all found saves"""
        results = {
            'success': [],
            'failed': [],
            'backups_created': [],
            'skipped': []
        }
        
        all_saves = self.find_and_classify_all_saves()
        
        targets = []
        if all_saves['primary']: targets.append(all_saves['primary'])
        targets.extend(all_saves['slots'])
        targets.extend(all_saves['cloud'])

        # Deduplicate by path
        seen_paths = set()
        unique_targets = []
        for t in targets:
            if t['path'] not in seen_paths:
                unique_targets.append(t)
                seen_paths.add(t['path'])
        
        for save_info in unique_targets:
            result = self._modify_single_save(save_info, amount, operation)
            (results['success'] if result['success'] else results['failed']).append(result)
        
        return results
    
    def _modify_single_save(self, save_info: Dict, amount: float, operation: str) -> Dict:
        """Modifies a single save file"""
        try:
            backup_path = self._create_backup(save_info['path'])
            
            success = False
            if save_info['file_type'] == 'json':
                success = self._modify_json_save(save_info['path'], amount, operation)
            
            if success:
                return {
                    'success': True,
                    'file': save_info['path'],
                    'backup': backup_path,
                    'operation': operation
                }
            else:
                return {
                    'success': False,
                    'file': save_info['path'],
                    'error': 'Modification failed or file type not supported',
                    'backup': backup_path
                }
        except Exception as e:
            return {
                'success': False,
                'file': save_info['path'],
                'error': str(e),
                'backup': None
            }
    
    def _create_backup(self, original_path: str) -> str:
        original = Path(original_path)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{original.stem}_backup_{timestamp}{original.suffix}"
        backup_path = self.backup_folder / backup_name
        shutil.copy2(original, backup_path)
        return str(backup_path)
    
    def _modify_json_save(self, file_path: str, amount: float, operation: str) -> bool:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            modified = self._modify_money_fields(data, amount, operation)
            
            if modified:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2)
                return True
            return False
        except Exception as e:
            print(f"JSON modification error: {e}")
            return False
    
    def _modify_money_fields(self, data, amount: float, operation: str) -> bool:
        modified = False
        
        if isinstance(data, dict):
            for key, value in data.items():
                if self._is_money_field(key, value):
                    if operation == 'set':
                        data[key] = amount
                    elif operation == 'add':
                        data[key] = value + amount
                    elif operation == 'multiply':
                        data[key] = value * amount
                    modified = True
                
                if isinstance(value, (dict, list)):
                    if self._modify_money_fields(value, amount, operation):
                        modified = True
        
        elif isinstance(data, list):
            for item in data:
                if self._modify_money_fields(item, amount, operation):
                    modified = True
                    
        return modified
    
    def _is_money_field(self, key, value) -> bool:
        if not isinstance(value, (int, float)):
            return False
        
        key_str = str(key).lower()
        money_keywords = ['money', 'cash', 'balance', 'wallet', 'currency', 'funds', 'gold', 'currentmoney']
        
        if any(kw in key_str for kw in money_keywords):
            return True
        
        if 0 < value < 100000000:
             if isinstance(value, float) and value == round(value, 2):
                return True
        return False
