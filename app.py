# app.py

from typing import Any, Dict, List
import os

from flask import Flask, request, jsonify, send_from_directory

from graph import graph
from agent_ranking import agent_rank_with_llm 

# --- LangSmith / LangChain tracing imports ---
from dotenv import load_dotenv
from langsmith.run_helpers import traceable

# Load .env so LANGSMITH_API_KEY, LANGCHAIN_TRACING_V2, etc. are available
load_dotenv()

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.join(BASE_DIR, "WearWise")



@traceable(
    run_type="chain",
    name="wearwise_recommendation",
    tags=["wearwise", "hackathon", "frontend-api"],
)
def run_wearwise_graph(user_input: str, raw_payload: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """
    Wraps the LangGraph invocation in a LangSmith trace.
    Every call to /api/recommend will show up as a run in LangSmith.
    """
    initial_state: Dict[str, Any] = {"user_input": user_input}
  
    final_state = graph.invoke(initial_state)
    return final_state


# ---------- FRONTEND PAGES ----------

@app.get("/")
def serve_home():
    """
    Landing page: WearWise home.
    """
    return send_from_directory(TEMPLATE_DIR, "wearwise.html")


@app.get("/wearwise.html")
def serve_home_explicit():
    """
    Explicit /wearwise.html route (for your back-links in the UI).
    """
    return send_from_directory(TEMPLATE_DIR, "wearwise.html")


@app.get("/questionaire.html")
def serve_questionnaire():
    """
    Questionnaire page – loaded after clicking the CTA on the home page.
    """
    return send_from_directory(TEMPLATE_DIR, "questionaire.html")


# ---------- STATIC ASSETS ----------

@app.get("/dress3.png")
def dress_image():
    return send_from_directory(TEMPLATE_DIR, "dress3.png")


@app.get("/favicon.png")
def favicon():
    return send_from_directory(TEMPLATE_DIR, "favicon.png")


# ---------- BACKEND API ----------

@app.post("/api/recommend")
def recommend():
    data: Dict[str, Any] = request.get_json(force=True) or {}
    user_input: str = data.get("user_input", "")

    print(">>> Received from frontend:\n", user_input)
    print(">>> Calling run_wearwise_graph(...) with LangSmith tracing")

    # LangGraph workflow wrapped in LangSmith tracing
    final_state = run_wearwise_graph(user_input=user_input, raw_payload=data)

    print(">>> Full final_state:", final_state, type(final_state))

    # Take items from graph output
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
    # Start on http://127.0.0.1:8005/
    # Make sure you have in your env / .env:
    #   LANGSMITH_API_KEY=...
    #   LANGCHAIN_TRACING_V2=true
    #   LANGCHAIN_PROJECT=wearwise-hackathon   (or similar)
    app.run(host="0.0.0.0", port=8005, debug=True)
