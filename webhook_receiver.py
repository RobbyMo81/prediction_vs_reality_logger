import os
from flask import Flask, request, jsonify
from validate_results import validate_results

app = Flask(__name__)
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")

@app.route("/hook/results", methods=["POST"])
def handle_webhook():
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    if token != WEBHOOK_SECRET:
        return jsonify({"error": "Unauthorized"}), 403

    print("[Webhook] Received update trigger.")
    validation_report = validate_results()
    return jsonify(validation_report), 200

if __name__ == "__main__":
    app.run(port=int(os.getenv("WEBHOOK_PORT", 8080)))
