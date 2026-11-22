#!/usr/bin/env python3
"""Bounded inbox retention. Only this dedicated filesystem is managed."""
import fcntl
import json
import os
from pathlib import Path
import stat
import time

ROOT = Path(os.environ.get('PHOTO_ROOT', '/srv/lab-photos'))
MAX_BYTES = int(os.environ.get('PHOTO_MAX_BYTES', 8 * 1024**3))
MAX_AGE = int(os.environ.get('PHOTO_MAX_AGE', 14 * 86400))

def clean(root=ROOT, now=None):
    now = time.time() if now is None else now
    files = []
    deleted = 0
    for p in (root / 'inbox').rglob('*'):
        s = p.lstat()
        if stat.S_ISREG(s.st_mode):
            # ctime records arrival/last change even when the phone preserves mtime.
            files.append((s.st_ctime, s.st_size, p))
    total = sum(size for _, size, _ in files)
    for changed, size, p in sorted(files):
        # Never prune an active upload or a photo that arrived in the last hour.
        if now - changed < 3600:
            continue
        if now - changed > MAX_AGE or total > MAX_BYTES:
            p.unlink()
            total -= size
            deleted += 1
    result = dict(files_deleted=deleted, bytes_remaining=total, checked_at=now)
    print(json.dumps(result))
    return result

if __name__ == '__main__':
    if not os.path.ismount(ROOT):
        raise SystemExit('Refusing cleanup: dedicated photo filesystem is not mounted')
    with open('/run/lab-photo-retention.lock', 'w') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        clean()
