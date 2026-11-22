# Lab photo inbox

Installed and verified 2026-11-21. Samsung SM-G990U1 (Android 16 as of 2026-11-22), FolderSync 4.16.0 → rdulx009 over Lab Wi-Fi. Take photos with the normal Camera app; no USB connection or manual sharing is needed after setup. Ask an agent to inspect the latest Lab photo.

Verified: real camera photo `20261121_161536.jpg` arrived automatically; phone and agent copy have identical SHA-256 hashes. Synthetic uploads arrived in about 3–6 seconds, including with the screen off. Deleting a server test photo and syncing again did not cause it to re-upload.

Offline recovery also passed: a synthetic photo queued with Wi-Fi disabled uploaded automatically about 60 seconds after Wi-Fi was restored, on the next scheduled sync. There is no need to tap Sync after reconnecting; allow up to the five-minute schedule interval.

## Storage and access

Original photos live at `rdulx009:/srv/lab-photos/inbox` (LAN address `192.168.4.98`). Existing agent SSH accounts can read them. This is temporary working storage, not an archive or an identification service.

From the repository root (use `python` on Windows):

```bash
python3 lab-photos/photos.py list
python3 lab-photos/photos.py latest
python3 lab-photos/photos.py fetch 20261121_160000.jpg
python3 lab-photos/photos.py status
python3 lab-photos/photos.py wait          # next new photo
python3 lab-photos/photos.py latest --max-age 10
python3 lab-photos/photos.py phone         # read-only adb phone check
```

`latest` and `fetch` print a local absolute path suitable for an agent's image-viewing tool. Preserve full resolution when reading component markings. Record uncertain identifications as uncertain; request another angle when markings are unreadable.

## Storage limits

- Dedicated, preallocated **12 GiB filesystem**: uploads cannot grow into the rest of the host disk.
- Every five minutes, remove oldest eligible files above **8 GiB**, and expire files **14 days after arrival/last server change**.
- Protect uploads and photos changed within the last hour. A burst can fill the dedicated filesystem; transfers then fail and retry after space is available. The host remains bounded.
- Retention covers everything in this dedicated inbox, including abandoned upload files. It does not touch any other directory or delete phone originals.
- Agent download cache: **1 GiB** budget, 100 MiB maximum per fetched photo.
- Save worthwhile photos outside this temporary inbox before expiry. No automatic backup is configured.

## Installed phone configuration

Official free FolderSync installed from Google Play. Android file access, notifications and exemption from battery optimization are enabled. Its instant-sync foreground service is running. After restarting the phone, unlock it and confirm FolderSync's monitoring notification is present. Avoid force-stopping FolderSync.

SFTP account:

- Host: `rdulx009.labnet.int`, port `22` (DNS resolution and reachability verified from the phone).
- Username: `labphoto`
- Account name: `Lab-Photos`. Its password-encrypted key is stored in FolderSync's app-specific external files directory, not Downloads; the passphrase is configured in the app. Recovery material remains in the original labnet007 workspace's protected `lab-photos/private` folder (see configuration.md), not this repository. Never copy it into notes or commit it. The key grants only inbox SFTP access, without shell or forwarding.
- Verify server ED25519 fingerprint: `SHA256:LG1y7JqKe5ZoPcczBUqeDkGkyx1QTfRKdHgzVPJJGEc`.

Folder pair `Lab-Camera`: phone `/storage/emulated/0/DCIM/Camera` → remote `/inbox`, one-way upload. Instant sync, five-minute recurring schedule, temporary-file uploads, and **only resync source files if modified (ignore target deletion)** are enabled. Sync deletions and move/delete source files are disabled. An include filename regex permits non-hidden JPEG, PNG, WebP and HEIC/HEIF photos; videos are excluded. No folder include rule is configured, so subfolders are excluded by FolderSync's include-filter behavior. Camera folder was empty when configured.

The resync option prevents server retention from causing unchanged phone images to upload again. Phone originals remain on the phone; phone cleanup is not enabled. Lab network access is required. The five-minute schedule retries queued files when connectivity returns. This does not expose an Internet upload service.

References: https://foldersync.io/docs/help/guides/ and https://foldersync.io/docs/help/filters/

## Operations

`lab-photo-retention.timer` runs `/usr/local/sbin/lab-photo-retention`. Review with `journalctl -u lab-photo-retention.service`. SSH restrictions are in `/etc/ssh/sshd_config.d/60-lab-photo.conf`; key authorization is `/etc/ssh/authorized_keys/labphoto`.

The backing file is `/var/lib/lab-photos.ext4`, mounted through `/etc/fstab`. Keep it out of general backups if temporary photos are not wanted there. A mount failure prevents normal uploads because the underlying directory is root-owned and has no writable inbox. Retention also refuses to run without the mount.

To disable uploads, remove the dedicated authorized key. To pause expiry, stop `lab-photo-retention.timer`. Do not delete the backing file while mounted. Rebuilding this system is not a reason to overwrite an existing inbox.

## Verification, 2026-11-22

Read-only adb check of SM-G990U1 (Android 16, patch 2026-10-05): FolderSync 4.16.0 installed
and not stopped, exempt from battery optimization (standby bucket "exempt"), InstantSyncService
running as a foreground service, boot-start permission granted, automatic date/time on.
All 49 photos in DCIM/Camera were present in the server inbox; 2 older server photos had
been deleted on the phone, which is expected with one-way upload. Server: timer enabled and
active, ext4 mounted nodev/nosuid/noexec, 2% used, no retention warnings in two days, no
leftover partial uploads. These checks are now repeatable with `photos.py phone` and `status`.
