"""
Shadow Data Collector — no auth, wide IAM, calls external URL.
Deployed by a rogue team member. This is what gets flagged.
"""
import os
import urllib.request
from flask import Flask, jsonify

app = Flask(__name__)

EXTERNAL_URL = "https://httpbin.org/post"


@app.route("/")
def index():
    return jsonify({"name": "shadow-data-collector", "status": "running"})


@app.route("/collect")
def collect():
    # Makes an outbound call to an external endpoint — suspicious
    try:
        urllib.request.urlopen(EXTERNAL_URL, timeout=3)
        ext_status = "reached"
    except Exception:
        ext_status = "timeout"

    return jsonify({
        "collected": 1000,
        "external_endpoint": EXTERNAL_URL,
        "external_status": ext_status,
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 8080)))
