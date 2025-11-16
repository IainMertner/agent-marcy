from typing import List, Dict

### compute a simple similarity score between user query and item description
def simple_similarity_score(user_query: str, description: str) -> float:
    # set of words in user query
    q_words = set(user_query.lower().split())
    # set of words in item description
    try:
        d_words = set(description.lower().split())
    except:
        return 0.0

    if not q_words:
        return 0.0
    
    # percentage of words in query that are also in description
    overlap = q_words.intersection(d_words)
    return len(overlap) / len(q_words)

### compute total score for single item - combining price, delivery speed, and similarity
def score_item(user_query: str, item: Dict) -> Dict:
    score = 0.0

    ## price based scoring
    price = item.get("price")
    price_score = 0.0

    if isinstance(price, (int, float)):
        if price <= 50:
            price_score = 2.0
        elif price <= 70:
            price_score = 1.0

    score += price_score

    ## delivery based scoring
    delivery = (item.get("delivery") or "").strip()
    delivery_score = 0.0

    if "Next Day" in delivery:
        delivery_score = 2.0
    elif "2–3 Days" in delivery or "2-3 Days" in delivery:
        delivery_score = 1.0

    score += delivery_score

    ## description similarity scoring
    sim = simple_similarity_score(user_query, item.get("description"))  # 0 to 1

    similarity_score = sim * 2.0
    score += similarity_score

    ## store individual component scores and total score
    item["price_score"] = price_score
    item["delivery_score"] = delivery_score
    item["similarity_score"] = similarity_score
    item["total_score"] = score

    return item

### rank items based on total scores
def rank_items(user_query: str, items: List[Dict]) -> List[Dict]:
    scored_items: List[Dict] = []

    for item in items:
        # calculate scores for each item
        scored = score_item(user_query, item)
        scored_items.append(scored)

    # sort descending
    scored_items.sort(key=lambda x: x.get("total_score", 0.0), reverse=True)

    return scored_items
