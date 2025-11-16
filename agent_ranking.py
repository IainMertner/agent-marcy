# agent_ranking.py

import json
import os
from typing import List, Dict, Any

from rank_items import rank_items
from llm_client import call_llm   


USE_LLM_AGENT = os.getenv("USE_LLM_AGENT", "false").lower() == "true"

def agent_rank_with_llm(user_query: str, items: List[Dict]) -> Dict[str, Any]:
    """
    Agent-style ranking:
    1. Use rule-based ranking to score and sort items.
    2. Take top_k candidates.
    3. Optionally (if USE_LLM_AGENT=true) ask the LLM to:
         - pick the best one
         - explain why, in human language
    4. Return:
         - full ranked list
         - chosen item (LLM or rule-based)
         - explanation
         - a trace for observability
    """

    trace: List[Dict[str, Any]] = []

    # Rule based ranking
    ranked = rank_items(user_query, items)
    trace.append({
        "step": "rule_ranking",
        "input_count": len(items),
        "output_count": len(ranked),
        "sample_scores": [
            {
                "title": it.get("title"),
                "price": it.get("price"),
                "delivery": it.get("delivery"),
                "price_score": it.get("price_score"),
                "delivery_score": it.get("delivery_score"),
                "similarity_score": it.get("similarity_score"),
                "total_score": it.get("total_score"),
            }
            for it in ranked[:5]
        ],
    })

    if not ranked:
        return {
            "ranked_items": [],
            "llm_choice": None,
            "llm_explanation": "No items were available.",
            "trace": trace,
        }

    #  Pick top_k candidates to show the LLM 
    top_k = 5
    candidates = ranked[:top_k]

    simplified: List[Dict[str, Any]] = []
    for idx, item in enumerate(candidates):
        simplified.append({
            "index": idx,
            "title": item.get("title"),
            "price": item.get("price"),
            "delivery": item.get("delivery"),
            "url": item.get("url"),
            "price_score": item.get("price_score"),
            "delivery_score": item.get("delivery_score"),
            "similarity_score": item.get("similarity_score"),
            "total_score": item.get("total_score"),
        })

    # LLM prompt
    system_prompt = (
    "You are a friendly fashion stylist helping choose the best fashion rental item for a user using UK English and no em dashes.\n"
    "You are given:\n"
    "- the user's request (which may include a line like 'Name: <first name>')\n"
    "- a small list of candidate items with numeric scores: price_score, "
    "delivery_score, similarity_score, total_score.\n\n"
    "Your job is to:\n"
    "1) pick the single best item index.\n"
    "2) explain in warm, customer friendly language why it is the best and why it works better than the other options.\n\n"
    "STYLE RULES (IMPORTANT):\n"
    "- If the user's request includes a clear first name on a line starting with 'Name:', naturally weave that name into the start of your reply, for example 'Emma, this dress...' or 'This dress will be perfect for you, Emma.'\n"
    "- Use the name only once in the opening sentence so it feels warm and natural, not repetitive.\n"
    "- If there is no name in the request, just talk to them as 'you' without inventing or guessing a name.\n"
    "- Do NOT mention any internal scores or numbers like price_score, "
    "delivery_score, similarity_score, total_score, or indices.\n"
    "- Do NOT say things like 'all dresses have identical specifications and scores'.\n"
    "- Do NOT use words like 'score', 'similarity score', 'specifications', or 'index' in the explanation.\n"
    "- Instead, talk about price vs budget, delivery speed, how formal it feels, fabric, colour, and how well it fits the brief.\n"
    "- Keep the explanation short: 1–3 sentences.\n"
    "- Write as if you're talking to a shopper, not an engineer.\n\n"
    "You MUST respond in JSON ONLY with this structure:\n"
    "{\n"
    '  \"chosen_index\": <number>,\n'
    '  \"explanation\": \"...your explanation...\"\n'
    "}\n"
    "Do not add any other keys or text."
)




    user_msg = (
        f"User request:\n{user_query}\n\n"
        f"Candidate items (as JSON list):\n{json.dumps(simplified, ensure_ascii=False)}"
    )

    #  Call the LLM
    raw_response = call_llm(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_msg},
        ],
        max_tokens=512,
    )

    trace.append({
        "step": "llm_ranking",
        "prompt_system": system_prompt,
        "prompt_user": user_msg,
        "raw_response": raw_response,
    })

    #  Parse LLM's JSON output safely
    chosen_index = 0
    llm_explanation = (
        "Chosen as the top rule-based item based on price, delivery speed, "
        "and how well it fits your brief."
    )

    try:
        parsed = json.loads(raw_response)
        if isinstance(parsed, dict):
            if "chosen_index" in parsed:
                ci = int(parsed["chosen_index"])
                if 0 <= ci < len(candidates):
                    chosen_index = ci
            if "explanation" in parsed:
                text = str(parsed["explanation"])
                # If the LLM response itself is a failure message, ignore it
                if "LLM call failed" not in text:
                    llm_explanation = text
    except Exception:
        # If parsing fails, just keep the rule-based explanation
        pass

    llm_choice = candidates[chosen_index]

    return {
        "ranked_items": ranked,
        "llm_choice": llm_choice,
        "llm_explanation": llm_explanation,
        "trace": trace,
    }
