import requests
import matplotlib.pyplot as plt
import numpy as np
import time

def get_rgb_map(game_map):
    x_dim, y_dim = game_map.shape
    rgb_map = np.zeros((x_dim, y_dim, 3), dtype=np.uint8)

    for i in range(x_dim):
        for j in range(y_dim):
            cell_value = game_map[i][j]

            if cell_value == 0:      # empty
                rgb_map[i][j] = [255, 255, 255]
            elif cell_value == 1:    # wall
                rgb_map[i][j] = [0, 0, 0]
            elif cell_value == 2:    # energy
                rgb_map[i][j] = [0, 255, 0]
            elif cell_value >= 100:  # player
                rgb_map[i][j] = [0, 0, 255]

    return rgb_map

base_url = "http://127.0.0.1:8000"

session = requests.Session()

response = session.get(
    base_url + "/get_world_state",
    params={"world_id": 0},
    timeout=5,
)
game_map = np.array(response.json()["world_state"]["map"])

rgb_map = get_rgb_map(game_map)

plt.ion()
fig, ax = plt.subplots()
img = ax.imshow(rgb_map)

while True:
    response = session.get(
        base_url + "/get_world_state",
        params={"world_id": 0},
        timeout=5,
    )

    game_map = np.array(response.json()["world_state"]["map"])
    rgb_map = get_rgb_map(game_map)

    img.set_data(rgb_map)
    fig.canvas.flush_events()

    time.sleep(0.2)