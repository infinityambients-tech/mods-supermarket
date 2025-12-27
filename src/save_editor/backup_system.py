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
