#!/usr/bin/env python3
"""List, fetch and inspect the Lab's temporary original camera photos.

  list                      newest first (up to 100)
  latest [--max-age MIN]    fetch the newest; refuse if older than MIN minutes
  wait [--timeout SEC]      wait for a photo that arrives after now, then fetch it
  fetch NAME                fetch one photo by name
  status                    server storage and retention timer
  phone                     read-only adb check of the camera phone and its uploads
"""
import argparse
import json
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
import time

HOST = 'rdulx009'
ROOT = '/srv/lab-photos/inbox'
CACHE = Path(__file__).resolve().parent / 'cache'
FOLDERSYNC = 'dk.tacit.android.foldersync.lite'
CAMERA_DIR = '/storage/emulated/0/DCIM/Camera'
PHOTO_EXT = ('.jpg', '.jpeg', '.png', '.webp', '.heic', '.heif')
REMOTE = '''import json, pathlib, stat
root=pathlib.Path('/srv/lab-photos/inbox')
out=[]
for p in root.rglob('*'):
 s=p.lstat()
 if stat.S_ISREG(s.st_mode) and p.suffix.lower() in ('.jpg','.jpeg','.png','.webp','.heic','.heif'):
  out.append(dict(name=str(p.relative_to(root)),bytes=s.st_size,modified=s.st_mtime,arrived=s.st_ctime))
print(json.dumps(sorted(out,key=lambda x:x['arrived'],reverse=True)))
'''


class PhotoError(Exception):
    pass


def ssh(command, **kwargs):
    try:
        return subprocess.run(['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=10', HOST, command],
                              check=True, **kwargs)
    except FileNotFoundError:
        raise PhotoError('OpenSSH client (ssh) is not installed.')
    except subprocess.CalledProcessError as exc:
        raise PhotoError(f'Could not reach {HOST} over SSH (exit {exc.returncode}). '
                         'Check the lab network and your SSH alias/key.')


def list_rows():
    return json.loads(ssh('python3 -c ' + shlex.quote(REMOTE), capture_output=True, text=True).stdout)


def server_now():
    return float(ssh('date +%s.%N', capture_output=True, text=True).stdout)


def fetch(row):
    if row['bytes'] > 100 * 1024**2:
        raise PhotoError('Photo exceeds the 100 MiB download limit.')
    CACHE.mkdir(exist_ok=True)
    # Cache is disposable; oldest local copies go first, capped at 1 GiB.
    cached = sorted((p for p in CACHE.iterdir() if p.is_file()), key=lambda p: p.stat().st_mtime)
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
            raise PhotoError('Photo changed during download; retry.')
        partial.replace(dest)
    finally:
        partial.unlink(missing_ok=True)
    return dest


def latest(max_age_min=None):
    rows = list_rows()
    if not rows:
        raise PhotoError('No photos in the inbox yet.')
    row = rows[0]
    if max_age_min is not None:
        age = (server_now() - row['arrived']) / 60
        if age > max_age_min:
            raise PhotoError(f"Newest photo {row['name']} arrived {age:.0f} min ago, "
                             f'older than {max_age_min} min. Take a new photo or use fetch NAME.')
    return fetch(row)


def wait(timeout=300, interval=4, clock=time.monotonic, sleep=time.sleep):
    """Return the first photo that arrives on the server after this call starts."""
    start = server_now()
    deadline = clock() + timeout
    print(f'Waiting up to {timeout} s for a new photo...', file=sys.stderr)
    while True:
        new = [r for r in list_rows() if r['arrived'] > start]
        if new:
            # Give a burst a moment to finish, then take the oldest new one.
            sleep(interval)
            new = sorted((r for r in list_rows() if r['arrived'] > start), key=lambda r: r['arrived'])
            if len(new) > 1:
                print(f'{len(new)} new photos arrived; fetching the first. Others: '
                      + ', '.join(r['name'] for r in new[1:]), file=sys.stderr)
            return fetch(new[0])
        if clock() >= deadline:
            raise PhotoError(f'No new photo arrived within {timeout} s. Is the phone on lab Wi-Fi '
                             'and is FolderSync showing its monitoring notification?')
        sleep(interval)


