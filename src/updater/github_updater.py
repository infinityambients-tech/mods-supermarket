import requests
import zipfile
import io
import os
import shutil
from pathlib import Path

class GitHubUpdater:
    def __init__(self, repo_owner, repo_name, current_version):
        self.repo_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}"
        self.current_version = current_version
    
    def check_for_updates(self):
        try:
            response = requests.get(f"{self.repo_url}/releases/latest", timeout=5)
            if response.status_code == 200:
                latest_release = response.json()
                latest_version = latest_release.get('tag_name', '').lstrip('v')
                
                if self.is_newer(latest_version):
                    return {
                        'available': True,
                        'version': latest_version,
                        'download_url': latest_release.get('zipball_url') or latest_release['assets'][0]['browser_download_url'],
                        'body': latest_release.get('body', '')
                    }
            return {'available': False}
        except Exception as e:
            print(f"Update check failed: {e}")
            return {'available': False}

    def is_newer(self, remote_version):
        try:
            v1_parts = [int(p) for p in self.current_version.split('.')]
            v2_parts = [int(p) for p in remote_version.split('.')]
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
                return True
            return False
        except Exception as e:
            print(f"Update download failed: {e}")
            return False

    def apply_update(self):
        """Applies the update by creating a replacement script."""
        if not hasattr(self, 'content_dir') or not self.content_dir.exists():
            return False
            
        try:
            # Create a batch script to replace files after app closes
            # It waits 2 seconds, moves files, deletes itself
            batch_content = f"""@echo off
timeout /t 2 /nobreak > nul
xcopy /s /e /y "{self.content_dir.absolute()}\\*" .
rd /s /q "update_temp"
start python money_mods.py
del "%~f0"
"""
            with open("updater_helper.bat", "w") as f:
                f.write(batch_content)
            
            # Run the batch script and exit current app
            os.startfile("updater_helper.bat")
            return True
        except Exception as e:
            print(f"Failed to prepare update application: {e}")
            return False
