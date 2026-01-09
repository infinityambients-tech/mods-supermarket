import os
import time
import json
import uuid
import psutil
from pathlib import Path
from datetime import datetime
import threading


class AdvancedLockManager:
    def __init__(self, lock_file="update.lock", lock_timeout=300):
        self.lock_file = Path(lock_file)
        self.lock_timeout = lock_timeout
        self.current_pid = os.getpid()
        try:
            self.current_process = psutil.Process(self.current_pid)
        except Exception:
            self.current_process = None
        # Heartbeat control
        self._hb_thread = None
        self._hb_stop = threading.Event()

    def acquire_lock(self, operation_id=None):
        """Attempt to acquire a lock, cleaning stale/legacy locks when safe."""
        # Check existing lock
        if self.lock_file.exists():
            lock_data = self._read_lock_file()
            if lock_data:
                pid = lock_data.get('pid')
                if self._is_process_alive(pid):
                    lock_age = time.time() - lock_data.get('timestamp', 0)
                    if lock_age < self.lock_timeout:
                        return {
                            'success': False,
                            'reason': 'lock_active',
                            'pid': pid,
                            'age_seconds': lock_age,
                            'message': f'Aktualizacja już w toku (PID: {pid})'
                        }
                    else:
                        # process alive but lock timed out
                        self._force_cleanup_stale_lock(lock_data)
                else:
                    # process dead -> clear stale lock
                    self._clear_stale_lock(lock_data)

        # Create new lock
        lock_data = {
            'pid': self.current_pid,
            'timestamp': time.time(),
            'process_name': self.current_process.name() if self.current_process else None,
            'update_id': operation_id or str(uuid.uuid4()),
            'start_time': datetime.utcnow().isoformat() + 'Z',
            'timeout_seconds': self.lock_timeout,
            'step': 'acquiring_lock',
            'version': '2.0'
        }

        try:
            with open(self.lock_file, 'w', encoding='utf-8') as f:
                json.dump(lock_data, f, indent=2)
                f.flush()
                os.fsync(f.fileno())

            time.sleep(0.05)
            if self._verify_lock_integrity(lock_data):
                return {'success': True, 'lock_id': lock_data['update_id'], 'message': 'Lock uzyskany pomyślnie'}
            else:
                return {'success': False, 'reason': 'verification_failed', 'message': 'Nie udało się zweryfikować locka'}
        except Exception as e:
            return {'success': False, 'reason': 'write_error', 'error': str(e), 'message': f'Błąd tworzenia locka: {e}'}

    def _is_process_alive(self, pid):
        try:
            if pid is None:
                return False
            proc = psutil.Process(int(pid))
            return proc.is_running() and proc.status() != psutil.STATUS_ZOMBIE
        except (psutil.NoSuchProcess, psutil.AccessDenied, ValueError, TypeError):
            return False

    def _read_lock_file(self):
        try:
            with open(self.lock_file, 'r', encoding='utf-8') as f:
                content = f.read().strip()

            if content.isdigit():
                return {'pid': int(content), 'timestamp': os.path.getmtime(self.lock_file), 'legacy_format': True}
            else:
                return json.loads(content)
        except Exception:
            return None

    def _read_lock_file_from_path(self, path: Path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
            if content.isdigit():
                return {'pid': int(content), 'timestamp': os.path.getmtime(path), 'legacy_format': True}
            else:
                return json.loads(content)
        except Exception:
            return None

    def _clear_stale_lock(self, lock_data=None):
        try:
            if lock_data and lock_data.get('legacy_format'):
                self._log_cleanup('legacy_lock_cleared', lock_data)
            if self.lock_file.exists():
                backup = Path('lock_backups')
                backup.mkdir(exist_ok=True)
                shutil_dest = backup / f"{self.lock_file.name}.backup.{int(time.time())}"
                try:
                    # create a backup copy
                    from shutil import copy2
                    copy2(self.lock_file, shutil_dest)
                except Exception:
                    pass
                self.lock_file.unlink(missing_ok=True)
            return True
        except Exception:
            return False

    def _force_cleanup_stale_lock(self, lock_data):
        pid = lock_data.get('pid')
        try:
            proc = psutil.Process(pid)
            if 'SupermarketMoneyBooster' in (proc.name() or ''):
                try:
                    proc.terminate()
                    proc.wait(timeout=5)
                    self._log_cleanup('process_terminated', lock_data)
                except Exception:
                    pass
        except Exception:
            pass
        self._clear_stale_lock(lock_data)

    def update_lock_step(self, step_name, additional_data=None):
        if not self.lock_file.exists():
            return False
        try:
            lock_data = self._read_lock_file()
            if not lock_data:
                return False
            lock_data['step'] = step_name
            lock_data['last_update'] = time.time()
            if additional_data:
                lock_data.update(additional_data)
            with open(self.lock_file, 'w', encoding='utf-8') as f:
                json.dump(lock_data, f, indent=2)
            return True
        except Exception:
            return False

    def start_heartbeat(self, interval=5):
        """Start a background thread that periodically updates `last_heartbeat` in the lock file."""
        if self._hb_thread and self._hb_thread.is_alive():
            return True
        self._hb_stop.clear()

        def _hb():
            while not self._hb_stop.is_set():
                try:
                    if self.lock_file.exists():
                        data = self._read_lock_file()
                        if data and data.get('pid') == self.current_pid:
                            data['last_heartbeat'] = time.time()
                            with open(self.lock_file, 'w', encoding='utf-8') as f:
                                json.dump(data, f, indent=2)
                except Exception:
                    pass
                self._hb_stop.wait(interval)

        t = threading.Thread(target=_hb, daemon=True)
        self._hb_thread = t
        t.start()
        return True

    def stop_heartbeat(self):
        try:
            self._hb_stop.set()
            if self._hb_thread:
                self._hb_thread.join(timeout=1)
            self._hb_thread = None
        except Exception:
            pass
        return True

    def release_lock(self, success=True, message=None):
        if not self.lock_file.exists():
            return {'success': False, 'message': 'Lock nie istnieje'}
        try:
            lock_data = self._read_lock_file()
            report = {
                'release_time': datetime.utcnow().isoformat() + 'Z',
                'success': success,
                'message': message,
                'lock_duration': time.time() - lock_data.get('timestamp', time.time()) if lock_data else 0,
                'final_step': lock_data.get('step', 'unknown') if lock_data else 'unknown'
            }
            report_file = self.lock_file.with_suffix('.report.json')
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2)
            self.lock_file.unlink(missing_ok=True)
            return {'success': True, 'report': report, 'message': 'Lock zwolniony pomyślnie'}
        except Exception as e:
            return {'success': False, 'error': str(e), 'message': f'Błąd zwalniania locka: {e}'}

    def cleanup_all_stale_locks(self, max_age_hours=24):
        import glob
        patterns = ['*.lock', 'update.*.lock', '*.lock.json']
        for pattern in patterns:
            for path in glob.glob(pattern):
                try:
                    p = Path(path)
                    lock_age = time.time() - os.path.getmtime(p)
                    if lock_age > (max_age_hours * 3600):
                        lock_data = self._read_lock_file_from_path(p)
                        if lock_data and 'pid' in lock_data:
                            if not self._is_process_alive(lock_data['pid']):
                                try:
                                    p.unlink()
                                    self._log_cleanup('auto_cleaned', lock_data)
                                except Exception:
                                    pass
                except Exception:
                    continue
        return True

    def _verify_lock_integrity(self, lock_data):
        try:
            current = self._read_lock_file()
            if not current:
                return False
            return current.get('pid') == lock_data.get('pid') and current.get('update_id') == lock_data.get('update_id')
        except Exception:
            return False

    def _log_cleanup(self, action, lock_data):
        try:
            log = Path('lock_cleanup.log')
            entry = {'time': datetime.utcnow().isoformat() + 'Z', 'action': action, 'data': lock_data}
            with open(log, 'a', encoding='utf-8') as f:
                f.write(json.dumps(entry) + "\n")
        except Exception:
            pass
