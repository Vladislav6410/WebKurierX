from flask import Flask, jsonify, request
import random
import time

app = Flask(__name__)

LAB_SECURITY_STATE = {
    "neurolab": {"issues": 0, "risk_score": 0.1},
    "quantum": {"issues": 1, "risk_score": 0.4},
    "holoshow": {"issues": 0, "risk_score": 0.2},
}

@app.route("/api/v1/security/<lab_name>", methods=["GET"])
def get_lab_security(lab_name):
    time.sleep(0.2)
    data = LAB_SECURITY_STATE.get(
        lab_name, {"issues": random.randint(0, 2), "risk_score": round(random.random(), 2)}
    )
    return jsonify({
        "lab": lab_name,
        "issues": data["issues"],
        "risk_score": data["risk_score"],
        "timestamp": time.time(),
        "source": "Mock SecurityAgent API"
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8088)