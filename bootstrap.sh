#!/usr/bin/env bash
set -euo pipefail

# WebKurierX bootstrap: creates lab/linux-tools/wktools structure + files

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET="${ROOT_DIR}/lab/linux-tools/wktools"

mkdir -p "${TARGET}"/{bin,conf,lib,scripts,logs}

# 1) .gitignore
cat > "${TARGET}/.gitignore" <<'EOF'
# secrets (NEVER COMMIT)
conf/secrets.env

# runtime
logs/
workspace/

# python
__pycache__/
*.pyc
.venv/

# junk
.DS_Store
EOF

# 2) README.md
cat > "${TARGET}/README.md" <<'EOF'
# WebKurierX — Linux Tools: wktools

Три команды после установки:
- `wk` — natural prompt -> Codex CLI -> генерирует/правит файлы в workspace
- `wkdoc` — Doctor Web: DNS/HTTP/token диагностика
- `wksetup` — установка/обновление/ввод токена

## Быстрая установка на Ubuntu 22.04
```bash
cd WebKurierX/lab/linux-tools/wktools
sudo bash scripts/install.sh
wksetup key
wkdoc --token-test
wk "Создай hello.txt и напиши туда 'WK is alive'"