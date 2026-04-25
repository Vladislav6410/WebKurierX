#!/usr/bin/env bash
# ============================================================
# bootstrap_wkagent.sh — WebKurier AI Engineer Setup
# Ubuntu 22.04 | Repo: WebKurierX
# Usage: bash bootstrap_wkagent.sh
# ============================================================
set -euo pipefail

BASE="/opt/wktools"
REPO_DIR="${HOME}/WebKurierX"
TOOLS_SRC="${REPO_DIR}/lab/linux-tools/wktools"

echo ""
echo "╔══════════════════════════════════════════╗"
echo "║   WKAgent Bootstrap — WebKurier v2.0    ║"
echo "╚══════════════════════════════════════════╝"
echo ""

# ── 1. System deps ──────────────────────────────────────────
echo "▶ [1/6] Системные зависимости..."
sudo apt-get update -qq
sudo apt-get install -y -qq \
  python3 python3-pip git curl wget rsync nano \
  build-essential jq 2>/dev/null || true

# ── 2. Node.js 20 LTS ───────────────────────────────────────
echo "▶ [2/6] Node.js 20 LTS..."
if ! command -v node &>/dev/null || [[ "$(node -e 'process.exit(parseInt(process.versions.node)>=18?0:1)' ; echo $?)" != "0" ]]; then
  curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
  sudo apt-get install -y nodejs
fi
echo "  Node: $(node --version) | npm: $(npm --version)"

# ── 3. Codex CLI ────────────────────────────────────────────
echo "▶ [3/6] OpenAI Codex CLI..."
if ! command -v codex &>/dev/null; then
  sudo npm install -g @openai/codex 2>/dev/null || \
    echo "  ⚠️  Codex install failed — продолжаем без него"
else
  echo "  Codex: $(codex --version 2>/dev/null || echo 'installed')"
fi

# ── 4. Directory structure ───────────────────────────────────
echo "▶ [4/6] Создание директорий /opt/wktools..."
sudo mkdir -p ${BASE}/{bin,conf,lib,logs,workspace,logs/reports}
sudo chown -R "$USER":"$USER" ${BASE}
sudo chmod 700 ${BASE}
sudo chmod 700 ${BASE}/conf

# ── 5. Install from repo source ──────────────────────────────
echo "▶ [5/6] Установка инструментов..."

if [[ -d "${TOOLS_SRC}" ]]; then
  cp -f "${TOOLS_SRC}"/bin/*   ${BASE}/bin/   2>/dev/null && echo "  ✅ bin/" || echo "  ⚠️  bin/ not found"
  cp -f "${TOOLS_SRC}"/lib/*   ${BASE}/lib/   2>/dev/null && echo "  ✅ lib/" || echo "  ⚠️  lib/ not found"
  cp -f "${TOOLS_SRC}"/conf/*.json    ${BASE}/conf/ 2>/dev/null || true
  cp -f "${TOOLS_SRC}"/conf/*.example ${BASE}/conf/ 2>/dev/null || true
else
  echo "  ⚠️  Источник ${TOOLS_SRC} не найден — создаём заглушки"
  # Create stub scripts so system is runnable
  cat > ${BASE}/bin/wk <<"WKEOF"
#!/usr/bin/env bash
python3 /opt/wktools/lib/wk.py "$@"
WKEOF
  cat > ${BASE}/bin/wkagent <<"WKEOF"
#!/usr/bin/env bash
python3 /opt/wktools/lib/wkagent.py "$@"
WKEOF
  cat > ${BASE}/bin/wksetup <<"WKEOF"
#!/usr/bin/env bash
CMD="${1:-help}"
case "$CMD" in
  key)  sudo nano /opt/wktools/conf/secrets.env && sudo chmod 600 /opt/wktools/conf/secrets.env ;;
  status) echo "Node: $(node -v)"; echo "Python: $(python3 -V)"; ls /opt/wktools ;;
  *) echo "wksetup: key | status" ;;
esac
WKEOF
fi

chmod +x ${BASE}/bin/* 2>/dev/null || true

# ── 6. Secrets file ──────────────────────────────────────────
if [[ ! -f ${BASE}/conf/secrets.env ]]; then
  cat > ${BASE}/conf/secrets.env <<"SECEOF"
# WebKurier — Secrets (НЕ коммитить в git!)
# Заполни ключи и сохрани: Ctrl+O, Enter, Ctrl+X

CODEX_API_KEY=
ANTHROPIC_API_KEY=
OPENAI_API_KEY=
QWEN_API_KEY=
SECEOF
  chmod 600 ${BASE}/conf/secrets.env
  echo "  ✅ secrets.env создан (заполни ключи: wksetup key)"
else
  echo "  ✅ secrets.env уже существует"
fi

# ── 7. wkagent.json config ───────────────────────────────────
cat > ${BASE}/conf/wkagent.json <<"JEOF"
{
  "log_file": "/opt/wktools/logs/wkagent.log",
  "report_dir": "/opt/wktools/logs/reports",
  "workspace": "/opt/wktools/workspace",
  "secrets_file": "/opt/wktools/conf/secrets.env",
  "checks": {
    "git_status_clean": true,
    "required_files": [".gitignore", "README.md"],
    "forbidden_patterns": ["sk-", "OPENAI_API_KEY=sk", "CODEX_API_KEY=sk", "ANTHROPIC_API_KEY=sk"]
  },
  "commands": {
    "python_lint": "python3 -m compileall . -q",
    "node_lint": "[ -f package.json ] && npm test --if-present || true",
    "tests": "[ -f pytest.ini ] || [ -f setup.py ] && pytest -q || true"
  }
}
JEOF

# ── 8. Symlinks ──────────────────────────────────────────────
echo "▶ [6/6] Создание symlinks..."
for tool in wk wkagent wksetup wkdoc; do
  if [[ -f ${BASE}/bin/${tool} ]]; then
    sudo ln -sf ${BASE}/bin/${tool} /usr/local/bin/${tool}
    echo "  ✅ /usr/local/bin/${tool}"
  fi
done

echo ""
echo "╔══════════════════════════════════════════╗"
echo "║         ✅ Bootstrap завершён!           ║"
echo "╚══════════════════════════════════════════╝"
echo ""
echo "Следующие шаги:"
echo ""
echo "  1. Добавь API ключ:"
echo "     wksetup key"
echo "     # Вставь: CODEX_API_KEY=sk-xxxxxxxx"
echo ""
echo "  2. Проверь установку:"
echo "     wksetup status"
echo ""
echo "  3. Проверь репозиторий:"
echo "     cd ~/WebKurierX && wkagent check --repo ."
echo ""
echo "  4. Исправить с помощью ИИ:"
echo "     wkagent fix --repo ."
echo ""
echo "Отчёты: /opt/wktools/logs/reports/"
echo "Workspace: /opt/wktools/workspace/"
echo ""