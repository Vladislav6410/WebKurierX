#!/usr/bin/env bash
set -euo pipefail

# Install wktools into /opt/wktools and create symlinks in /usr/local/bin
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "== wktools install =="
echo "Source: $ROOT"
echo "Target: /opt/wktools"

# Create target dirs (secure)
sudo mkdir -p /opt/wktools/{bin,conf,lib,logs,workspace,snapshots,archives}
sudo chown -R "$USER":"$USER" /opt/wktools
sudo chmod 700 /opt/wktools
sudo chmod 700 /opt/wktools/conf

# Copy tools
cp -f "$ROOT"/bin/* /opt/wktools/bin/
cp -f "$ROOT"/lib/* /opt/wktools/lib/

# Copy configs if present
if compgen -G "$ROOT/conf/*.json" > /dev/null; then
  cp -f "$ROOT"/conf/*.json /opt/wktools/conf/
fi

# Create secrets.env if missing (from example)
if [[ ! -f /opt/wktools/conf/secrets.env ]]; then
  if [[ -f "$ROOT/conf/secrets.env.example" ]]; then
    cp -f "$ROOT/conf/secrets.env.example" /opt/wktools/conf/secrets.env
  else
    cat > /opt/wktools/conf/secrets.env <<'EOF'
# NEVER COMMIT REAL SECRETS
CODEX_API_KEY=
OPENAI_API_KEY=
EOF
  fi
  chmod 600 /opt/wktools/conf/secrets.env
else
  chmod 600 /opt/wktools/conf/secrets.env || true
fi

# Ensure executable wrappers
chmod +x /opt/wktools/bin/*

# Symlinks
sudo ln -sf /opt/wktools/bin/wk      /usr/local/bin/wk      2>/dev/null || true
sudo ln -sf /opt/wktools/bin/wkdoc   /usr/local/bin/wkdoc   2>/dev/null || true
sudo ln -sf /opt/wktools/bin/wksetup /usr/local/bin/wksetup 2>/dev/null || true
sudo ln -sf /opt/wktools/bin/wkagent /usr/local/bin/wkagent 2>/dev/null || true
sudo ln -sf /opt/wktools/bin/wkapply /usr/local/bin/wkapply 2>/dev/null || true

echo ""
echo "✅ Installed wktools:"
echo "  - /opt/wktools/bin/*"
echo "  - /opt/wktools/lib/*"
echo "  - /opt/wktools/conf/*"
echo ""
echo "Next:"
echo "  wksetup status"
echo "  sudo npm i -g @openai/codex"
echo "  wksetup key"
echo "  wkdoc --token-test"
echo "  wkagent check --repo ."