import os
from pathlib import Path

class SaveManager:
    def __init__(self):
        self.steam_paths = [
            Path(os.environ.get('USERPROFILE', '')) / 'AppData' / 'LocalLow' / 'NoktaGames' / 'Supermarket Simulator',
            Path(os.environ.get('USERPROFILE', '')) / 'AppData' / 'LocalLow' / 'Nokta Games' / 'Supermarket Simulator',
            Path(os.environ.get('USERPROFILE', '')) / 'Documents' / 'Supermarket Simulator',
        ]
    
    def find_save_file(self):
        """Auto-detect save file."""
        for path in self.steam_paths:
            if path.exists():
                save_files = list(path.rglob('*.json'))
                # Also check for .dat and .es3 if applicable
                save_files.extend(list(path.rglob('*.dat')))
                save_files.extend(list(path.rglob('*.es3')))
                
                for file in save_files:
                    # Look for likely save names
                    if 'save' in file.name.lower() or 'data' in file.name.lower():
                        return file
        return None

    def get_save_dir(self, save_file_path):
        if save_file_path:
            return Path(save_file_path).parent
        return None
