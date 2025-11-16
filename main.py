from graph import graph

# initial input to graph
initial_state = {"user_input": "green"}
# run pipeline
result = graph.invoke(initial_state)
# print final ranked lists
for item in enumerate(result["ranked_items"]):
    print(item)