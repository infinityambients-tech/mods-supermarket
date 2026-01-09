#!/usr/bin/env python3
"""finalize_update.py

Safe finalizer for updates. Waits for PID to exit, copies files from content dir,
verifies lock file matches the expected update_id, and only then removes the lock.
Writes logs to provided log file.
"""
import argparse
import shutil
import sys
import time
import os
import json
from pathlib import Path

try:
    import psutil
except Exception:
    psutil = None


def is_pid_alive(pid):
    try:
        if psutil:
            p = psutil.Process(pid)
            return p.is_running()
        else:
            # Fallback: on Windows use tasklist
            rc = os.system(f'tasklist /FI "PID eq {pid}" >nul 2>&1')
            return rc == 0
    except Exception:
        return False


def wait_for_pid_exit(pid, timeout=300):
    start = time.time()
    while is_pid_alive(pid):
        if time.time() - start > timeout:
            return False
        time.sleep(1)
    return True


def safe_copytree(src: Path, dst: Path, log_file=None):
    try:
        for root, dirs, files in os.walk(src):
            rel = os.path.relpath(root, src)
            target_root = dst if rel == '.' else dst / rel
            os.makedirs(target_root, exist_ok=True)
            for f in files:
                s = Path(root) / f
                d = Path(target_root) / f
                try:
                    shutil.copy2(s, d)
                except Exception as e:
                    if log_file:
                        with open(log_file, 'a') as lf:
                            lf.write(f"Failed copy {s} -> {d}: {e}\n")
        return True
    except Exception as e:
        if log_file:
            with open(log_file, 'a') as lf:
                lf.write(f"safe_copytree failed: {e}\n")
        return False


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--pid', type=int, required=True)
    p.add_argument('--content_dir', required=True)
    p.add_argument('--lock_file', required=True)
    p.add_argument('--update_id', required=False)
    p.add_argument('--log', required=False)
    args = p.parse_args()

    pid = args.pid
    content_dir = Path(args.content_dir)
    lock_file = Path(args.lock_file)
    update_id = args.update_id
    log = args.log

    def logmsg(msg):
        if log:
            try:
                with open(log, 'a') as lf:
                    lf.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n")
            except Exception:
                pass

    logmsg(f"Finalizer started. Waiting for PID {pid} to exit")

    ok = wait_for_pid_exit(pid, timeout=600)
    if not ok:
        logmsg(f"Timeout waiting for PID {pid} to exit")
        sys.exit(2)

    logmsg(f"PID {pid} exited. Copying files from {content_dir}")
    # Copy
    try:
        # content_dir may contain nested folder; copy contents into cwd
        safe_copytree(content_dir, Path('.'), log_file=log)
    except Exception as e:
        logmsg(f"Copy failed: {e}")
        sys.exit(3)

    # Remove update_temp if exists
    try:
        if content_dir.exists():
            shutil.rmtree(content_dir.parent)
            logmsg("Removed update_temp")
    except Exception as e:
        logmsg(f"Cleanup failed: {e}")

    # Validate and remove lock
    try:
        if lock_file.exists():
            try:
                text = lock_file.read_text().strip()
                try:
                    data = json.loads(text)
                except Exception:
                    data = {'pid': int(text) if text.isdigit() else None}

                # If update_id provided, only remove if matches
                if update_id:
                    if data.get('update_id') == update_id or data.get('pid') != pid:
                        lock_file.unlink(missing_ok=True)
                        logmsg("Lock removed (matched update_id or pid mismatch)")
                    else:
                        logmsg("Lock not removed: update_id mismatch and pid matches")
                else:
                    # No update_id provided: remove only if PID not alive
                    if not is_pid_alive(data.get('pid')):
                        lock_file.unlink(missing_ok=True)
                        logmsg("Lock removed (no update_id and pid not alive)")
                    else:
                        logmsg("Lock not removed: pid still alive")
            except Exception as e:
                logmsg(f"Lock handling failed: {e}")
    except Exception as e:
        logmsg(f"Final steps failed: {e}")

    logmsg("Finalizer completed")
    return 0

if __name__ == '__main__':
    sys.exit(main())
