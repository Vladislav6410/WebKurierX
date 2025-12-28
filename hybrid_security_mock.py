# hybrid_security_mock.py
from flask import Flask, request, jsonify
app = Flask(__name__)

@app.route("/api/v1/security/report", methods=["POST"])
def receive_report():
    data = request.json
    print(f"📩 Received report from {data.get('lab')} — issues={data.get('issues')}")
    return jsonify({"status": "ok", "received": data}), 200

if __name__ == "__main__":
    app.run(port=9090)