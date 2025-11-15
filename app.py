from typing import Any, Dict, List
import os

from flask import Flask, request, jsonify, send_from_directory

from graph import graph  # ⬅️ only import graph here

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.join(BASE_DIR, "WearWise")


@app.get("/questionaire.html")
def serve_questionnaire():
    return send_from_directory(TEMPLATE_DIR, "questionaire.html")


@app.get("/dress3.png")
def dress_image():
    return send_from_directory(TEMPLATE_DIR, "dress3.png")


@app.get("/favicon.png")
def favicon():
    return send_from_directory(TEMPLATE_DIR, "favicon.png")


@app.post("/api/recommend")
def recommend():
    data = request.get_json(force=True) or {}
    user_input = data.get("user_input", "")

    print(">>> Received from frontend:\n", user_input)
    print(">>> Calling graph.invoke(...)")

    # 🔸 Use dict state, just like in main.py
    initial_state: Dict[str, Any] = {"user_input": user_input}
    final_state = graph.invoke(initial_state)

    # Debug: see exactly what the graph returned
    print(">>> Full final_state:", final_state, type(final_state))

    # Safely pull ranked_items out of the dict
    ranked_items: List[Dict[str, Any]] = final_state.get("ranked_items") or []
    top_k = 10

    return jsonify({"ranked_items": ranked_items[:top_k]})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
