from world import World

def vectorize_state(agent_state, vision):
    # only include info the agent would know TODO
    # Example vectorization: [x, y, facing_direction, cell_1, cell_2, ..., cell_n]
    facing_mapping = {"up": 0, "right": 1, "down": 2, "left": 3}
    vector = [
        agent_state.position.x,
        agent_state.position.y,
        facing_mapping[agent_state.facing],
    ]
    for visioncell in vision:
        vector.append(visioncell.value)
    return vector


world = World(seed=42, wall_count=1000)
agents = world.add_random_agents(10)

success = True
while success == True:
    result = world.apply_agent_action({
        "agent_id": agents[0].agent_id,
        "action": "move",
        "direction": "right",
    })
    success = result.success

    print(vectorize_state(result.agent_state, result.vision))

world.visualize()