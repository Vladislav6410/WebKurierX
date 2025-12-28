import os
import requests
import datetime
import pathlib
import json
import re

# 🌐 Конфигурация
endpoint = os.getenv("HYBRID_FEEDBACK_ENDPOINT", "http://localhost:9090/api/v1/hybrid/feedback")
token = os.getenv("HYBRID_TOKEN", "mock-token")
headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

# 📁 Пути
docs_path = pathlib.Path("docs/FEEDBACK_STATUS.md")
logs_dir = pathlib.Path("logs")
logs_dir.mkdir(parents=True, exist_ok=True)
log_file = logs_dir / "hybrid_feedback.log"

print(f"🌐 Fetching feedback from Hybrid endpoint: {endpoint}")

# 🛰 Получение данных
try:
    response = requests.get(endpoint, headers=headers, timeout=10)
    response.raise_for_status()
    data = response.json()
except Exception as e:
    print(f"❌ Failed to get feedback: {e}")
    with log_file.open("a", encoding="utf-8") as lf:
        lf.write(f"[{datetime.datetime.utcnow()}] ERROR: {e}\n")
    raise SystemExit(1)

timestamp = datetime.datetime.utcnow().isoformat() + "Z"
labs = data.get("labs", [])
summary = data.get("summary", {})

# 🧠 Извлечение предыдущих trust и risk из логов
previous_trust = {}
previous_risk = {}
if log_file.exists():
    try:
        text = log_file.read_text(encoding="utf-8")
        for match in re.findall(r"- (\w+): trust=([0-9.]+), risk=([0-9.]+)", text):
            lab, trust, risk = match
            previous_trust[lab] = float(trust)
            previous_risk[lab] = float(risk)
    except Exception:
        pass

# 🧾 Добавляем в лог новую запись
with log_file.open("a", encoding="utf-8") as lf:
    lf.write(f"\n[{timestamp}] Feedback sync\n")
    for lab in labs:
        trust = lab.get("trust_score", 0.0)
        risk = lab.get("risk_score", 0.0)
        lf.write(
            f"  - {lab.get('name')}: trust={trust:.3f}, risk={risk:.3f}, "
            f"status={lab.get('status')}, ready={lab.get('promotion_ready')}\n"
        )
    lf.write(
        f"  Summary: overall_trust={summary.get('overall_trust_index', 0):.3f}, "
        f"eligible={summary.get('eligible_for_promotion', 0)} / "
        f"total={summary.get('total_labs', len(labs))}\n"
    )

print(f"🪵 Log updated → {log_file}")

# 📊 Формирование Markdown с анализом trust + risk
table_header = (
    "| 🧪 Lab | 🔒 Trust | ⚠️ Risk | 🧭 Trust Δ | ⚡ Risk Δ | 🧮 SecTrust Index | 📊 Status | 🚀 Promotion | 📝 Notes |\n"
    "|:------|:---------:|:-------:|:----------:|:----------:|:----------------:|:----------|:-------------:|:---------|\n"
)

rows = []
for lab in labs:
    name = lab.get("name")
    trust = lab.get("trust_score", 0.0)
    risk = lab.get("risk_score", 0.0)
    prev_t = previous_trust.get(name)
    prev_r = previous_risk.get(name)
    trust_delta = trust - prev_t if prev_t is not None else 0
    risk_delta = risk - prev_r if prev_r is not None else 0
    sec_trust_index = round(trust * (1 - risk), 3)

    trust_trend = "🆕" if prev_t is None else (
        f"🟢 ↑{trust_delta:.2f}" if trust_delta > 0.02 else (
            f"⚠️ ↓{abs(trust_delta):.2f}" if trust_delta < -0.02 else "➖ stable"
        )
    )
    risk_trend = "🆕" if prev_r is None else (
        f"⚠️ ↑{risk_delta:.2f}" if risk_delta > 0.02 else (
            f"🟢 ↓{abs(risk_delta):.2f}" if risk_delta < -0.02 else "➖ stable"
        )
    )

    rows.append(
        f"| {name} "
        f"| {trust:.2f} "
        f"| {risk:.2f} "
        f"| {trust_trend} "
        f"| {risk_trend} "
        f"| {sec_trust_index:.2f} "
        f"| {'✅ validated' if lab.get('status') == 'validated' else '🕓 ' + lab.get('status', 'unknown')} "
        f"| {'✅ yes' if lab.get('promotion_ready') else '❌ no'} "
        f"| {lab.get('notes', '').replace('|', '/')} |"
    )

table = "\n".join(rows)

summary_table = (
    "| Metric | Value |\n"
    "|:--------|:------|\n"
    f"| Total Labs | {summary.get('total_labs', len(labs))} |\n"
    f"| Eligible for Promotion | {summary.get('eligible_for_promotion', 0)} |\n"
    f"| Overall Trust Index | {summary.get('overall_trust_index', 0):.3f} |\n"
)

# 🧱 Markdown отчёт
content = f"""# 🧠 Hybrid+X Intelligence Feedback Report

_Last sync: **{timestamp} UTC**_

---

## Overview

This dashboard merges **trust** and **risk** analytics from Hybrid feedback,
producing a combined **Security-Trust Index (STI)** for each lab.

| Field | Description |
|:------|:-------------|
| `Trust` | Reliability and validation consistency |
| `Risk` | Security vulnerability score (0–1) |
| `Trust Δ` | Change in trust since last feedback |
| `Risk Δ` | Change in risk level |
| `SecTrust Index` | (trust × (1 - risk)) — combined metric |
| `Promotion` | Eligibility for graduation to production |
| `Notes` | Feedback from Hybrid |

---

## 🧩 Latest Hybrid+X Feedback

{table_header}{table}

---

## 📈 Summary

{summary_table}

---

### 🧾 Historical Log Reference
See trust & risk evolution in:
`logs/hybrid_feedback.log`

---

_Last updated automatically by `scripts/pull_hybrid_feedback.py (Enterprise+ Intelligence Layer)`_
"""

docs_path.write_text(content, encoding="utf-8")
print(f"✅ Intelligence Layer report updated → {docs_path}")
