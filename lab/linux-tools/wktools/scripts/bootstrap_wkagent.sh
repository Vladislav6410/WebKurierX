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
if ! command -v node &>/dev/null; then
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
  echo "  Codex: уже установлен"
fi

# ── 4. Directory structure ───────────────────────────────────
echo "▶ [4/6] Создание директорий /opt/wktools..."
sudo mkdir -p ${BASE}/{bin,conf,lib,logs,workspace,logs/reports}
sudo chown -R "$USER":"$USER" ${BASE}
sudo chmod 700 ${BASE}
sudo chmod 700 ${BASE}/conf

# ── 5. Install from repo source ──────────────────────────────
echo "▶ [5/6] Установка инструментов..."
cp -f "${TOOLS_SRC}"/bin/*        ${BASE}/bin/
cp -f "${TOOLS_SRC}"/lib/*        ${BASE}/lib/
cp -f "${TOOLS_SRC}"/conf/*.json  ${BASE}/conf/ 2>/dev/null || true

# ── 6. Secrets file ──────────────────────────────────────────
echo "▶ [6/6] Secrets..."
if [[ ! -f ${BASE}/conf/secrets.env ]]; then
  cp -f "${TOOLS_SRC}/conf/secrets.env.example" ${BASE}/conf/secrets.env
  chmod 600 ${BASE}/conf/secrets.env
  echo "  ✅ secrets.env создан (заполни ключи: wksetup key)"
else
  echo "  ✅ secrets.env уже существует"
fi

chmod +x ${BASE}/bin/*

# ── Symlinks ─────────────────────────────────────────────────
for tool in wk wkdoc wksetup wkagent wkapply; do
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
echo "  1. Добавь API ключи:"
echo "     wksetup key"
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
echo "  5. Применить фикс:"
echo "     wkapply --repo . --workspace /opt/wktools/workspace/WebKurierX_ДАТА"
echo ""
