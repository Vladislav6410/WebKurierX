import os, requests, json, datetime, pathlib

endpoint = os.getenv("HYBRID_FEEDBACK_ENDPOINT", "http://localhost:9090/api/v1/hybrid/feedback")
token = os.getenv("HYBRID_TOKEN", "mock-token")
headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

print(f"🌐 Connecting to {endpoint}...")

try:
    response = requests.get(endpoint, headers=headers, timeout=10)
    response.raise_for_status()
    data = response.json()
except Exception as e:
    print(f"❌ Failed to fetch feedback: {e}")
    raise SystemExit(1)

timestamp = datetime.datetime.utcnow().isoformat()
status_path = pathlib.Path("docs/FEEDBACK_STATUS.md")

content = [
    "# 🔁 Hybrid Feedback Status",
    f"Last update: **{timestamp} UTC**",
    "",
    "## Feedback Summary",
    f"```json\n{json.dumps(data, indent=2, ensure_ascii=False)}\n```",
    "",
    "_Auto-synced from Hybrid feedback endpoint_",
]

status_path.write_text("\n".join(content), encoding="utf-8")
print(f"✅ Feedback written to {status_path}")