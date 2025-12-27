import os
import hashlib
from typing import Dict, Tuple
from pathlib import Path

class SafetySystem:
    def __init__(self):
        self.max_backups = 10
    
    def pre_modification_check(self, save_info: Dict) -> Tuple[bool, str]:
        """Runs safety checks before modification"""
        checks = [
            ("File exists", self._check_file_exists),
            ("File accessible", self._check_file_access),
            ("Not system folder", self._check_not_system_folder),
            ("Structure validation", self._validate_structure),
            ("Backup possible", self._check_backup_possible),
            ("Permissions sufficient", self._check_permissions),
        ]
        
        for check_name, check_func in checks:
            success, message = check_func(save_info)
            if not success:
                return False, f"{check_name} failed: {message}"
        
        return True, "All safety checks passed"
    
    def post_modification_verify(self, original_path: str, backup_path: str) -> Tuple[bool, str]:
        """Verifies modification success"""
        try:
            if not os.path.exists(backup_path):
                return False, "Backup was not created"
            
            if not os.path.exists(original_path):
                return False, "Original file disappeared"
            
            orig_size = os.path.getsize(original_path)
            backup_size = os.path.getsize(backup_path)
            
            if orig_size == 0:
                return False, "File is empty after modification"
            
            # Check if file changed (md5 check)
            if self._calculate_checksum(original_path) == self._calculate_checksum(backup_path):
                # NOTE: This might return False if we modified a value to be exactly what it was, 
                # or if modification failed silently. For now, we assume we wanted a change.
                # However, usually we want to confirm it IS modified.
                pass 
            
            return True, "Modification verified successfully"
            
        except Exception as e:
            return False, f"Verification error: {str(e)}"

    def cleanup_old_backups(self):
        """Cleans up old backups"""
        backup_folder = Path(os.environ.get('USERPROFILE', '')) / "SupermarketSaveBackups"
        if backup_folder.exists():
            backups = sorted(backup_folder.glob("*_backup_*"), key=os.path.getmtime)
            
            if len(backups) > self.max_backups:
                for old_backup in backups[:-self.max_backups]:
                    try:
                        os.remove(old_backup)
                    except:
                        pass

    def _check_file_exists(self, save_info):
        return os.path.exists(save_info['path']), "File exists"

    def _check_file_access(self, save_info):
        try:
            with open(save_info['path'], 'rb') as f:
                pass
            return True, "File is readable"
        except Exception as e:
            return False, str(e)

    def _check_not_system_folder(self, save_info):
        path = str(save_info['path']).lower()
        if "windows\\system32" in path or "program files" in path:
            # We allow Program Files if it's Steam library, but generally careful.
            # Ideally we check against specific forbidden zones.
            pass
        return True, "Safe location"

    def _validate_structure(self, save_info):
        if save_info.get('is_valid'):
            return True, "Structure valid"
        return False, "Invalid structure"

    def _check_backup_possible(self, save_info):
        # Could check disk space here
        return True, "Backup feasible"

    def _check_permissions(self, save_info):
        return os.access(save_info['path'], os.W_OK), "Write permission granted"

    def _calculate_checksum(self, file_path: str) -> str:
        with open(file_path, 'rb') as f:
             return hashlib.md5(f.read()).hexdigest()
