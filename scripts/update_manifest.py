#!/usr/bin/env python3
"""
WebKurierX — Auto Promotion + Smart Manifest Updater (v2)
----------------------------------------------------------
Отслеживает успешные сборки CI лабораторий и повышает maturity.
При достижении maturity >= 3 создаёт Pull Request в целевой Core-репозиторий.
"""

import os
import re
import yaml
import json
import subprocess
from datetime import datetime
from pathlib import Path

CONFIG_PATH = Path("config.yml")
MANIFEST_PATH = Path("docs/AGENT_MANIFEST.md")

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
REPO_OWNER = "WebKurierOrg"         # пример — заменить на реального владельца
HYBRID_REPO = "WebKurierHybrid"

def load_yaml(path):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def save_yaml(path, data):
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True, sort_keys=False)

def count_successful_builds(lab_path):
    """Читает build.log и считает количество успешных CI-запусков"""
    log_path = lab_path / ".ci" / "build.log"
    if not log_path.exists():
        return 0
    with open(log_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    return sum(1 for l in lines if "BUILD SUCCESS" in l or "✅" in l)

def create_pull_request(target_repo, branch_name, title, body):
    """Создаёт PR через GitHub CLI (gh)"""
    try:
        subprocess.run([
            "gh", "pr", "create",
            "--repo", f"{REPO_OWNER}/{target_repo}",
            "--base", "main",
            "--head", branch_name,
            "--title", title,
            "--body", body
        ], check=True)
        print(f"🚀 Создан PR в {target_repo}")
    except Exception as e:
        print(f"⚠️ Ошибка при создании PR: {e}")

def update_maturity(cfg):
    updated_labs = []
    for lab_name, lab in cfg["labs"].items():
        lab_path = Path(f"labs/{lab_name}")
        if not lab_path.exists():
            continue

        builds = count_successful_builds(lab_path)
        maturity = lab.get("maturity", 0)
        if builds >= 3 and maturity < 3:
            lab["maturity"] = maturity + 1
            updated_labs.append(lab_name)

        # Проверка на "готовность к продвижению"
        if lab["maturity"] >= 3:
            branch_name = f"promote/{lab_name}-v{lab['maturity']}"
            title = f"Promote {lab_name} → {lab['upstream_target']} (maturity {lab['maturity']})"
            body = f"""
Автоматическое повышение зрелости лаборатории `{lab_name}`.
Модуль готов к интеграции в **{lab['upstream_target']}**.

**CI успешные сборки:** {builds}
**Дата:** {datetime.utcnow().isoformat()} UTC
"""
            create_pull_request(lab["upstream_target"], branch_name, title, body)

    return updated_labs

def regenerate_manifest(cfg):
    header = (
        "# 🌐 WebKurierX — Smart AGENT MANIFEST (Auto Generated v2)\n\n"
        f"Последнее обновление: **{datetime.utcnow().isoformat()} UTC**\n\n---\n"
    )
    sections = []
    for lab_name, lab in cfg["labs"].items():
        sections.append(
            f"## 🧩 {lab['agent']}\n"
            f"**Лаборатория:** `{lab_name}`\n"
            f"**Описание:** {lab['description']}\n"
            f"**Зрелость:** {lab['maturity']}\n"
            f"**CI активен:** {'✅' if lab['ci_enabled'] else '❌'}\n"
            f"**Цель:** `{lab['upstream_target']}`\n\n---\n"
        )
    with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
        f.write(header + "".join(sections))

def main():
    cfg = load_yaml(CONFIG_PATH)
    updated = update_maturity(cfg)
    if updated:
        print(f"🔁 Обновлены maturity для: {', '.join(updated)}")
    save_yaml(CONFIG_PATH, cfg)
    regenerate_manifest(cfg)
    print("✅ Manifest обновлён успешно.")

if __name__ == "__main__":
    main()
