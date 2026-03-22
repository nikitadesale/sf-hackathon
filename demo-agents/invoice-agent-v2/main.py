"""
invoice-agent-v2 — Finance invoice processing agent.

This agent IS in the IT-approved registry (it was sanctioned by IT),
but it was redeployed without authentication by a developer who thought
"it's just invoices, who cares." That makes it COMPROMISED:
approved but now publicly accessible without any auth.
"""
import os
from flask import Flask, jsonify, request

app = Flask(__name__)

@app.route("/", methods=["GET"])
def health():
    return jsonify({"status": "ok", "agent": "invoice-agent-v2"})

@app.route("/process-invoice", methods=["POST"])
def process_invoice():
    data = request.get_json(silent=True) or {}
    return jsonify({
        "invoice_id":   data.get("invoice_id", "INV-0001"),
        "status":       "processed",
        "amount":       data.get("amount", 0),
        "note":         "WARNING: This endpoint has no authentication",
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
