#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "▶ Установка wktools из: $ROOT"

sudo mkdir -p /opt/wktools/{bin,conf,lib,logs,workspace,logs/reports}
sudo chown -R "$USER":"$USER" /opt/wktools
sudo chmod 700 /opt/wktools
sudo chmod 700 /opt/wktools/conf

cp -f "$ROOT"/bin/*       /opt/wktools/bin/
cp -f "$ROOT"/lib/*       /opt/wktools/lib/
cp -f "$ROOT"/conf/*.json /opt/wktools/conf/ 2>/dev/null || true

if [[ ! -f /opt/wktools/conf/secrets.env ]]; then
  cp -f "$ROOT/conf/secrets.env.example" /opt/wktools/conf/secrets.env
  chmod 600 /opt/wktools/conf/secrets.env
  echo "  ✅ secrets.env создан"
else
  echo "  ✅ secrets.env уже есть — не перезаписываем"
fi

chmod +x /opt/wktools/bin/*

for tool in wk wkdoc wksetup wkagent wkapply; do
  if [[ -f /opt/wktools/bin/$tool ]]; then
    sudo ln -sf /opt/wktools/bin/$tool /usr/local/bin/$tool
    echo "  ✅ /usr/local/bin/$tool"
  fi
done

echo ""
echo "✅ wktools установлен!"
echo ""
echo "  wksetup key            # добавить ключи"
echo "  wksetup status         # проверить"
echo "  wkagent check --repo . # первый анализ"

