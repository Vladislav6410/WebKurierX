# 🔁 Hybrid Feedback Status

_Last sync: pending update..._

---

## 🧠 Overview

This document is automatically updated by  
**`.github/workflows/hybrid_feedback_listener.yml`**,  
which synchronizes WebKurierX lab security and trust data from **Hybrid** (mock or production).

| Field | Description |
|:------|:-------------|
| `trust_score` | Numerical trust index (0–1.0) |
| `status` | Lab security validation stage |
| `promotion_ready` | Indicates if lab can move up from sandbox |
| `notes` | Brief remarks from Hybrid feedback pipeline |

---

## 🧩 Latest Feedback Snapshot

| 🧪 Lab | 🔒 Trust Score | 📊 Status | 🚀 Promotion Ready | 📝 Notes |
|:------|:---------------:|:----------|:------------------:|:---------|
| neurolab | 0.96 | ✅ validated | ✅ yes | Static validation OK, sandbox integrity confirmed. |
| quantum | 0.88 | 🕓 in-review | ❌ no | Pending hybrid simulation confirmation. |

---

## 📈 Summary

| Metric | Value |
|:--------|:------|
| Total Labs | 2 |
| Eligible for Promotion | 1 |
| Overall Trust Index | 0.92 |

---

### 🧩 Next Update
This file is synced every **15 minutes** or when manually triggered from  
→ **Actions → 🔁 Hybrid Feedback Listener (v1)**

_Last generated automatically by `scripts/pull_hybrid_feedback.py`_