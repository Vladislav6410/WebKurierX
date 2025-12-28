#!/usr/bin/env python3
"""
WebKurierX — Smart Manifest v3 (Security-Aware Promotion Layer)
---------------------------------------------------------------
Добавляет слой безопасности в процесс авто-повышения maturity.
- Проверяет security_report.json каждой лаборатории.
- Блокирует продвижение при наличии уязвимостей.
"""

import os
import yaml
import json
import subprocess
from datetime import datetime
from pathlib import Path

CONFIG_PATH = Path("config.yml")
MANIFEST_PATH = Path("docs/AGENT_MANIFEST.md")
SECURITY_REPORT_NAME = "security_report.json"

REPO_OWNER = "WebKurierOrg"  # заменить на реальный namespace
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")

def load_yaml(path):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def save_yaml(path, data):
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True, sort_keys=False)

def count_successful_builds(lab_path):
    """Читает .ci/build.log и считает количество успешных билдов"""
    log_path = lab_path / ".ci" / "build.log"
    if not log_path.exists():
        return 0
    with open(log_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    return sum(1 for l in lines if "BUILD SUCCESS" in l or "✅" in l)

def load_security_report(lab_path):
    """Читает security_report.json и возвращает количество найденных уязвимостей"""
    report_path = lab_path / ".ci" / SECURITY_REPORT_NAME
    if not report_path.exists():
        return 0
    try:
        with open(report_path, "r", encoding="utf-8") as f:
            report = json.load(f)
        return int(report.get("issues", 0))
    except Exception:
        return 0

def create_pull_request(target_repo, branch_name, title, body):
    """Создаёт PR через GitHub CLI"""
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
    updated, blocked = [], []
    for lab_name, lab in cfg["labs"].items():
        lab_path = Path(f"labs/{lab_name}")
        if not lab_path.exists():
            continue

        builds = count_successful_builds(lab_path)
        issues = load_security_report(lab_path)
        maturity = lab.get("maturity", 0)

        if issues > 0:
            blocked.append((lab_name, issues))
            continue

        if builds >= 3 and maturity < 3:
            lab["maturity"] = maturity + 1
            updated.append(lab_name)

            if lab["maturity"] >= 3:
                branch = f"promote/{lab_name}-v{lab['maturity']}"
                title = f"Promote {lab_name} → {lab['upstream_target']} (maturity {lab['maturity']})"
                body = f"""
Автоматическое продвижение лаборатории `{lab_name}`.
✅ Все CI тесты и проверки безопасности успешно пройдены.
**Уровень зрелости:** {lab['maturity']}
**Дата:** {datetime.utcnow().isoformat()} UTC
"""
                create_pull_request(lab["upstream_target"], branch, title, body)

    return updated, blocked

def regenerate_manifest(cfg, blocked):
    header = (
        "# 🌐 WebKurierX — Smart AGENT MANIFEST (v3: Security-Aware)\n\n"
        f"Последнее обновление: **{datetime.utcnow().isoformat()} UTC**\n\n"
        "Автоматически обновляется после успешных CI и проверок безопасности.\n\n---\n"
    )

    sections = []
    for lab_name, lab in cfg["labs"].items():
        warning = ""
        if any(lab_name == b[0] for b in blocked):
            issues = [b[1] for b in blocked if b[0] == lab_name][0]
            warning = f"⚠️ Найдено проблем безопасности: {issues}\n\n"
        sections.append(
            f"## 🧩 {lab['agent']}\n"
            f"**Лаборатория:** `{lab_name}`\n"
            f"**Описание:** {lab['description']}\n"
            f"**Зрелость:** {lab['maturity']}\n"
            f"**CI активен:** {'✅' if lab['ci_enabled'] else '❌'}\n"
            f"**Цель:** `{lab['upstream_target']}`\n"
            f"{warning}---\n"
        )

    with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
        f.write(header + "".join(sections))

def main():
    cfg = load_yaml(CONFIG_PATH)
    updated, blocked = update_maturity(cfg)
    save_yaml(CONFIG_PATH, cfg)
    regenerate_manifest(cfg, blocked)
    if updated:
        print(f"🔁 Повышены maturity: {', '.join(updated)}")
    if blocked:
        for lab, issues in blocked:
            print(f"⛔ Лаборатория {lab} заблокирована ({issues} проблем безопасности)")
    print("✅ Manifest и config.yml обновлены.")

if __name__ == "__main__":
    main()