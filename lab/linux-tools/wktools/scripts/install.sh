#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

sudo mkdir -p /opt/wktools/{bin,conf,lib,logs,workspace}
sudo chown -R "$USER":"$USER" /opt/wktools
sudo chmod 700 /opt/wktools
sudo chmod 700 /opt/wktools/conf

cp -f "$ROOT"/bin/* /opt/wktools/bin/
cp -f "$ROOT"/lib/* /opt/wktools/lib/
cp -f "$ROOT"/conf/*.json /opt/wktools/conf/ 2>/dev/null || true
cp -f "$ROOT"/conf/*.example /opt/wktools/conf/ 2>/dev/null || true

if [[ ! -f /opt/wktools/conf/secrets.env ]]; then
  cp -f "$ROOT/conf/secrets.env.example" /opt/wktools/conf/secrets.env
  chmod 600 /opt/wktools/conf/secrets.env
fi

chmod +x /opt/wktools/bin/*

sudo ln -sf /opt/wktools/bin/wk /usr/local/bin/wk
sudo ln -sf /opt/wktools/bin/wkdoc /usr/local/bin/wkdoc
sudo ln -sf /opt/wktools/bin/wksetup /usr/local/bin/wksetup
sudo ln -sf /opt/wktools/bin/wkagent /usr/local/bin/wkagent

echo "Installed wktools (wk, wkdoc, wksetup, wkagent)"
echo "Next:"
echo "  sudo npm i -g @openai/codex"
echo "  wksetup key"
echo "  wkdoc --token-test"
echo "  wkagent check --repo ."