# app.py - Flask backend for chat system

from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Enables cross-origin requests from frontend

@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json()
    username = data.get("username")
    message = data.get("message")

    print(f"✅ Received from {username}: {message}")

    reply = f"Hello {username}, I received your message: '{message}'"
    return jsonify({"reply": reply})

if __name__ == "__main__":
    app.run(debug=True)