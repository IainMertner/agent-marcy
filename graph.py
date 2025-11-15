from dataclasses import dataclass
from typing import Optional
from langgraph.graph import StateGraph, START, END

@dataclass
class AgentState:
    text: Optional[str] = None
    response: Optional[str] = None

def step1(state: AgentState):
    return {"response": state.text}

graph = StateGraph(AgentState)
graph.add_node("step1", step1)
graph.add_edge(START, "step1")
graph.add_edge("step1", END)
graph = graph.compile()
