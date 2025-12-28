#!/usr/bin/env python3
"""
WebKurierX — Auto Manifest Updater
-----------------------------------
Скрипт автоматически обновляет:
 - docs/AGENT_MANIFEST.md
 - config.yml (модуль maturity, version)
при каждом коммите в любую лабораторию /labs/
или корневой экспериментальный модуль.

Используется GitHub Actions workflow (.github/workflows/manifest_update.yml)
"""

import os
import re
import yaml
from datetime import datetime
from pathlib import Path

CONFIG_PATH = Path("config.yml")
MANIFEST_PATH = Path("docs/AGENT_MANIFEST.md")

def load_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def save_config(cfg):
    cfg["meta"]["last_update"] = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        yaml.dump(cfg, f, allow_unicode=True, sort_keys=False)

def update_maturity(cfg):
    """Если есть изменения в лабораториях — повышаем maturity"""
    labs = cfg.get("labs", {})
    changed = False

    for lab_name, lab_info in labs.items():
        lab_path = Path(f"labs/{lab_name}")
        if not lab_path.exists():
            continue

        # Проверка изменений по времени модификации
        last_mod = max((f.stat().st_mtime for f in lab_path.rglob("*") if f.is_file()), default=0)
        last_update = datetime.strptime(cfg["meta"]["last_update"].split(" ")[0], "%Y-%m-%d")
        if datetime.utcfromtimestamp(last_mod) > last_update:
            maturity = lab_info.get("maturity", 0)
            if maturity < 3:
                lab_info["maturity"] = maturity + 1
                changed = True

    return changed

def regenerate_manifest(cfg):
    """Перестраивает AGENT_MANIFEST.md"""
    header = (
        "# 🌐 WebKurierX — AGENT MANIFEST (Auto-Generated)\n\n"
        f"Последнее обновление: **{cfg['meta']['last_update']}**\n\n"
        "Документ сгенерирован автоматически при коммите в любую лабораторию.\n\n---\n"
    )

    sections = []
    for lab_name, lab in cfg["labs"].items():
        agent = lab.get("agent", "UnknownAgent")
        maturity = lab.get("maturity", 0)
        desc = lab.get("description", "")
        target = lab.get("upstream_target", "Unknown")
        ci = "✅" if lab.get("ci_enabled", False) else "❌"

        section = f"""## 🧩 {agent}
**Лаборатория:** `{lab_name}`  
**Описание:** {desc}  
**Целевая интеграция:** `{target}`  
**Уровень зрелости:** {maturity}  
**CI/CD:** {ci}

---
"""
        sections.append(section)

    with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
        f.write(header + "\n".join(sections))

def main():
    cfg = load_config()
    if update_maturity(cfg):
        print("🔁 Обновлены уровни зрелости лабораторий.")
    save_config(cfg)
    regenerate_manifest(cfg)
    print("✅ AGENT_MANIFEST.md и config.yml обновлены успешно.")

if __name__ == "__main__":
    main()