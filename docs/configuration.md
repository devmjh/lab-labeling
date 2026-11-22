# Deployment configuration

Recorded 2026-11-21. Phone settings below are from the supplied, previously verified
runbook. Server mount, SFTP configuration and timer were read back during consolidation.

| Component | Configuration |
| --- | --- |
| Camera | Dedicated Samsung SM-G990U1, Android 16 (read back 2026-11-22), normal Camera app |
| Upload application | FolderSync 4.16.0, account `Lab-Photos`, folder pair `Lab-Camera` |
| Source | `/storage/emulated/0/DCIM/Camera` |
| SFTP destination | `rdulx009.labnet.int:22`, user `labphoto`, chroot-relative `/inbox` |
| Server | rdulx009, `192.168.4.98` |
| Actual inbox | `/srv/lab-photos/inbox` |
| Filesystem | 12 GiB preallocated `/var/lib/lab-photos.ext4`, mounted at `/srv/lab-photos` |
| Mount flags | `loop,nodev,nosuid,noexec,nofail` in `/etc/fstab` |
| Retention | 14 days by server ctime; prune oldest eligible files above 8 GiB; protect last hour |
| Scheduler | `lab-photo-retention.timer`: boot +2 min, then every 5 min |
| Reader | Existing SSH agent account; Windows alias `rdulx009` uses `rduadmin` |
| Client cache | `lab-photos/cache/`, disposable, 1 GiB; maximum individual download 100 MiB |
| Live inventory | `C:\Users\james\Lab\Lab\Inventory` |
| Printer | Zebra GX420d, `192.168.4.113:9100`, raw ZPL over TCP |
| Label | 2.25 x 1.25 inches; 456 x 253 dots at nominal 203 dpi |
| Calibration | +5 mm vertical offset, `^LT40`; margin 8 dots; no border |

## Phone details

Instant sync and a five-minute recurring schedule are both enabled. File access,
notifications and battery-optimization exemption are enabled. Unlock after reboot
and confirm the monitoring notification; do not force-stop FolderSync.

One-way upload, temporary-file transfer, and "only resync source files if modified
(ignore target deletion)" are enabled. Delete synchronization and move/delete source
are disabled. Phone originals are retained, and server retention must not cause old
photos to upload again. Lab Wi-Fi/network reachability is required.

The installed include regex permits non-hidden JPEG/PNG/WebP/HEIC/HEIF photos and
excludes videos. The exact expression was not included in the source runbook and
has not been read back from the phone; verify it in FolderSync when rebuilding.
No folder include rule is configured. Do not substitute guessed settings silently.

The phone key is passphrase-protected in FolderSync's app-specific external files
directory. Existing recovery material remains on labnet007 in
`/home/jcollier/Documents/ChatGPT/AI Tech Lab/lab-photos/private/`; it was not copied
or read during consolidation. Configure credentials separately, never in this repo.
Server ED25519 fingerprint:
`SHA256:LG1y7JqKe5ZoPcczBUqeDkGkyx1QTfRKdHgzVPJJGEc`.

## Windows agent access

The photo reader uses the existing OpenSSH alias, not the restricted phone account:

```sshconfig
Host rdulx009
    HostName 192.168.4.98
    User rduadmin
    IdentityFile ~/.ssh/id_ed25519
    IdentitiesOnly yes
```

This documents the current machine, not a key to distribute. New machines need their
own approved account/key and verified host key. The client uses BatchMode and a
10-second connection timeout. It can run directly on Windows; labnet007 is not needed
as a jump host for inbox access.

## Server provisioning and recovery

`lab-photos/provision.sh` is the captured deployment script, not an automatic startup
step. Run only during a deliberate server setup/repair. It requires Linux, root,
OpenSSH server, systemd, Python 3, ext4 tools, and over 30 GiB available before initial
image creation. It expects these staged inputs:

```text
/tmp/lab-photo-setup/provision.sh
/tmp/lab-photo-setup/retention.py
/tmp/lab-photo-setup/phone.pub       # dedicated phone PUBLIC key only
```

Review the target host and existing filesystem first, then run
`sudo bash /tmp/lab-photo-setup/provision.sh`. The script reuses an existing backing
file; it must never be deleted/reformatted to make a re-run succeed. It replaces the
dedicated user's authorized key and service configuration, so it is not a harmless
status check. Retention can delete eligible inbox files immediately on installation.

The SFTP account has no shell, forwarding or TTY; it is chrooted and key-only.
Authorized keys live in `/etc/ssh/authorized_keys/labphoto`; restrictions in
`/etc/ssh/sshd_config.d/60-lab-photo.conf`. The retention executable is installed as
`/usr/local/sbin/lab-photo-retention`. The provisioning source includes both systemd
unit definitions. Service hardening permits writes only to the photo filesystem
and `/run`; the script refuses cleanup if the dedicated filesystem is not mounted.

Use `python lab-photos/photos.py status` and server journal checks for diagnosis.
Stop the timer to pause expiry; remove the dedicated authorized key to disable uploads.
Do not unmount/delete the backing file as a routine troubleshooting step.

## Ownership and backups

Git tracks code/configuration documentation. Obsidian owns inventory content. The
inbox and download cache are temporary, not backups. Preserve selected evidence
outside both before expiry. Do not place private recovery keys in the vault or repo.
This project does not change the vault's existing backup or synchronization setup.