def adb(*args):
    return subprocess.run(['adb', *args], capture_output=True, text=True, timeout=30).stdout.replace('\r', '')


def phone_check():
    """Read-only checks; never changes phone settings or files."""
    if not shutil.which('adb'):
        raise PhotoError('adb is not installed (sudo apt-get install adb).')
    devices = [l.split()[0] for l in adb('devices').splitlines()[1:] if l.strip().endswith('device')]
    if not devices:
        raise PhotoError('No phone visible to adb. Connect USB and allow USB debugging.')
    sh = lambda *a: adb('-s', devices[0], 'shell', *a)
    results = []
    def check(label, ok, detail=''):
        results.append(ok)
        print(f"[{'ok' if ok else 'FAIL'}] {label}" + (f': {detail}' if detail else ''))
    model = sh('getprop', 'ro.product.model').strip()
    check('Phone', True, f"{model}, Android {sh('getprop', 'ro.build.version.release').strip()}")
    pkg = sh('dumpsys', 'package', FOLDERSYNC)
    version = next((l.split('=', 1)[1] for l in pkg.splitlines() if 'versionName=' in l), '')
    check('FolderSync installed', bool(version), version or 'missing')
    check('FolderSync not force-stopped', 'stopped=false' in pkg)
    check('Battery optimization exempt', FOLDERSYNC in sh('dumpsys', 'deviceidle', 'whitelist'))
    services = sh('dumpsys', 'activity', 'services', FOLDERSYNC)
    check('Instant sync service running in foreground',
          'InstantSyncService' in services and 'isForeground=true' in services)
    check('Automatic date/time', sh('settings', 'get', 'global', 'auto_time').strip() == '1',
          'filenames are capture timestamps')
    phone = {n for n in sh('ls', CAMERA_DIR).split() if n.lower().endswith(PHOTO_EXT)}
    server = {Path(r['name']).name for r in list_rows()}
    missing = sorted(phone - server)
    # Expired server copies are expected; only recent phone photos must be present.
    recent_missing = [n for n in missing if n[:8] >= time.strftime('%Y%m%d', time.localtime(time.time() - 13 * 86400))]
    check('Recent camera photos all on server', not recent_missing,
          f'{len(phone)} on phone, missing: {", ".join(recent_missing[:10])}' if recent_missing
          else f'{len(phone)} on phone')
    return all(results)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('action', choices=['list', 'latest', 'wait', 'fetch', 'status', 'phone'])
    parser.add_argument('name', nargs='?')
    parser.add_argument('--max-age', type=float, help='latest: refuse photos older than this many minutes')
    parser.add_argument('--timeout', type=int, default=300, help='wait: seconds (default 300)')
    args = parser.parse_args()
    try:
        if args.action == 'status':
            ssh('df -h /srv/lab-photos; systemctl is-active lab-photo-retention.timer; '
                'systemctl show lab-photo-retention.service -p Result -p ExecMainExitTimestamp')
        elif args.action == 'list':
            print(json.dumps(list_rows()[:100], indent=2))
        elif args.action == 'latest':
            print(latest(args.max_age))
        elif args.action == 'wait':
            print(wait(args.timeout))
        elif args.action == 'phone':
            sys.exit(0 if phone_check() else 1)
        else:
            if not args.name:
                parser.error('fetch needs a photo NAME (see list).')
            rows = [r for r in list_rows() if r['name'] == args.name]
            if not rows:
                raise PhotoError(f'{args.name} is not in the inbox (it may have expired).')
            print(fetch(rows[0]))
    except PhotoError as exc:
        sys.exit(f'Photo error: {exc}')


if __name__ == '__main__':
    main()
