#!/usr/bin/env python3
"""fix_update_lock.py

Non-interactive repair tool to clean stale `update.lock` files.

Usage:
  python fix_update_lock.py --auto    # non-interactive auto cleanup
  python fix_update_lock.py          # interactive when needed
"""
import argparse
import json
import os
import shutil
import sys
import time
from pathlib import Path


def is_pid_running(pid):
    try:
        import psutil
    except Exception:
        return False

    try:
        p = psutil.Process(pid)
        return p.is_running() and p.status() != psutil.STATUS_ZOMBIE
    except Exception:
        return False


def terminate_pid(pid, timeout=5):
    try:
        import psutil
    except Exception:
        return False

    try:
        p = psutil.Process(pid)
        p.terminate()
        p.wait(timeout=timeout)
        return True
    except Exception:
        return False


def backup_file(path: Path, backup_dir: Path):
    backup_dir.mkdir(parents=True, exist_ok=True)
    dest = backup_dir / f"{path.name}.backup.{int(time.time())}"
    shutil.copy2(path, dest)
    return dest


def handle_legacy_lock(lock_file: Path, auto: bool):
    with open(lock_file, 'r', encoding='utf-8') as f:
        content = f.read().strip()

    if not content:
        print("Empty lock file — removing.")
        backup = backup_file(lock_file, Path("lock_backups"))
        lock_file.unlink(missing_ok=True)
        print(f"Backed up to {backup}")
        return True

    if content.isdigit():
        pid = int(content)
        print(f"Legacy lock with PID: {pid}")

        running = is_pid_running(pid)
        if running:
            print(f"Process {pid} appears to be running.")
            if auto:
                print("Auto mode: will NOT terminate running process. Aborting removal.")
                return False
            else:
                choice = input("Terminate process and remove lock? (y/N): ")
                if choice.strip().lower() != 'y':
                    print("Aborted by user.")
                    return False
                print("Terminating process...")
                terminated = terminate_pid(pid)
                print("Terminated:" , terminated)

        # Backup then remove
        backup = backup_file(lock_file, Path("lock_backups"))
        lock_file.unlink(missing_ok=True)
        print(f"Lock removed. Backup: {backup}")
        return True

    # Not just digits — try JSON
    try:
        data = json.loads(content)
    except Exception:
        print("Unknown lock format — backing up and removing in auto mode.")
        if auto:
            backup = backup_file(lock_file, Path("lock_backups"))
            lock_file.unlink(missing_ok=True)
            print(f"Lock removed. Backup: {backup}")
            return True
        else:
            choice = input("Unknown lock format. Backup and remove? (y/N): ")
            if choice.strip().lower() != 'y':
                print("Aborted by user.")
                return False
            backup = backup_file(lock_file, Path("lock_backups"))
            lock_file.unlink(missing_ok=True)
            print(f"Lock removed. Backup: {backup}")
            return True

    # JSON parsed
    pid = data.get('pid')
    ts = data.get('timestamp') or os.path.getmtime(lock_file)
    age = time.time() - float(ts)
    print(f"JSON lock parsed. PID={pid}, age_seconds={int(age)}")

    # If process not alive, safe to remove
    if pid is None or not is_pid_running(pid):
        backup = backup_file(lock_file, Path("lock_backups"))
        lock_file.unlink(missing_ok=True)
        print(f"Stale lock removed. Backup: {backup}")
        return True

    # Process alive
    print(f"Process {pid} appears to be alive.")
    if auto:
        print("Auto mode: will NOT terminate running process. Aborting removal.")
        return False

    choice = input("Terminate process and remove lock? (y/N): ")
    if choice.strip().lower() != 'y':
        print("Aborted by user.")
        return False

    terminated = terminate_pid(pid)
    print("Terminated:", terminated)
    backup = backup_file(lock_file, Path("lock_backups"))
    lock_file.unlink(missing_ok=True)
    print(f"Lock removed. Backup: {backup}")
    return True


def main():
    parser = argparse.ArgumentParser(description="Repair stale update.lock files")
    parser.add_argument('--lock', '-l', default='update.lock', help='path to lock file')
    parser.add_argument('--auto', action='store_true', help='non-interactive auto cleanup (do not kill running processes)')
    args = parser.parse_args()

    lock_file = Path(args.lock)

    if not lock_file.exists():
        print("✓ No lock file found - nothing to do.")
        return 0

    print(f"Found lock file: {lock_file}")

    try:
        success = handle_legacy_lock(lock_file, auto=args.auto)
        if success:
            print("✓ Lock repair completed.")
            return 0
        else:
            print("⚠ Lock repair aborted or needs manual action.")
            return 2
    except Exception as e:
        print(f"❌ Error during repair: {e}")
        try:
            # attempt forced backup+remove
            backup = backup_file(lock_file, Path("lock_backups"))
            lock_file.unlink(missing_ok=True)
            print(f"Forced removal done. Backup: {backup}")
            return 0
        except Exception as e2:
            print(f"Failed forced removal: {e2}")
            return 1


if __name__ == '__main__':
    sys.exit(main())
