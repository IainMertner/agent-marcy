from graph import graph

initial_state = {"text": "hi"}
result = graph.invoke(initial_state)
print(result["response"])