from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from langgraph.graph import StateGraph, START, END
from rank_items import simple_similarity_score, score_item, rank_items

# define the shared state for the pipeline
@dataclass
class AgentState:
    user_input: Optional[str] = None
    sites: List[str] = field(default_factory=list)
    item_urls: List[str] = field(default_factory=list)
    items: List[Dict[str, Any]] = field(default_factory=list)
    ranked_items: List[Dict[str, Any]] = field(default_factory=list)

### node functions

## parse user input (dummy code)
def parse_input_step(state: AgentState):
    return {"parsed_input": {"query": state.user_input}}

## get list of sites to search (dummy code)
def get_sites_step(state: dict):
    return {"sites": ["siteA.com", "siteB.com"]}

## find list of relevant item urls from sites (dummy code)
def find_item_urls_step(state: dict):
    item_urls = []
    for site in state.sites:
        for i in range(3):
            item_urls.append(site + str(i))
    return {"item_urls": item_urls}

## get individual item details from urls (dummy code)
def get_item_details_step(state: dict):
    items = []
    for item_url in state.item_urls:
        items.append({"url": item_url, "title": "Red Silk Dress", "price": 45, "delivery": "Next Day", "description": "cool"})
        items.append({"url": item_url, "title": "Black Suit", "price": 55, "delivery": "2-3 Days", "description": "awesome"})
        items.append({"url": item_url, "title": "Gold Gown", "price": 70, "delivery": "Next Day", "description": "rad"})
    return {"items": items}

## score and rank items
def rank_items_step(state: dict):
    ranked = rank_items(state.user_input, state.items)
    return {"ranked_items": ranked}

### build graph

graph = StateGraph(AgentState)
## add nodes
graph.add_node("parse_input_step", parse_input_step)
graph.add_node("get_sites_step", get_sites_step)
graph.add_node("find_item_urls_step", find_item_urls_step)
graph.add_node("get_item_details_step", get_item_details_step)
graph.add_node("rank_items_step", rank_items_step)
## connect nodes through edges (fully sequential)
graph.add_edge(START, "parse_input_step")
graph.add_edge("parse_input_step", "get_sites_step")
graph.add_edge("get_sites_step", "find_item_urls_step")
graph.add_edge("find_item_urls_step", "get_item_details_step")
graph.add_edge("get_item_details_step", "rank_items_step")
graph.add_edge("rank_items_step", END)
# compile graph for execution
graph = graph.compile()