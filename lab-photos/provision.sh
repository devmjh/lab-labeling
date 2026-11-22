#!/bin/bash
set -euo pipefail
test "$(id -u)" = 0
image=/var/lib/lab-photos.ext4
root=/srv/lab-photos
if ! test -e "$image"; then
    test "$(df --output=avail -B1 /var/lib | tail -1)" -gt 32212254720
    fallocate -l 12G "$image"
    chmod 600 "$image"
    mkfs.ext4 -q -E nodiscard -m 0 -L lab-photos "$image"
fi
mkdir -p "$root"
if ! grep -q '^/var/lib/lab-photos.ext4 ' /etc/fstab; then
    echo '/var/lib/lab-photos.ext4 /srv/lab-photos ext4 loop,nodev,nosuid,noexec,nofail 0 0' >> /etc/fstab
    systemctl daemon-reload
fi
mountpoint -q "$root" || mount "$root"
getent passwd labphoto >/dev/null || useradd --system --no-create-home --home-dir /inbox --shell /usr/sbin/nologin labphoto
chown root:root "$root"
chmod 755 "$root"
install -d -o labphoto -g labphoto -m 755 "$root/inbox"
install -d -m 755 /etc/ssh/authorized_keys
install -m 644 /tmp/lab-photo-setup/phone.pub /etc/ssh/authorized_keys/labphoto
cat > /etc/ssh/sshd_config.d/60-lab-photo.conf <<'EOF'
Match User labphoto
    ChrootDirectory /srv/lab-photos
    ForceCommand internal-sftp -d /inbox -u 0022
    AuthorizedKeysFile /etc/ssh/authorized_keys/%u
    PasswordAuthentication no
    KbdInteractiveAuthentication no
    DisableForwarding yes
    PermitTTY no
Match all
EOF
sshd -t
systemctl reload ssh
install -m 755 /tmp/lab-photo-setup/retention.py /usr/local/sbin/lab-photo-retention
cat > /etc/systemd/system/lab-photo-retention.service <<'EOF'
[Unit]
Description=Expire temporary Lab photos (14 days / 8 GiB target)
RequiresMountsFor=/srv/lab-photos
[Service]
Type=oneshot
ExecStart=/usr/local/sbin/lab-photo-retention
ProtectSystem=strict
ReadWritePaths=/srv/lab-photos /run
PrivateTmp=true
NoNewPrivileges=true
EOF
cat > /etc/systemd/system/lab-photo-retention.timer <<'EOF'
[Unit]
Description=Check Lab photo inbox every 5 minutes
[Timer]
OnBootSec=2min
OnUnitActiveSec=5min
[Install]
WantedBy=timers.target
EOF
systemctl daemon-reload
systemctl enable --now lab-photo-retention.timer
systemctl start lab-photo-retention.service
df -h "$root"
ssh-keygen -lf /etc/ssh/ssh_host_ed25519_key.pub
