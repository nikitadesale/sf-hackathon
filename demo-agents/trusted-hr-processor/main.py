"""
trusted-hr-processor — Demo authorized agent.
Represents a properly-governed AI agent:
  - IT-approved and in the allowlist
  - Private Cloud Run (requires authentication)
  - Limited service account (read-only HR data)
  - Internal traffic only
"""
import os
from flask import Flask, jsonify

app = Flask(__name__)

@app.route("/", methods=["GET"])
def health():
    return jsonify({"status": "ok", "agent": "trusted-hr-processor"})

@app.route("/process", methods=["POST"])
def process():
    return jsonify({
        "status": "processed",
        "message": "HR data processed securely (internal only)",
        "access": "private — authentication required",
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
