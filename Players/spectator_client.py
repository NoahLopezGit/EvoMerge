import requests
import matplotlib.pyplot as plt
import numpy as np
import time
# from threading import Thread

class SpectatorClient():
    def __init__(self):
        self.base_url = "http://127.0.0.1:8000"
        self.session = requests.Session()
        self.display_setup = False

    def get_worlds(self):
        response = self.session.get(
            self.base_url + "/get_worlds",
            timeout=5,
        )
        return response.json()

    def get_rgb_map(self, game_map):
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

    def __init__display(self, rgb_map):
        plt.ion()
        self.fig, self.ax = plt.subplots()
        self.img = self.ax.imshow(rgb_map)

    def spectate_world(self, world_id: str):
        self.display_loop(world_id)
        # Thread(target=self.display_loop, args=(world_id,), daemon=True).start()

    def display_loop(self, world_id: str):
        if not self.display_setup:
            game_map = self.get_game_interface(world_id)
            rgb_map = self.get_rgb_map(game_map)
            self.__init__display(rgb_map)
            self.display_setup = True

        while True:
            response = self.session.get(
                self.base_url + "/get_world_state",
                params={"world_id": world_id},
                timeout=5,
            )

            game_map = np.array(response.json()["world_state"]["map"])
            rgb_map = self.get_rgb_map(game_map)

            self.img.set_data(rgb_map)
            self.fig.canvas.flush_events()

            time.sleep(0.2)

    def get_game_interface(self, world_id: str):
        response = self.session.get(
            self.base_url + "/get_world_state",
            params={"world_id": world_id},
            timeout=5,
        )
        game_map = np.array(response.json()["world_state"]["map"])
        return game_map

if __name__=="__main__":
    spectator = SpectatorClient()
    games = spectator.get_worlds()
    print(games)
    spectator.spectate_world(list(games.values())[0]["world_id"])