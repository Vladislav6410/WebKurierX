#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WebKurierX Intelligence Layer — AutoChart Renderer 📈
Generates ASCII line charts of Trust and Risk dynamics for inclusion in INDEX.md
"""

import re
from pathlib import Path
from statistics import mean

index_path = Path("docs/analytics/INDEX.md")
if not index_path.exists():
    print("⚠️ INDEX.md not found, aborting chart rendering.")
    raise SystemExit(0)

with open(index_path, "r", encoding="utf-8") as f:
    content = f.read()

# === Extract trust and risk data ===
lines = [l for l in content.splitlines() if re.match(r"\|\s*\d{4}-\d{2}-\d{2}", l)]
trust_values, risk_values, dates = [], [], []

for line in lines:
    parts = [x.strip() for x in line.strip("|").split("|")]
    if len(parts) >= 3:
        try:
            date = parts[0]
            trust = float(parts[1])
            risk = float(parts[2])
            trust_values.append(trust)
            risk_values.append(risk)
            dates.append(date)
        except ValueError:
            continue

if not trust_values:
    print("⚠️ No numeric data found in INDEX.md.")
    raise SystemExit(0)

def render_chart(values, label, height=6, width=30):
    """Simple ASCII line chart generator"""
    max_val, min_val = max(values), min(values)
    span = max_val - min_val or 1
    step = max(1, len(values) // width)
    scaled = [(v - min_val) / span for v in values[::step]]
    chart = []
    for y in reversed(range(height)):
        row = ""
        for x in scaled:
            row += "█" if x >= y / height else " "
        chart.append(row)
    chart_text = "\n".join(chart)
    return f"**{label} trend:**\n```\n{chart_text}\n```\n"

# === Render charts ===
trust_chart = render_chart(trust_values, "Trust Index")
risk_chart = render_chart(risk_values, "Risk Index")

# === Append to INDEX.md ===
charts_section = f"""
---

## 📈 AutoChart Visualization

{trust_chart}
{risk_chart}

> _Charts generated automatically by WebKurierX Intelligence Layer AutoChart Renderer._
"""

# Remove any old chart section
content = re.sub(r"(?s)## 📈 AutoChart Visualization.*", "", content)
content += charts_section

with open(index_path, "w", encoding="utf-8") as f:
    f.write(content)

print(f"✅ AutoChart rendered successfully → {index_path}")