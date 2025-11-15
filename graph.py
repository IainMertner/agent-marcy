from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from langgraph.graph import StateGraph, START, END

@dataclass
class AgentState:
    user_input: Optional[str] = None
    sites: List[str] = field(default_factory=list)
    items: List[Dict[str, Any]] = field(default_factory=list)
    item_details: List[Dict[str, Any]] = field(default_factory=list)
    ranked_items: List[Dict[str, Any]] = field(default_factory=list)

def parse_input(state: AgentState):
    return {"parsed_input": {"query": state.user_input}}

def find_sites(state: dict):
    return {"sites": ["siteA.com", "siteB.com"]}

def find_items(state: dict):
    all_items = []
    for site in state.sites:
        items = [
            {"site": site, "item_id": f"{site}-1"},
            {"site": site, "item_id": f"{site}-2"},
        ]
        all_items.extend(items)
    return {"items": all_items}

def get_item_details(state: dict):
    detailed = []
    for item in state.items:
        detailed.append({**item, "price": 10, "sizes": ["S", "M"]})
    return {"item_details": detailed}

def rank_items(state: dict):
    items = state.item_details
    ranked = items
    return {"ranked_items": ranked}

graph = StateGraph(AgentState)

graph.add_node("parse_input", parse_input)
graph.add_node("find_sites", find_sites)
graph.add_node("find_items", find_items)
graph.add_node("get_item_details", get_item_details)
graph.add_node("rank_items", rank_items)

graph.add_edge(START, "parse_input")
graph.add_edge("parse_input", "find_sites")
graph.add_edge("find_sites", "find_items")
graph.add_edge("find_items", "get_item_details")
graph.add_edge("get_item_details", "rank_items")
graph.add_edge("rank_items", END)
graph = graph.compile()