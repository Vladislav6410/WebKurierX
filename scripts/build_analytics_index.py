import os
import re
import json
from datetime import datetime
from pathlib import Path
from statistics import mean

# === Paths ===
analytics_dir = Path("docs/analytics")
index_file = analytics_dir / "INDEX.md"
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)
log_file = log_dir / "analytics_history.log"

snapshots = sorted(analytics_dir.glob("*.md"))

if not snapshots:
    print("⚠️ No analytics snapshots found.")
    raise SystemExit(0)

table_rows = []
header = """# 📊 Continuous Intelligence Archive — WebKurierX

This index is automatically generated from daily analytics snapshots
by the Hybrid+X Intelligence Layer.

| Date | Trust Index | Risk Index | Labs | Trend |
|------|--------------|-------------|-------|--------|
"""

def extract_metrics(file_path):
    """Парсинг метрик из snapshot-файлов"""
    trust, risk, labs = "—", "—", "—"
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
    return trust, risk, labs


trust_values = []
risk_values = []
previous_trust = None
trend = "➖"

for snap in snapshots:
    trust, risk, labs = extract_metrics(snap)
    date = snap.stem
    try:
        trust_value = float(trust)
        risk_value = float(risk)
    except:
        trust_value, risk_value = None, None

    # Detect trend
    if previous_trust is not None and trust_value is not None:
        if trust_value > previous_trust:
            trend = "🟢 up"
        elif trust_value < previous_trust:
            trend = "🔻 down"
        else:
            trend = "➖"
    previous_trust = trust_value if trust_value is not None else previous_trust

    # Store metrics for averages
    if trust_value is not None:
        trust_values.append(trust_value)
    if risk_value is not None:
        risk_values.append(risk_value)

    table_rows.append(f"| {date} | {trust} | {risk} | {labs} | {trend} |")

# === Compute analytics summary ===
avg_trust = mean(trust_values[-7:]) if trust_values else 0.0
avg_risk = mean(risk_values[-7:]) if risk_values else 0.0
security_trust_index = round(avg_trust * (1 - avg_risk), 3)

summary = f"""
## 🧠 Weekly Summary
- 📅 Last 7-day Average Trust Index: **{avg_trust:.3f}**
- ⚖️ Last 7-day Average Risk Index: **{avg_risk:.3f}**
- 🔐 Integrated Security-Trust Index (STI): **{security_trust_index:.3f}**

_Last update: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%SZ')}_
"""

# === Write index file ===
with open(index_file, "w", encoding="utf-8") as f:
    f.write(header + "\n".join(reversed(table_rows)) + "\n" + summary + "\n")

# === Log analytics history ===
with open(log_file, "a", encoding="utf-8") as log:
    log.write(f"[{datetime.utcnow().isoformat()}] Trust={avg_trust:.3f}, Risk={avg_risk:.3f}, STI={security_trust_index:.3f}\n")

print(f"✅ Analytics index updated → {index_file}")
print(f"📦 Processed {len(snapshots)} snapshots.")
print(f"🧾 Logged summary to {log_file}")


