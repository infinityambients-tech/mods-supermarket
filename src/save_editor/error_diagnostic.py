import os
import time
import json
from pathlib import Path

class ErrorDiagnosticSystem:
    def __init__(self):
        self.diagnostic_log = []

    def diagnose_modification_error(self, save_path: str, stat_type: str, attempted_value) -> dict:
        diagnosis = {
            'timestamp': time.time(),
            'save_path': save_path,
            'stat_type': stat_type,
            'attempted_value': attempted_value,
            'issues': [],
            'file_info': {},
            'structure_analysis': {}
        }

        diagnosis['file_info'] = self._analyze_file(save_path)
        diagnosis['permission_check'] = self._check_permissions(save_path)
        diagnosis['game_status'] = self._check_game_status()
        diagnosis['structure_analysis'] = self._analyze_structure(save_path)

        # Basic issue identification
        if not diagnosis['file_info'].get('exists'):
            diagnosis['issues'].append('Plik save nie istnieje')
        if not diagnosis['permission_check'].get('can_write'):
            diagnosis['issues'].append('Brak uprawnień do zapisu pliku')
        if diagnosis['permission_check'].get('is_locked'):
            diagnosis['issues'].append('Plik jest zablokowany przez inny proces')
        if diagnosis['game_status'].get('is_running'):
            diagnosis['issues'].append('Gra jest uruchomiona - zamyka plik save')
        if not diagnosis['structure_analysis'].get('is_valid_json'):
            diagnosis['issues'].append('Plik nie jest poprawnym JSON')

        return diagnosis

    def _analyze_file(self, file_path: str) -> dict:
        info = {'exists': False, 'size': 0, 'modified_time': None, 'is_json': False}
        try:
            p = Path(file_path)
            info['exists'] = p.exists()
            if info['exists']:
                info['size'] = p.stat().st_size
                info['modified_time'] = time.ctime(p.stat().st_mtime)
                try:
                    with open(p, 'r', encoding='utf-8') as f:
                        s = f.read(100)
                        info['is_json'] = s.strip().startswith('{')
                except Exception:
                    info['is_json'] = False
        except Exception as e:
            info['error'] = str(e)
        return info

    def _check_permissions(self, file_path: str) -> dict:
        perms = {'can_read': False, 'can_write': False, 'is_locked': False}
        try:
            perms['can_read'] = os.access(file_path, os.R_OK)
            perms['can_write'] = os.access(file_path, os.W_OK)
            perms['is_locked'] = self._is_file_locked(file_path)
        except Exception:
            pass
        return perms

    def _is_file_locked(self, filepath: str) -> bool:
        try:
            if os.path.exists(filepath):
                # try opening for append
                with open(filepath, 'a') as f:
                    f.write('')
                return False
        except Exception:
            return True
        return False

    def _check_game_status(self) -> dict:
        # Lightweight check: look for processes with 'supermarket' in name
        status = {'is_running': False, 'processes': []}
        try:
            import psutil
            for proc in psutil.process_iter(['name','pid']):
                name = proc.info.get('name') or ''
                if 'supermarket' in name.lower():
                    status['is_running'] = True
                    status['processes'].append({'pid': proc.info.get('pid'),'name':name})
        except Exception:
            pass
        return status

    def _analyze_structure(self, file_path: str) -> dict:
        analysis = {'is_valid_json': False, 'depth': 0, 'key_count': 0}
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            try:
                data = json.loads(content)
                analysis['is_valid_json'] = True
                # basic counts
                analysis['depth'] = self._calculate_json_depth(data)
                analysis['key_count'] = self._count_keys(data)
            except Exception:
                analysis['is_valid_json'] = False
        except Exception:
            analysis['error'] = 'Cannot read file'
        return analysis

    def _calculate_json_depth(self, obj, level=0):
        if isinstance(obj, dict):
            return max([self._calculate_json_depth(v, level + 1) for v in obj.values()] + [level])
        if isinstance(obj, list):
            return max([self._calculate_json_depth(v, level + 1) for v in obj] + [level])
        return level

    def _count_keys(self, obj):
        if isinstance(obj, dict):
            c = len(obj)
            for v in obj.values():
                c += self._count_keys(v)
            return c
        if isinstance(obj, list):
            c = 0
            for v in obj:
                c += self._count_keys(v)
            return c
        return 0
