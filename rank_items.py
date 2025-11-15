# ranking.py
# ---------------------------------------------------------
# Ranking module for the fashion rental agent.
#
# INPUT:
#   - user_query: string (what the user typed)
#   - items: list of dicts
#
# OUTPUT:
#   - items sorted by total score
# ---------------------------------------------------------

from typing import List, Dict


def simple_similarity_score(user_query: str, description: str) -> float:
    """
    Simple text similarity between the user query and an item title.
    """
    q_words = set(user_query.lower().split())
    d_words = set(description.lower().split())

    if not q_words:
        return 0.0
    
    overlap = q_words.intersection(d_words)

    return len(overlap) / len(q_words)


def score_item(user_query: str, item: Dict) -> Dict:
    """
    extracts price, delivery, title from an item
    - calculates three sub-scores: price_score, delivery_score, similarity_score
    - sums them into total_score
    - returns the same item dict with extra score fields added
    """
    score = 0.0

    # -------- 1) PRICE SCORE --------
    price = item.get("price")
    price_score = 0.0

    if isinstance(price, (int, float)):
        if price <= 50:
            price_score = 2.0
        elif price <= 70:
            price_score = 1.0

    score += price_score

    # -------- 2) DELIVERY SCORE --------
    delivery = (item.get("delivery") or "").strip()
    delivery_score = 0.0

    if "Next Day" in delivery:
        delivery_score = 2.0
    elif "2–3 Days" in delivery or "2-3 Days" in delivery:
        delivery_score = 1.0

    score += delivery_score

    # -------- 3) SIMILARITY SCORE --------
    sim = simple_similarity_score(user_query, item.get("description"))  # 0 to 1

    similarity_score = sim * 2.0
    score += similarity_score

    # Store the sub-scores back on the item for explainability
    item["price_score"] = price_score
    item["delivery_score"] = delivery_score
    item["similarity_score"] = similarity_score
    item["total_score"] = score

    return item


def rank_items(user_query: str, items: List[Dict]) -> List[Dict]:
    """
    Main function to be used by the rest of the system.
    INPUT:
        user_query: user’s natural language request
        items: list of item dicts from the search / retrieval step
    PROCESS:
        - calls score_item(user_query, item) on each item
        - sorts items by total_score (highest first)
    OUTPUT:
        - list of items sorted from best to worst with scoring fields added:
            price_score, delivery_score, similarity_score, total_score
    """
    scored_items: List[Dict] = []

    for item in items:
        scored = score_item(user_query, item)
        scored_items.append(scored)

    # Sort by total_score descending
    scored_items.sort(key=lambda x: x.get("total_score", 0.0), reverse=True)

    return scored_items
