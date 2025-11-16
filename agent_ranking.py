# agent_ranking.py

import json
import os
from typing import List, Dict, Any

from rank_items import rank_items
from llm_client import call_llm

# Toggle via .env: USE_LLM_AGENT=true / false
USE_LLM_AGENT = os.getenv("USE_LLM_AGENT", "false").lower() == "true"


def agent_rank_with_llm(user_query: str, items: List[Dict]) -> Dict[str, Any]:

    trace: List[Dict[str, Any]] = []

    # ---- 1) RULE-BASED RANKING (always run) ----
    # NOTE: this uses rank_items.score_item under the hood:
    #   - price_score:     0–2
    #   - delivery_score:  0–2
    #   - similarity_score: 0–2  (similarity * 2.0)
    #   - total_score = price_score + delivery_score + similarity_score
    rule_weights = {
        "price_weight": 1.0,
        "delivery_weight": 1.0,
        "similarity_weight": 1.0,  # similarity already scaled *2 in rank_items
        "total_score_formula": "price_score + delivery_score + similarity_score",
    }

    ranked = rank_items(user_query, items)

    trace.append({
        "step": "rule_ranking",
        "description": "Deterministic rule-based scoring of all items.",
        "rule_weights": rule_weights,
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

    # Default (if LLM disabled or fails): stick with rule based top item
    default_choice = ranked[0]
    default_explanation = (
        "Chosen as the top match based on your budget, delivery speed, "
        "and how well it fits your brief."
    )

    # SHORT-CIRCUIT IF LLM AGENT IS DISABLED
    if not USE_LLM_AGENT:
        trace.append({
            "step": "llm_ranking_skipped",
            "reason": "USE_LLM_AGENT is false – using rule-based ranking only.",
        })
        return {
            "ranked_items": ranked,
            "llm_choice": default_choice,
            "llm_explanation": default_explanation,
            "trace": trace,
        }

    # PREPARE TOP-K CANDIDATES FOR LLM JUDGEMENT
    top_k = 10
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

    # ---- 4) LLM PROMPT FOR JUDGEMENT RANKING ----
    system_prompt = (
        "You are a friendly fashion stylist helping choose the best fashion rental item for a user, "
        "using UK English and no em dashes.\n"
        "You are given:\n"
        "- the user's request (which may include a line like 'Name: <first name>')\n"
        "- a small list of candidate items with numeric scores: price_score, delivery_score, "
        "similarity_score, total_score.\n\n"
        "Your job is to:\n"
        "1) Assign each candidate a FINAL match score from 0 to 100 (higher = better) based on the brief.\n"
        "   Use the numeric scores as signals but you may adjust the ranking if the text clearly suggests "
        "   a better fit (e.g. wrong formality, wrong vibe).\n"
        "2) Produce a final ranking of all candidates from best to worst.\n"
        "3) For each candidate, provide a short reason explaining your judgement in everyday language.\n"
        "4) Provide one short overall explanation for why the top choice is best for this user.\n\n"
        "STYLE RULES (IMPORTANT):\n"
        "- If the user's request includes a clear first name on a line starting with 'Name:', naturally weave that name "
        "  into the start of your overall explanation, for example 'Emma, this dress...' or "
        "  'This outfit will be perfect for you, Emma.' Use the name only once so it feels natural.\n"
        "- If there is no name, just talk to them as 'you' without inventing a name.\n"
        "- Do NOT mention internal terms like 'price_score', 'delivery_score', 'similarity_score', or 'total_score'.\n"
        "- Do NOT talk about 'indices' or 'specifications'.\n"
        "- Instead, talk about price versus budget, delivery speed, occasion formality, colour, vibe, and how well it fits the brief.\n"
        "- Keep the overall explanation short: 1–3 sentences.\n"
        "- Keep each per-item reason to 1 short sentence.\n\n"
        "You MUST respond in JSON ONLY with this structure:\n"
        "{\n"
        '  \"ranking\": [\n'
        '    {\"index\": <number>, \"final_score\": <0-100>, \"reason\": \"short reason\"},\n'
        "    ... one entry per candidate ...\n"
        "  ],\n"
        '  \"overall_explanation\": \"short explanation for the user\"\n'
        "}\n"
        "Do not add any other keys or text."
    )

    user_msg = (
        f"User request:\n{user_query}\n\n"
        f"Candidate items (as JSON list):\n{json.dumps(simplified, ensure_ascii=False)}"
    )

    # CALL THE LLM
    raw_response = call_llm(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_msg},
        ],
        max_tokens=512,
    )

    trace.append({
        "step": "llm_ranking_call",
        "description": "LLM returns final 0–100 judgement scores and reasons.",
        "prompt_system": system_prompt,
        "prompt_user": user_msg,
        "raw_response": raw_response,
    })

    #  PARSE LLM OUTPUT SAFELY 
    final_ranked = ranked  # default fallback
    llm_choice = default_choice
    llm_explanation = default_explanation

    try:
        parsed = json.loads(raw_response)
    except Exception as e:
        trace.append({
            "step": "llm_ranking_parse_error",
            "error": f"Failed to parse LLM JSON; using rule-based ranking. {repr(e)}",
        })
        return {
            "ranked_items": final_ranked,
            "llm_choice": llm_choice,
            "llm_explanation": llm_explanation,
            "trace": trace,
        }

    if not isinstance(parsed, dict) or "ranking" not in parsed or not isinstance(parsed["ranking"], list):
        trace.append({
            "step": "llm_ranking_invalid_shape",
            "error": "Parsed JSON missing 'ranking' list; using rule-based ranking.",
            "parsed": parsed,
        })
        return {
            "ranked_items": final_ranked,
            "llm_choice": llm_choice,
            "llm_explanation": llm_explanation,
            "trace": trace,
        }

    ranking_entries = parsed["ranking"]
    overall_expl = parsed.get("overall_explanation") or default_explanation

    # Build new order for the top_k candidates based on LLM judgement
    seen_indices = set()
    new_order_indices: List[int] = []

    for entry in ranking_entries:
        try:
            idx = int(entry.get("index"))
        except (TypeError, ValueError):
            continue
        if 0 <= idx < len(candidates) and idx not in seen_indices:
            seen_indices.add(idx)
            new_order_indices.append(idx)

            # Attach LLM score + reason to the candidate item for explainability
            score_val = entry.get("final_score")
            reason_val = entry.get("reason")
            if isinstance(score_val, (int, float)):
                candidates[idx]["llm_score"] = float(score_val)
            if isinstance(reason_val, str):
                candidates[idx]["llm_reason"] = reason_val.strip()

    # If LLM gave us no valid indices, keep rule-based ranking
    if not new_order_indices:
        trace.append({
            "step": "llm_ranking_empty",
            "error": "LLM returned no usable indices; using rule-based ranking.",
            "parsed": parsed,
        })
        return {
            "ranked_items": final_ranked,
            "llm_choice": llm_choice,
            "llm_explanation": llm_explanation,
            "trace": trace,
        }

    # Add any candidates not mentioned by LLM at the end in original rule order
    for i in range(len(candidates)):
        if i not in seen_indices:
            new_order_indices.append(i)

    # Rebuild the ranked list:
    # - first the LLM-reordered top_k,
    # - then the remaining items as originally scored.
    new_top_candidates = [candidates[i] for i in new_order_indices]
    final_ranked = new_top_candidates + ranked[top_k:]

    llm_choice = new_top_candidates[0]
    llm_explanation = overall_expl

    # ADD TOP VS SECOND COMPARISON FOR JUDGES
    top_vs_second = None
    if len(new_top_candidates) > 1:
        a = new_top_candidates[0]
        b = new_top_candidates[1]
        top_vs_second = {
            "top_title": a.get("title"),
            "second_title": b.get("title"),
            "rule_scores": {
                "top": {
                    "price_score": a.get("price_score"),
                    "delivery_score": a.get("delivery_score"),
                    "similarity_score": a.get("similarity_score"),
                    "total_score": a.get("total_score"),
                },
                "second": {
                    "price_score": b.get("price_score"),
                    "delivery_score": b.get("delivery_score"),
                    "similarity_score": b.get("similarity_score"),
                    "total_score": b.get("total_score"),
                },
            },
            "llm_scores": {
                "top": {
                    "llm_score": a.get("llm_score"),
                    "llm_reason": a.get("llm_reason"),
                },
                "second": {
                    "llm_score": b.get("llm_score"),
                    "llm_reason": b.get("llm_reason"),
                },
            },
        }

    trace.append({
        "step": "llm_ranking_applied",
        "description": "Applied LLM judgement scores to re-rank top candidates.",
        "new_order_indices": new_order_indices,
        "overall_explanation": llm_explanation,
        "top_vs_second_comparison": top_vs_second,
    })

    return {
        "ranked_items": final_ranked,
        "llm_choice": llm_choice,
        "llm_explanation": llm_explanation,
        "trace": trace,
    }
