from graph import graph

initial_state = {"user_input": "rad and awesome"}
result = graph.invoke(initial_state)
print(result["ranked_items"])