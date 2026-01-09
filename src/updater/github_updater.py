import requests
import zipfile
import io
import os
import shutil
from pathlib import Path
import sys

# Advanced lock manager
from advanced_lock import AdvancedLockManager

class GitHubUpdater:
    LOG_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "logs", "updater_log.txt")
    LOCK_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "update.lock")

    def __init__(self, repo_owner, repo_name, current_version):
        self.repo_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}"
        self.current_version = current_version
        
        # Ensure logs directory exists
        log_dir = os.path.dirname(self.LOG_FILE)
        if not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
            
        self._log(f"Updater initialized. Local version: {current_version}")
        # Use AdvancedLockManager for safer lock handling
        self.lock_manager = AdvancedLockManager(lock_file=self.LOCK_FILE)
        # Cleanup very old locks on startup
        try:
            self.lock_manager.cleanup_all_stale_locks(max_age_hours=1)
        except Exception:
            pass

    def _log(self, message):
        """Logs message to a file."""
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            with open(self.LOG_FILE, "a") as f:
                f.write(f"[{timestamp}] {message}\n")
        except:
            pass

    def _cleanup_stale_lock(self):
        # Legacy helper kept for backward compatibility (no-op now)
        return

    def _acquire_lock(self):
        # Acquire lock via AdvancedLockManager
        result = self.lock_manager.acquire_lock()
        return result.get('success', False)

    def _release_lock(self):
        try:
            return self.lock_manager.release_lock()
        except Exception:
            return {'success': False}
    
    def check_for_updates(self):
        try:
            self._log(f"Starting update check from {self.repo_url}...")
            print(f"DEBUG: Checking updates from {self.repo_url}")
            response = requests.get(f"{self.repo_url}/releases/latest", timeout=5)
            if response.status_code == 200:
                latest_release = response.json()
                latest_version = latest_release.get('tag_name', '').lstrip('v')
                
                # Check for lock
                if latest_version != self.current_version and Path(self.LOCK_FILE).exists():
                    lock_data = self.lock_manager._read_lock_file()
                    if lock_data and self.lock_manager._is_process_alive(lock_data.get('pid')):
                        print("Update in progress by another instance.")
                        return {'available': False}

                if self.is_newer(latest_version):
                    return {
                        'available': True,
                        'version': latest_version,
                        'download_url': latest_release.get('zipball_url') or latest_release['assets'][0]['browser_download_url'],
                        'body': latest_release.get('body', '')
                    }
            return {'available': False}
        except Exception as e:
            self._log(f"Update check failed: {e}")
            print(f"Update check failed: {e}")
            return {'available': False}

    def is_newer(self, remote_version):
        import re
        try:
            def parse_version(v):
                # Extract all number sequences from the string
                return [int(x) for x in re.findall(r'\d+', v)]
            
            v1_parts = parse_version(self.current_version)
            v2_parts = parse_version(remote_version)
            return v2_parts > v1_parts
        except:
            return False

    def download_update(self, download_url):
        """Downloads the update archive."""
        try:
            response = requests.get(download_url, stream=True, timeout=30)
            if response.status_code == 200:
                update_path = Path("update_temp")
                if update_path.exists():
                    shutil.rmtree(update_path)
                update_path.mkdir(exist_ok=True)
                
                # If it's a zip from GitHub releases
                with zipfile.ZipFile(io.BytesIO(response.content)) as z:
                    z.extractall("update_temp")
                
                # Usually GitHub zips have a root folder like 'repo-tagname'
                # Find the actual content folder
                root_folders = [f for f in update_path.iterdir() if f.is_dir()]
                if root_folders:
                    self.content_dir = root_folders[0]
                else:
                    self.content_dir = update_path
                self._log(f"Download successful. Extracted to {self.content_dir}")
                return True
            self._log(f"Download failed with status: {response.status_code}")
            return False
        except Exception as e:
            self._log(f"Update download failed: {e}")
            print(f"Update download failed: {e}")
            return False

    def apply_update(self):
        """Applies the update by creating a replacement script."""
        if not hasattr(self, 'content_dir') or not self.content_dir.exists():
            return False
        # Acquire lock
        if not self._acquire_lock():
            self._log("Could not acquire update lock - another update may be running.")
            return False

        try:
            pid = os.getpid()
            self._log(f"Preparing update script. Waiting for PID {pid}")

            # SAFETY: Remove updater_log.txt from source (update package) to prevent
            # "Sharing violation" when xcopy tries to overwrite the log file we are currently writing to.
            potential_log_in_update = self.content_dir / "logs" / "updater_log.txt"
            if potential_log_in_update.exists():
                try:
                    os.remove(potential_log_in_update)
                    self._log("Removed conflicting updater_log.txt from update package.")
                except Exception as e:
                    self._log(f"Warning: Could not remove log from update package: {e}")
            
            # Use absolute path for logs in batch script to avoid CWD issues
            log_abs_path = self.LOG_FILE
            
            # Create a batch script to replace files after app closes
            # It waits for the parent process to exit, moves files, deletes itself
            # Read lock to get update_id
            lock_data = None
            try:
                lock_data = self.lock_manager._read_lock_file()
            except Exception:
                lock_data = None

            update_id = lock_data.get('update_id') if lock_data else ''

            # Create a small batch that invokes the Python finalizer. The finalizer will
            # wait for PID to exit, copy files, and safely remove the lock only if it matches
            # the expected update_id.
            python_exe = sys.executable
            finalizer_cmd = f'"{python_exe}" "{Path(os.path.abspath("finalize_update.py")).as_posix()}" --pid {pid} --content_dir "{self.content_dir.absolute()}" --lock_file "{self.LOCK_FILE}" --update_id "{update_id}" --log "{log_abs_path}"'

            batch_content = f"""@echo off
setlocal
set LOG_FILE={log_abs_path}
echo [%DATE% %TIME%] --- BATCH UPDATE STARTED --- >> "%LOG_FILE%"
echo [%DATE% %TIME%] Launching finalizer... >> "%LOG_FILE%"
{finalizer_cmd}
echo [%DATE% %TIME%] Finalizer executed. >> "%LOG_FILE%"
echo [%DATE% %TIME%] Restarting application... >> "%LOG_FILE%"
start "" "{python_exe}" money_mods.py >> "%LOG_FILE%" 2>&1
echo [%DATE% %TIME%] Update completed. >> "%LOG_FILE%"
del "%~f0"
"""

            with open("updater_helper.bat", "w") as f:
                f.write(batch_content)

            self._log("Update script created. Launching finalizer batch...")
            os.startfile("updater_helper.bat")
            return True
        except Exception as e:
            self._log(f"Failed to prepare update application: {e}")
            print(f"Failed to prepare update application: {e}")
            self._release_lock()
            return False
