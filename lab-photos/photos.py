#!/usr/bin/env python3
"""List, fetch and inspect the Lab's temporary original camera photos."""
import argparse
import json
from pathlib import Path
import shlex
import subprocess

HOST = 'rdulx009'
ROOT = '/srv/lab-photos/inbox'
CACHE = Path(__file__).resolve().parent / 'cache'
REMOTE = '''import json, pathlib, stat
root=pathlib.Path('/srv/lab-photos/inbox')
out=[]
for p in root.rglob('*'):
 s=p.lstat()
 if stat.S_ISREG(s.st_mode) and p.suffix.lower() in ('.jpg','.jpeg','.png','.webp','.heic','.heif'):
  out.append(dict(name=str(p.relative_to(root)),bytes=s.st_size,modified=s.st_mtime,arrived=s.st_ctime))
print(json.dumps(sorted(out,key=lambda x:x['arrived'],reverse=True)))
'''

def ssh(command, **kwargs):
    return subprocess.run(['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=10', HOST, command], check=True, **kwargs)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['list', 'latest', 'fetch', 'status'])
    parser.add_argument('name', nargs='?')
    args = parser.parse_args()
    if args.action == 'status':
        ssh('df -h /srv/lab-photos; systemctl is-active lab-photo-retention.timer; systemctl show lab-photo-retention.service -p Result -p ExecMainExitTimestamp')
        return
    rows = json.loads(ssh('python3 -c ' + shlex.quote(REMOTE), capture_output=True, text=True).stdout)
    if args.action == 'list':
        print(json.dumps(rows[:100], indent=2))
        return
    candidates = rows if args.action == 'latest' else [r for r in rows if r['name'] == args.name]
    if not candidates:
        raise SystemExit('No matching photos in the inbox yet.')
    row = candidates[0]
    if row['bytes'] > 100 * 1024**2:
        raise SystemExit('Photo exceeds the 100 MiB download limit.')
    CACHE.mkdir(exist_ok=True)
    # Cache is disposable; oldest local copies go first, capped at 1 GiB.
    cached = sorted((p for p in CACHE.iterdir() if p.is_file()), key=lambda p:p.stat().st_mtime)
    total = sum(p.stat().st_size for p in cached)
    for p in cached:
        if total + row['bytes'] <= 1024**3:
            break
        total -= p.stat().st_size
        p.unlink()
    dest = CACHE / Path(row['name']).name
    partial = dest.with_suffix(dest.suffix + '.partial')
    try:
        with partial.open('wb') as f:
            ssh('cat -- ' + shlex.quote(ROOT + '/' + row['name']), stdout=f)
        if partial.stat().st_size != row['bytes']:
            raise RuntimeError('Photo changed during download; retry.')
        partial.replace(dest)
    finally:
        partial.unlink(missing_ok=True)
    print(dest)

if __name__ == '__main__':
    main()
