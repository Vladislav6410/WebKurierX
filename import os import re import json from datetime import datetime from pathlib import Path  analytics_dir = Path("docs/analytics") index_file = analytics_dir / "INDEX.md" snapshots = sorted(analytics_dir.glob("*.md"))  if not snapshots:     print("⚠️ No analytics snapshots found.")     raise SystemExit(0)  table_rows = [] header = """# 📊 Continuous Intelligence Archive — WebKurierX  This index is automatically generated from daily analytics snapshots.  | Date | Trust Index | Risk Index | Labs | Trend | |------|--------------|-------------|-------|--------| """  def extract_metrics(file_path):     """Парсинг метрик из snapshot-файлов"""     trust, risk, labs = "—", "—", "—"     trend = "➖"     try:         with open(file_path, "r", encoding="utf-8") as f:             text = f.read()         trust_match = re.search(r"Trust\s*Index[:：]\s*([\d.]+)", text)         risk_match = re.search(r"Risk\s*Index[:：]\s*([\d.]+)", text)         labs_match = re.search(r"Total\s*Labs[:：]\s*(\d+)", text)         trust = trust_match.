import os
import re
import json
from datetime import datetime
from pathlib import Path

analytics_dir = Path("docs/analytics")
index_file = analytics_dir / "INDEX.md"
snapshots = sorted(analytics_dir.glob("*.md"))

if not snapshots:
    print("⚠️ No analytics snapshots found.")
    raise SystemExit(0)

table_rows = []
header = """# 📊 Continuous Intelligence Archive — WebKurierX

This index is automatically generated from daily analytics snapshots.

| Date | Trust Index | Risk Index | Labs | Trend |
|------|--------------|-------------|-------|--------|
"""

def extract_metrics(file_path):
    """Парсинг метрик из snapshot-файлов"""
    trust, risk, labs = "—", "—", "—"
    trend = "➖"
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()
        trust_match = re.search(r"Trust\s*Index[:：]\s*([\d.]+)", text)
        risk_match = re.search(r"Risk\s*Index[:：]\s*([\d.]+)", text)
        labs_match = re.search(r"Total\s*Labs[:：]\s*(\d+)", text)
        trust = trust_match.group(1) if trust_match else "—"
        risk = risk_match.group(1) if risk_match else "—"
        labs = labs_match.group(1) if labs_match else "—"
    except Exception as e:
        print(f"⚠️ Failed to parse {file_path}: {e}")
    return trust, risk, labs, trend


previous_trust = None
for snap in snapshots:
    trust, risk, labs, trend = extract_metrics(snap)
    date = snap.stem
    try:
        trust_value = float(trust)
    except:
        trust_value = None

    if previous_trust is not None and trust_value is not None:
        if trust_value > previous_trust:
            trend = "🟢 up"
        elif trust_value < previous_trust:
            trend = "🔻 down"
        else:
            trend = "➖"
    previous_trust = trust_value if trust_value is not None else previous_trust

    table_rows.append(f"| {date} | {trust} | {risk} | {labs} | {trend} |")

with open(index_file, "w", encoding="utf-8") as f:
    f.write(header + "\n".join(reversed(table_rows)) + "\n")

print(f"✅ Analytics index updated: {index_file}")