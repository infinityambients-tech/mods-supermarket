import os
import json
import winreg
import glob
import hashlib
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import psutil

class SupermarketSaveScanner:
    def __init__(self):
        self.found_saves = []
        self.game_process_name = "Supermarket Simulator.exe"
        self.save_patterns = ["*.json", "*.dat", "*.save", "*.sav", "*.bak", "*.backup", "*.es3"]
        self.save_keywords = ["save", "data", "game", "player", "profile", "slot"]
        
    def detect_game_installation(self) -> Dict[str, str]:
        """Detects all possible game installation locations"""
        locations = {
            'steam': None,
            'epic': None,
            'gog': None,
            'manual': [],
            'saves': []
        }
        
        # 1. Check Steam via Registry
        try:
            steam_path = self._get_steam_install_path()
            if steam_path:
                # Find Supermarket Simulator in Steam library
                steam_library = steam_path / "steamapps" / "common"
                game_path = self._find_game_in_directory(steam_library)
                if game_path:
                    locations['steam'] = str(game_path)
                    # Find saves in Steam Cloud
                    locations['saves'].extend(self._find_steam_cloud_saves(steam_path))
        except Exception as e:
            print(f"Steam detection error: {e}")
        
        # 2. Check standard Unity locations
        user_profile = os.environ.get('USERPROFILE')
        if user_profile:
            unity_paths = [
                Path(user_profile) / 'AppData' / 'LocalLow' / 'NoktaGames' / 'Supermarket Simulator',
                Path(user_profile) / 'AppData' / 'LocalLow' / 'Nokta Games' / 'Supermarket Simulator',
                Path(user_profile) / 'AppData' / 'Local' / 'NoktaGames',
                Path(user_profile) / 'Documents' / 'My Games' / 'Supermarket Simulator',
            ]
            
            for path in unity_paths:
                if path.exists():
                    locations['saves'].append(str(path))
                    save_files = self._scan_for_save_files(path)
                    self.found_saves.extend(save_files)
        
        # 3. Check running game processes
        game_process = self._find_running_game()
        if game_process:
            try:
                exe_path = Path(game_process.exe()).parent
                locations['manual'].append(str(exe_path))
                # Find saves in process folder
                save_path = exe_path / "Saves"
                if save_path.exists():
                    locations['saves'].append(str(save_path))
            except Exception as e:
                print(f"Error accessing process info: {e}")
        
        # 4. Full system scan (optional/fallback - mostly disabled for speed unless explicit)
        if not locations['saves'] and not self.found_saves:
             # Basic fallback scan in Documents if nothing else found
             pass 

        return locations
    
    def _get_steam_install_path(self) -> Optional[Path]:
        """Gets Steam install path from Registry"""
        try:
            # 64-bit Windows
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 
                                r"SOFTWARE\WOW6432Node\Valve\Steam")
            install_path, _ = winreg.QueryValueEx(key, "InstallPath")
            return Path(install_path)
        except WindowsError:
            try:
                # 32-bit Windows
                key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 
                                    r"SOFTWARE\Valve\Steam")
                install_path, _ = winreg.QueryValueEx(key, "InstallPath")
                return Path(install_path)
            except WindowsError:
                return None
    
    def _find_game_in_directory(self, directory: Path) -> Optional[Path]:
        """Helper to find game executable in a directory"""
        if directory.exists():
            for child in directory.iterdir():
                if child.is_dir() and "supermarket" in child.name.lower():
                    return child
        return None

    def _find_steam_cloud_saves(self, steam_path: Path) -> List[str]:
        """Finds Steam Cloud saves"""
        cloud_saves = []
        userdata_path = steam_path / "userdata"
        
        if userdata_path.exists():
            for user_id in userdata_path.iterdir():
                if user_id.is_dir():
                    # APP ID for Supermarket Simulator 
                    app_ids = ["2670630"]  # Example ID
                    
                    for app_id in app_ids:
                        remote_path = user_id / app_id / "remote"
                        if remote_path.exists():
                            cloud_saves.append(str(remote_path))
                            # Scan files in remote
                            save_files = self._scan_for_save_files(remote_path)
                            self.found_saves.extend(save_files)
        return cloud_saves
    
    def _find_running_game(self) -> Optional[psutil.Process]:
        """Finds running game process"""
        for proc in psutil.process_iter(['name', 'exe']):
            try:
                if proc.info['name'] and self.game_process_name.lower() in proc.info['name'].lower():
                    return proc
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return None
    
    def _scan_for_save_files(self, directory: Path) -> List[Dict]:
        """Scans directory for save files"""
        save_files = []
        
        if not directory.exists():
            return []

        for pattern in self.save_patterns:
            for file_path in directory.rglob(pattern):
                if self._is_likely_save_file(file_path):
                    save_info = self._analyze_save_file(file_path)
                    if save_info:
                        save_files.append(save_info)
        
        return save_files
    
    def _is_likely_save_file(self, file_path: Path) -> bool:
        """Checks if file is likely a save file"""
        filename = file_path.name.lower()
        
        if any(keyword in filename for keyword in self.save_keywords):
            return True
        
        if file_path.suffix.lower() in ['.json', '.dat', '.sav', '.es3']:
                return True
        
        try:
            file_size = file_path.stat().st_size
            if 1024 < file_size < 50 * 1024 * 1024:  # 1KB - 50MB
                return True
        except:
            pass
        
        return False
    
    def _analyze_save_file(self, file_path: Path) -> Optional[Dict]:
        """Analyzes save file and extracts info"""
        try:
            stats = file_path.stat()
            
            save_info = {
                'path': str(file_path),
                'filename': file_path.name,
                'size': stats.st_size,
                'modified': datetime.fromtimestamp(stats.st_mtime),
                'created': datetime.fromtimestamp(stats.st_ctime),
                'is_backup': self._is_backup_file(file_path),
                'slot_number': self._extract_slot_number(file_path),
                'checksum': self._calculate_checksum(file_path),
                'file_type': self._detect_file_type(file_path),
                'money_amount': None,
                'is_valid': False
            }
            
            content_info = self._read_save_content(file_path)
            if content_info:
                save_info.update(content_info)
                save_info['is_valid'] = True
            
            return save_info
            
        except Exception as e:
            print(f"Error analyzing {file_path}: {e}")
            return None

    def _is_backup_file(self, file_path: Path) -> bool:
        name = file_path.name.lower()
        return 'backup' in name or '.bak' in name

    def _extract_slot_number(self, file_path: Path) -> Optional[int]:
        import re
        match = re.search(r'slot_?(\d+)', file_path.name.lower())
        if match:
            return int(match.group(1))
        return None

    def _calculate_checksum(self, file_path: Path) -> str:
        try:
            return hashlib.md5(file_path.read_bytes()).hexdigest()
        except:
            return ""

    def _detect_file_type(self, file_path: Path) -> str:
        suffix = file_path.suffix.lower()
        if suffix == '.json' or suffix == '.es3': return 'json'
        if suffix == '.dat': return 'binary'
        return 'unknown'
    
    def _read_save_content(self, file_path: Path) -> Optional[Dict]:
        """Reads and analyzes save content"""
        try:
            if file_path.suffix.lower() in ['.json', '.es3']:
                return self._parse_json_save(file_path)
            elif file_path.suffix.lower() == '.dat':
                # Binary parsing placeholder
                return {'format': 'binary'}
            else:
                return {'format': 'unknown'}
        except:
            return None
    
    def _parse_json_save(self, file_path: Path) -> Dict:
        """Parses JSON save and finds money"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            result = {
                'format': 'json',
                'raw_preview': content[:500],
            }
            
            data = json.loads(content)
            money = self._find_money_in_structure(data)
            if money is not None:
                result['money_amount'] = money
                
            return result
        except Exception:
            return {'format': 'json_error'}
    
    def _find_money_in_structure(self, data) -> Optional[float]:
        """Recursively search for money value"""
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(key, str) and any(money_key in key.lower() 
                    for money_key in ['money', 'cash', 'balance', 'wallet', 'currency']):
                    if isinstance(value, (int, float)):
                        return float(value)
                
                if isinstance(value, (int, float)) and 1000 < value < 10000000:
                    pass # Heuristic check, can be risky if false positive
                
                if isinstance(value, (dict, list)):
                    result = self._find_money_in_structure(value)
                    if result is not None:
                        return result
        elif isinstance(data, list):
            for item in data:
                result = self._find_money_in_structure(item)
                if result is not None:
                    return result
        return None
    
    def _quick_system_scan(self) -> List[str]:
        # Implementation of quick scan can go here
        return []
