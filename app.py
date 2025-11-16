#app.py

from typing import Any, Dict, List
import os

from flask import Flask, request, jsonify, send_from_directory

from graph import graph
from agent_ranking import agent_rank_with_llm 

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

    # LangGraph workflow
    initial_state: Dict[str, Any] = {"user_input": user_input}
    final_state = graph.invoke(initial_state)

    print(">>> Full final_state:", final_state, type(final_state))

    #Take items from graph output
    items: List[Dict[str, Any]] = (
        final_state.get("ranked_items")
        or final_state.get("items")
        or []
    )

    if not items:
        return jsonify({
            "ranked_items": [],
            "llm_choice": None,
            "llm_explanation": "No items found.",
            "trace": [],
        })

    # Run explainable ranking agent
    agent_result = agent_rank_with_llm(user_input, items)

    ranked_items = agent_result["ranked_items"]
    llm_choice = agent_result["llm_choice"]
    llm_explanation = agent_result["llm_explanation"]
    trace = agent_result["trace"]

    top_k = 10

    # Return everything to the frontend
    return jsonify({
        "ranked_items": ranked_items[:top_k],
        "llm_choice": llm_choice,
        "llm_explanation": llm_explanation,
        "trace": trace,
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8005, debug=True)


# Website url: http://127.0.0.1:8005/questionaire.html