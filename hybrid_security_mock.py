from flask import Flask, request, jsonify
import datetime

app = Flask(__name__)

@app.route("/api/v1/security/report", methods=["POST"])
def receive_report():
    data = request.json
    print(f"📩 Received report from {data.get('lab')} — issues={data.get('issues')}")
    return jsonify({"status": "ok", "received": data}), 200


@app.route("/api/v1/hybrid/feedback", methods=["GET"])
def send_feedback():
    print("🔁 Sending Hybrid feedback...")
    mock_feedback = {
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "repository": "WebKurierX",
        "labs": [
            {
                "name": "neurolab",
                "trust_score": 0.96,
                "last_report": "2025-12-28T18:30:00Z",
                "status": "validated",
                "promotion_ready": True,
                "notes": "Static validation OK, sandbox integrity confirmed."
            },
            {
                "name": "quantum",
                "trust_score": 0.88,
                "last_report": "2025-12-28T18:30:00Z",
                "status": "in-review",
                "promotion_ready": False,
                "notes": "Pending hybrid simulation confirmation."
            }
        ],
        "summary": {
            "total_labs": 2,
            "eligible_for_promotion": 1,
            "overall_trust_index": 0.92
        }
    }
    return jsonify(mock_feedback), 200


if __name__ == "__main__":
    app.run(port=9090)

