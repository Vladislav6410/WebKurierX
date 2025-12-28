# 🛡️ SecurityAgent Mock API

Mock REST API, имитирующий работу центрального SecurityAgent Hybrid.
Используется системой SAPL (Security-Aware Promotion Layer).

---

## 🔹 Эндпоинты

### `GET /api/v1/security/<lab_name>`
Возвращает риск-профиль лаборатории.

**Пример:**
```bash
curl http://localhost:8088/api/v1/security/neurolab