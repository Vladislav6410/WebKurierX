#!/usr/bin/env bash
set -euo pipefail

# Installs a daily timer that packs snapshots older than 24h for a given repo path.
# Usage:
#   sudo bash systemd-install-pack-timer.sh /path/to/repo

REPO_PATH="${1:-}"
if [[ -z "$REPO_PATH" ]]; then
  echo "Usage: sudo bash systemd-install-pack-timer.sh /path/to/repo"
  exit 1
fi

SERVICE="/etc/systemd/system/wktools-pack.service"
TIMER="/etc/systemd/system/wktools-pack.timer"

cat > "$SERVICE" <<EOF
[Unit]
Description=wktools: pack snapshots older than 24h

[Service]
Type=oneshot
ExecStart=/usr/local/bin/wkapply pack --repo "${REPO_PATH}" --older-than-hours 24
EOF

cat > "$TIMER" <<EOF
[Unit]
Description=wktools: daily snapshot pack

[Timer]
OnCalendar=daily
Persistent=true

[Install]
WantedBy=timers.target
EOF

systemctl daemon-reload
systemctl enable --now wktools-pack.timer
systemctl status wktools-pack.timer --no-pager
echo "✅ Installed timer. It will pack snapshots older than 24h daily."