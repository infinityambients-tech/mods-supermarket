import shutil
from pathlib import Path
from datetime import datetime

class BackupSystem:
    def create_backup(self, save_path):
        """Creates a backup of the save file."""
        if not save_path or not Path(save_path).exists():
            return None
            
        save_path = Path(save_path)
        backup_dir = save_path.parent / 'backups'
        backup_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = backup_dir / f"backup_{timestamp}_{save_path.name}"
        
        try:
            shutil.copy2(save_path, backup_path)
            return backup_path
        except Exception as e:
            print(f"Backup failed: {e}")
            return None
    def list_backups(self, save_path):
        """Lists available backups for a given save slot."""
        if not save_path: return []
        save_path = Path(save_path)
        backup_dir = save_path.parent / 'backups'
        if not backup_dir.exists(): return []
        
        backups = []
        for f in backup_dir.glob(f"backup_*_{save_path.name}"):
            backups.append({
                'name': f.name,
                'path': f,
                'date': datetime.fromtimestamp(f.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
            })
        
        return sorted(backups, key=lambda x: x['path'].stat().st_mtime, reverse=True)

    def restore_backup(self, backup_path, target_path):
        """Restores a backup to the target save path."""
        try:
            shutil.copy2(backup_path, target_path)
            return True
        except Exception as e:
            print(f"Restore failed: {e}")
            return False
