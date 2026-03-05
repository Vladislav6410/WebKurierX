#!/usr/bin/env bash
set -euo pipefail

# Installs a systemd timer that packs old snapshots daily.
# It will run: wkapply pack --repo <REPO_PATH> --older-than-hours 24
# You can adjust REPO_PATH and hour threshold inside the unit file after install.

SERVICE_NAME="wktools-pack"
TIMER_FILE="/etc/systemd/system/${SERVICE_NAME}.timer"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"

echo "== Installing systemd timer: ${SERVICE_NAME} =="

# Default repo path to pack snapshots for (edit after install if needed)
DEFAULT_REPO_PATH="/opt/webkurier/WebKurierX"
DEFAULT_HOURS="24"

sudo bash -c "cat > '${SERVICE_FILE}'" <<EOF
[Unit]
Description=wktools: pack old snapshots (tar.gz) and cleanup

[Service]
Type=oneshot
Environment=REPO_PATH=${DEFAULT_REPO_PATH}
Environment=OLDER_THAN_HOURS=${DEFAULT_HOURS}
ExecStart=/usr/local/bin/wkapply pack --repo "\${REPO_PATH}" --older-than-hours "\${OLDER_THAN_HOURS}"
EOF

sudo bash -c "cat > '${TIMER_FILE}'" <<'EOF'
[Unit]
Description=wktools: daily pack timer

[Timer]
OnCalendar=daily
Persistent=true

[Install]
WantedBy=timers.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable --now "${SERVICE_NAME}.timer"

echo ""
echo "✅ Installed & enabled:"
echo "  - ${SERVICE_FILE}"
echo "  - ${TIMER_FILE}"
echo ""
echo "Check:"
echo "  systemctl status ${SERVICE_NAME}.timer"
echo "Run once manually:"
echo "  sudo systemctl start ${SERVICE_NAME}.service"
echo ""
echo "Edit repo path if needed:"
echo "  sudo nano ${SERVICE_FILE}"