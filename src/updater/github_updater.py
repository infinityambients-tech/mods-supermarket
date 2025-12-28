import requests
import zipfile
import io
import os
import shutil
from pathlib import Path

class GitHubUpdater:
    LOG_FILE = os.path.join("logs", "updater_log.txt")
    LOCK_FILE = "update.lock"

    def __init__(self, repo_owner, repo_name, current_version):
        self.repo_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}"
        self.current_version = current_version
        
        # Ensure logs directory exists
        log_dir = os.path.dirname(self.LOG_FILE)
        if not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
            
        self._log(f"Updater initialized. Local version: {current_version}")
        self._cleanup_stale_lock()

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
        """Removes lock file if it's older than 5 minutes."""
        if os.path.exists(self.LOCK_FILE):
            try:
                age = os.path.getmtime(self.LOCK_FILE)
                if (os.path.getmtime(self.LOCK_FILE) - age) > 300:
                    os.remove(self.LOCK_FILE)
            except:
                pass

    def _acquire_lock(self):
        if os.path.exists(self.LOCK_FILE):
            return False
        with open(self.LOCK_FILE, "w") as f:
            f.write(str(os.getpid()))
        return True

    def _release_lock(self):
        if os.path.exists(self.LOCK_FILE):
            try:
                os.remove(self.LOCK_FILE)
            except:
                pass
    
    def check_for_updates(self):
        try:
            response = requests.get(f"{self.repo_url}/releases/latest", timeout=5)
            if response.status_code == 200:
                latest_release = response.json()
                latest_version = latest_release.get('tag_name', '').lstrip('v')
                
                # Check for lock
                if latest_version != self.current_version and os.path.exists(self.LOCK_FILE):
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
            
        if not self._acquire_lock():
            return False

        try:
            pid = os.getpid()
            # SAFETY: Aggressively remove the 'logs' directory from the source (update package)
            # This is critical to prevent "Sharing violation" errors when xcopy tries to
            # overwrite the log file that this script is currently writing to.
            # We never want to overwrite user logs with logs from the repo anyway.
            potential_logs_dir = self.content_dir / "logs"
            if potential_logs_dir.exists():
                try:
                    shutil.rmtree(potential_logs_dir)
                    self._log("Removed conflicting 'logs' directory from update package.")
                except Exception as e:
                    self._log(f"Warning: Could not remove 'logs' dir from update package: {e}")
            
            # Use absolute path for logs in batch script to avoid CWD issues
            log_abs_path = os.path.abspath(self.LOG_FILE)
            
            # Create a batch script to replace files after app closes
            # It waits for the parent process to exit, moves files, deletes itself
            batch_content = f"""@echo off
setlocal
set LOG_FILE={log_abs_path}
echo [%DATE% %TIME%] --- BATCH UPDATE STARTED --- >> "%LOG_FILE%"
echo [%DATE% %TIME%] Waiting for process {pid} to exit... >> "%LOG_FILE%"

:WAIT_LOOP
tasklist /FI "PID eq {pid}" 2>NUL | find /I /N "{pid}">NUL
if "%ERRORLEVEL%"=="0" (
    timeout /t 1 /nobreak > nul
    goto WAIT_LOOP
)

echo [%DATE% %TIME%] Process {pid} exited. Proceeding with file replacement. >> "%LOG_FILE%"

echo [%DATE% %TIME%] Copying files from {self.content_dir.absolute()}... >> "%LOG_FILE%"
xcopy /s /e /y "{self.content_dir.absolute()}\\*" . >> "%LOG_FILE%" 2>&1

if %ERRORLEVEL% NEQ 0 (
    echo [%DATE% %TIME%] ERROR: xcopy failed with code %ERRORLEVEL% >> "%LOG_FILE%"
) else (
    echo [%DATE% %TIME%] File replacement successful. >> "%LOG_FILE%"
)

echo [%DATE% %TIME%] Cleaning up... >> "%LOG_FILE%"
rd /s /q "update_temp" >> "%LOG_FILE%" 2>&1
del "{self.LOCK_FILE}" >> "%LOG_FILE%" 2>&1

echo [%DATE% %TIME%] Restarting application... >> "%LOG_FILE%"
start python money_mods.py >> "%LOG_FILE%" 2>&1

echo [%DATE% %TIME%] Update completed. >> "%LOG_FILE%"
del "%~f0"
"""
            with open("updater_helper.bat", "w") as f:
                f.write(batch_content)
            
            self._log("Update script created. Launching...")
            # Run the batch script and exit current app
            os.startfile("updater_helper.bat")
            return True
        except Exception as e:
            self._log(f"Failed to prepare update application: {e}")
            print(f"Failed to prepare update application: {e}")
            self._release_lock()
            return False
