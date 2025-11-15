from graph import graph

# initial input to graph
initial_state = {"user_input": "rad and awesome"}
# run pipeline
result = graph.invoke(initial_state)
# print final ranked lists
print(result["ranked_items"])